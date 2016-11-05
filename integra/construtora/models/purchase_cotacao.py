# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


SITUACAO = [
    ['A', 'Aberta'],
    ['C', 'Confirmada'],
    ['F', 'Fechada'],
]


class purchase_cotacao(orm.Model):
    _name = 'purchase.cotacao'
    _description = u'Cotação'
    _order = 'data desc, codigo'
    _rec_name = 'codigo'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for purchase_cotacao in self.browse(cr, uid, ids):
            res[purchase_cotacao.id] = purchase_cotacao.id

        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=True, select=True),
        'company_id': fields.many2one('res.company',string=u'Empresa'),
        'data': fields.date(u'Data'),
        'situacao': fields.selection(SITUACAO, u'Situação', select=True),

        'planejamento_ids': fields.many2many('project.orcamento.item.planejamento', 'purchase_cotacao_planejamento', 'cotacao_id', 'planejamento_id', string=u'Itens planejados/solicitados'),

        'solicitacao_ids': fields.many2many('purchase.solicitacao.cotacao.item.orcado', 'purchase_cotacao_item_solicitacao', 'cotacao_id', 'solicitacao_item_id', string=u'Itens solicitados'),

        'item_ids': fields.one2many('purchase.cotacao.item', 'cotacao_id', string=u'Item da Cotação'),
        'fornecedor_ids': fields.one2many('purchase.cotacao.fornecedor', 'cotacao_id', string=u'Fornecedor da Cotação'),

        'supplierinfo_ids': fields.many2many('product.supplierinfo', 'cotacao_id', 'supplierinfo_id', string=u'Informações de fornecedores'),

        'purchase_order_ids': fields.one2many('purchase.order', 'cotacao_id', string=u'Pedidos de compra'),

        'obs': fields.text(u'Observações'),
    }

    _defaults = {
        'data': fields.date.today(),
        'situacao': 'A',
        #'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'purchase.cotacao', context=c),
    }

    def compartilha_fornecedor(self, cr, uid, ids, context={}):
        grupo_pool = self.pool.get('res.groups')
        usuario_pool = self.pool.get('res.users')

        for cotacao_obj in self.browse(cr, uid, ids):
            for forn_obj in cotacao_obj.fornecedor_ids:
                grupo_id = grupo_pool.cria_grupo_compartilhamento(cr, 1, forn_obj.partner_id.id)
                usuario_id = usuario_pool.cria_usuario_compartilhamento(cr, 1, forn_obj.email, grupo_id)
                cotacao_obj.enviar_email_compartilhamento(usuario_id)

    def confirma_cotacao(self, cr, uid, ids, context={}):
        supplier_pool = self.pool.get('product.supplierinfo')
        if not len(ids):
            return {}

        res = {}

        self.pool.get('purchase.cotacao').preparar_produtos(cr, uid, ids, context=context)

        for cotacao_obj in self.browse(cr, uid, ids):
            if not cotacao_obj.item_ids:
                raise osv.except_osv(u'Erro!', u'Não existe nehum item viculado à cotação!')

            elif not cotacao_obj.fornecedor_ids:
                raise osv.except_osv(u'Erro!', u'Não existe nenhum fornecedor viculado à cotação!')

            else:
                if cotacao_obj.solicitacao_ids:
                    for solicitacao_obj in cotacao_obj.solicitacao_ids:
                        solicitacao_obj.write({'cotacao_aprovada_id':cotacao_obj.id})

                supplierinfo_ids = []

                i = 1
                for fornecedor in cotacao_obj.fornecedor_ids:
                    for item in cotacao_obj.item_ids:
                        busca = [
                            ('name', '=', fornecedor.partner_id.id),
                            ('product_id', '=', item.product_id.product_tmpl_id.id),
                            ('codigo_cotacao', '=', cotacao_obj.id),
                        ]
                        supplier_id = supplier_pool.search(cr, 1, busca, limit=1)

                        if supplier_id:
                            supplier_id = supplier_id[0]
                            supplierinfo_ids.append(supplier_id)
                            supplier_pool.write(cr, uid, [supplier_id], {'codigo_cotacao': cotacao_obj.id, 'quantidade_cotada': item.quantidade, 'obs': cotacao_obj.obs})

                        else:
                            dados = {
                                'codigo_cotacao': cotacao_obj.id,
                                'name': fornecedor.partner_id.id,
                                'product_id': item.product_id.product_tmpl_id.id,
                                'quantidade_cotada': item.quantidade,
                                'obs': cotacao_obj.obs,
                                'min_qty': 0,
                                'delay': 10,
                            }
                            supplier_id = supplier_pool.create(cr, uid, dados)
                            supplierinfo_ids.append(supplier_id)

                        chave = 'supplierinfo_%d_id' % i
                        item.write({chave: supplier_id})
                        i += 1

                dados_obj = {
                    'situacao': 'C',
                    'supplierinfo_ids': [[6, False, supplierinfo_ids]],
                }
                cotacao_obj.write(dados_obj)

                if 'equalizando' not in context:
                    cotacao_obj.compartilha_fornecedor()

        return res

    def equalizacao(self, cr, uid, ids, context={}):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        self.pool.get('purchase.cotacao').confirma_cotacao(cr, uid, ids, context={'equalizando': True})

        for cotacao_obj in self.browse(cr, uid, ids):
            for item_obj in cotacao_obj.item_ids:
                dados = {
                    'escolhido_1': False,
                    'escolhido_2': False,
                    'escolhido_3': False,
                    'escolhido_4': False,
                    'escolhido_5': False,
                    #'escolhido_6': False,
                    #'escolhido_7': False,
                    #'escolhido_8': False,
                    #'escolhido_9': False,
                    #'escolhido_10': False,

                    'preco_negociado_1': D(0),
                    'preco_negociado_2': D(0),
                    'preco_negociado_3': D(0),
                    'preco_negociado_4': D(0),
                    'preco_negociado_5': D(0),
                }

                escolhido = 0
                menor = 0

                for numero in range(1, 6):
                    valor = getattr(item_obj, 'total_%d' % numero, 0) or 0

                    supplierinfo_obj = getattr(item_obj, 'supplierinfo_%d_id' % numero, False)

                    if supplierinfo_obj:
                        dados['preco_negociado_%d' % numero] = D(supplierinfo_obj.preco or 0)

                    if valor > 0:
                        if menor == 0:
                            menor = valor
                            escolhido = numero

                        elif valor < menor:
                            menor = valor
                            escolhido = numero

                if escolhido != 0:
                    dados['escolhido_%d' % escolhido] = True

                item_obj.write(dados)


        return True

    def gera_pedido_compra(self, cr, uid, ids, context={}):
        supplier_pool = self.pool.get('product.supplierinfo')
        compra_pool = self.pool.get('purchase.order')
        item_pool = self.pool.get('purchase.order.line')
        orcamento_pool = self.pool.get('project.orcamento')
        location_pool = self.pool.get('stock.location')
        location_ids = location_pool.search(cr, uid, [('entrada_padrao', '=', True)])

        for cotacao_obj in self.browse(cr, uid, ids):

            obs = u''

            sql_obs = """
            select
                coalesce(psc.obs,'')
            from
                purchase_cotacao pc
                join purchase_cotacao_item_solicitacao pcis on pcis.cotacao_id = pc.id
                join purchase_solicitacao_cotacao_item_orcado pscio on pscio.id = pcis.solicitacao_item_id
                join purchase_solicitacao_cotacao psc on psc.id = pscio.solicitacao_id

            where
                pc.id = {cotacao_id}
            """
            sql_obs = sql_obs.format(cotacao_id=cotacao_obj.id)
            cr.execute(sql_obs)
            obs_objs = cr.fetchall()

            for observacao in obs_objs:
                obs += observacao[0] + u' '


            sql = """
select
    cotacao.*,
    si.name as partner_id

from (select
  coalesce(aac.company_id, pc.company_id) as company_id,
  pscio.project_id,
  pscio.orcamento_id,
  pscio.item_id,
  pscio.planejamento_id as planejamento_id,
  pscio.product_id,
  pscio.quantidade,
  pscio.centrocusto_id,
  case
      when pi.escolhido_1 then pi.supplierinfo_1_id
      when pi.escolhido_2 then pi.supplierinfo_2_id
      when pi.escolhido_3 then pi.supplierinfo_3_id
      when pi.escolhido_4 then pi.supplierinfo_4_id
      when pi.escolhido_5 then pi.supplierinfo_5_id
  end as supplierinfo_id,
  case
      when pi.escolhido_1 then pi.preco_negociado_1
      when pi.escolhido_2 then pi.preco_negociado_2
      when pi.escolhido_3 then pi.preco_negociado_3
      when pi.escolhido_4 then pi.preco_negociado_4
      when pi.escolhido_5 then pi.preco_negociado_5
  end as preco_negociado

from
    purchase_cotacao pc
    join purchase_cotacao_item_solicitacao pcis on pcis.cotacao_id = pc.id
    join purchase_solicitacao_cotacao_item_orcado pscio on pscio.id = pcis.solicitacao_item_id
    join purchase_cotacao_item pi on pi.cotacao_id = pc.id and pi.product_id = pscio.product_id
    left join project_project p on p.id = pscio.project_id
    left join account_analytic_account aac on aac.id = p.analytic_account_id

where
    pc.id = {cotacao_id}
) as cotacao
join product_supplierinfo si on si.id = cotacao.supplierinfo_id

order by
    partner_id,
    company_id,
    product_id;
            """
        sql = sql.format(cotacao_id=cotacao_obj.id)
        print(sql)
        cr.execute(sql)
        produtos = cr.fetchall()

        company_anterior_id = None
        partner_anterior_id = None
        compra_id = None
        compras = []

        for company_id, project_id, orcamento_id, item_id, planejamento_id, product_id, quantidade, centrocusto_id, supplier_id, preco_negociado, partner_id in produtos:
            print(project_id, company_anterior_id, partner_id, partner_anterior_id)
            if company_id != company_anterior_id or partner_id != partner_anterior_id:
            #if partner_id != partner_anterior_id:
                #project_obj = self.pool.get('project.project').browse(cr, uid, project_id)

                complemento = compra_pool.onchange_partner_id(cr, uid, False, partner_id)

                dados = complemento['value']

                dados.update({
                    'company_id': company_id,
                    'project_id': project_id,
                    'partner_id': partner_id,
                    'orcamento_id': orcamento_id,
                    'cotacao_id': cotacao_obj.id,
                    'location_id': location_ids[0],
                    'origin': u'Cotação ' + str(cotacao_obj.id) + u'; orçamento ' + str(orcamento_id),
                    'notes': obs,
                    'centrocusto_id': centrocusto_id,
                })
                compra_id = compra_pool.create(cr, uid, dados)
                compra_obj = compra_pool.browse(cr, uid, compra_id)
                compras.append(compra_id)
                partner_anterior_id = partner_id
                company_anterior_id = company_id

            complemento = item_pool.onchange_product_id(cr, uid, False, compra_obj.pricelist_id.id, product_id, quantidade, False, compra_obj.partner_id.id, compra_obj.date_order, False, False, False, False, False, context)

            dados = complemento['value']
            dados.update({
                'order_id': compra_id,
                'product_id': product_id,
                'product_qty': quantidade,
                'price_unit': preco_negociado,
                'orcamento_item_id': item_id,
                'orcamento_planejamento_id': planejamento_id,
                'centrocusto_id': centrocusto_id,
            })

            item_id = item_pool.create(cr, uid, dados)

            compra_pool.wkf_confirm_order(cr, uid, compras)
            cotacao_obj.write({'situacao': 'F'}, context={'aprovando_cotacao': True})

        return True

    def preparar_produtos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('purchase.cotacao.item')

        for cotacao_obj in self.browse(cr, uid, ids):
            #if cotacao_obj.situacao != 'A':
            #    continue

            itens = {}

            item_ids = item_pool.search(cr, uid, [('cotacao_id', '=', cotacao_obj.id)])
            item_pool.unlink(cr, uid, item_ids)

            #for plan_obj in cotacao_obj.planejamento_ids:
                #if not plan_obj.product_id.id in itens:
                    #itens[plan_obj.product_id.id] = 0

                #itens[plan_obj.product_id.id] += plan_obj.quantidade

            for solicitacao_obj in cotacao_obj.solicitacao_ids:
                if not solicitacao_obj.product_id.id in itens:
                    itens[solicitacao_obj.product_id.id] = 0

                itens[solicitacao_obj.product_id.id] += solicitacao_obj.quantidade


            for produto_id in itens:
                dados = {
                    'cotacao_id': cotacao_obj.id,
                    'product_id': produto_id,
                    'quantidade': itens[produto_id],
                }
                item_pool.create(cr, uid, dados)

    def preparar_arquivos_anexos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')

        cotacao_obj = self.pool.get('purchase.cotacao').browse(cr, uid, ids[0])

        solicitacao_ids = []
        for plan_obj in cotacao_obj.planejamento_ids:
            if plan_obj.solicitacao_id:
                if plan_obj.solicitacao_id.id not in solicitacao_ids:
                    solicitacao_ids.append(plan_obj.solicitacao_id.id)

        anexo_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'purchase.solicitacao.cotacao'), ('res_id', 'in', solicitacao_ids)])

        if len(anexo_ids):
            for anexo_obj in attachment_pool.browse(cr, uid, anexo_ids):
                dados = {
                    'datas': anexo_obj.datas,
                    'name': anexo_obj.name,
                    'datas_fname': anexo_obj.fname,
                    'file_type': anexo_obj.file_type,
                    'res_model': purchase.cotacao,
                    'res_id': cotacao_obj.id,
                }
                attachment_pool.create(cr, uid, dados)

    def enviar_email_compartilhamento(self, cr, uid, ids, usuario_id, context=None):
        #self._logger.info(u'Enviando emails de compartilhamento...')
        mail_pool = self.pool.get('mail.message')
        usuario_obj = self.pool.get('res.users').browse(cr, 1, uid)
        attachment_pool = self.pool.get('ir.attachment')

        if not usuario_obj.user_email:
            raise osv.except_osv(u'Email obrigatório!', u'Seu usuário precisa ter um endereço de email configurado nas preferências de usuário para poder enviar emails')

        #
        # Busca os arquivos anexos nas solicitações, e anexa aqui na cotação
        #
        self.pool.get('purchase.cotacao').preparar_arquivos_anexos(cr, uid, ids)

        cotacao_obj = self.pool.get('purchase.cotacao').browse(cr, uid, ids[0])
        #
        # Monta a url para o login
        #
        base_url = self.pool.get('ir.config_parameter').get_param(cr, 1, 'web.base.url', default='', context=context)
        base_url += '/web/webclient/home'

        #
        # Monta a mensagem de compartilhamento
        #
        texto = u'Olá,'
        texto += u'\n\n'
        texto += u'Eu compartilhei a cotação de compra nº [ {cotacao} ] com você!'
        texto += u'\n\n'
        texto += u'Os documentos não estão em anexo; você pode vê-los online diretamente no nosso sistema, no seguinte endereço:'
        texto += u'\n    ' + base_url
        texto += u'\n\n'

        texto += u'Para que você possa ter acesso à informação, use o seguinte nome de usuário e senha:\n'
        texto += u'Usuário: {login}\n'
        texto += u'Senha: {senha}\n'
        texto += u'Banco de dados: %s\n' % cr.dbname

        texto += u'\n\n'
        texto += (usuario_obj.signature or u'')
        texto += u'\n\n'
        texto += u'--\n'
        texto += u'Enviado usando o ERP Integra - www.ERPIntegra.com.br'

        assunto = u'Cotação de compra nº [ {cotacao} ]'

        assunto_email = assunto.format(cotacao=cotacao_obj.id)

        novo_usuario_obj = self.pool.get('res.users').browse(cr, 1, usuario_id)
        texto_email = texto.format(cotacao=cotacao_obj.id, login=novo_usuario_obj.login, senha=novo_usuario_obj.password)

        dados = {
            'subject':  assunto_email,
            'model': 'purchase.cotacao',
            'res_id': cotacao_obj.id,
            'user_id': usuario_obj.id,
            'email_to': novo_usuario_obj.login,
            'email_from': usuario_obj.user_email,
            'date': str(fields.datetime.now()),
            'headers': '{}',
            'email_cc': '',
            'reply_to': usuario_obj.user_email,
            'state': 'outgoing',
            'message_id': False,
            'body_text': texto_email,
            'body_html': False,
        }

        mail_id = mail_pool.create(cr, uid, dados)

        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'purchase.cotacao'), ('res_id', '=', cotacao_obj.id)])
        if len(attachment_ids):
            anexos = []
            for attachment_id in attachment_ids:
                anexos.append((4, attachment_id))
            mail_pool.write(cr, uid, mail_id, {'attachment_ids': anexos})

        mail_pool.process_email_queue(cr, uid, [mail_id])

        #nova_mensagem = mail_pool.schedule_with_attach(cr, uid, usuario_obj.user_email, [novo_usuario_obj.login],
                #assunto_email, texto_email, model='purchase.cotacao', context=context)

        #mail_pool.send(cr, uid, [nova_mensagem], context=context)
        ##self._logger.info(u'Emails de compartilhamento enviados.')

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Proíbe a reabertura de uma cotação aprovada anteriormente
        #
        if 'situacao' in dados and not 'aprovando_cotacao' in context:
            for cotacao_obj in self.pool.get('purchase.cotacao').browse(cr, uid, ids):
                if (cotacao_obj.situacao == 'F') and (len(cotacao_obj.purchase_order_ids)):
                    raise osv.except_osv(u'Erro!', u'Proibido alterar a situação de uma cotação fechada, e com pedidos de compra já gerados!')

        return super(purchase_cotacao, self).write(cr, uid, ids, dados, context=context)

    def unlink(self, cr, uid, ids, context={}):
        #
        # Proíbe a exclusão de uma cotação aprovada anteriormente
        #
        for cotacao_obj in self.pool.get('purchase.cotacao').browse(cr, uid, ids):
            if cotacao_obj.situacao != 'A':
                raise osv.except_osv(u'Erro!', u'Proibido excluir uma cotação em andamento!')

        return super(purchase_cotacao, self).unlink(cr, uid, ids, context=context)


purchase_cotacao()


class purchase_cotacao_planejamento(orm.Model):
    _name = 'purchase.cotacao.planejamento'

    _columns = {
        'cotacao_id': fields.many2one('purchase.cotacao', u'Cotação', ondelete='cascade'),
        'planejamento_id': fields.many2one('project.orcamento.item.planejamento', u'Planejamento', ondelete='restrict'),
    }

    _sql_constraints = [
        ('planejamento_unique', 'UNIQUE(planejamento_id)', u'O item planejado não pode se repetir, e ele já existe em outra cotação!')
    ]


purchase_cotacao_planejamento()


class purchase_cotacao_item(orm.Model):
    _name = 'purchase.cotacao.item'
    _description = u'Item da Cotação'
    _rec_name = 'quantidade'

    def _calcula_totais(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(0)


            if 'total_negociado_' in nome_campo:
                numero = nome_campo.split('_')[2]
                valor = D(item_obj.quantidade or 0) * D(getattr(item_obj, 'preco_negociado_%s' % numero, 0))
                print(numero, valor)

            else:
                numero = nome_campo.split('_')[1]
                if getattr(item_obj, 'supplierinfo_%s_id' % numero, False):
                    supplierinfo_obj = getattr(item_obj, 'supplierinfo_%s_id' % numero)
                    valor = D(item_obj.quantidade or 0) * D(supplierinfo_obj.preco or 0)

            res[item_obj.id] = valor

        return res

    def _get_supplier_info_id(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            res[item_obj.id] = False

            numero = int(nome_campo.split('_')[1])
            fornecedor_ids = self.pool.get('purchase.cotacao.fornecedor').search(cr, uid, [('cotacao_id', '=', item_obj.cotacao_id.id)], order='id')

            print('aqui')
            print(numero, fornecedor_ids)

            if numero <= len(fornecedor_ids):
                fornecedor_id = fornecedor_ids[numero - 1]
                fornecedor_obj = self.pool.get('purchase.cotacao.fornecedor').browse(cr, uid, fornecedor_id)
                print(fornecedor_obj)

                si_ids = self.pool.get('product.supplierinfo').search(cr, uid, [('name', '=', fornecedor_obj.partner_id.id), ('product_id', '=', item_obj.product_id.product_tmpl_id.id), ('codigo_cotacao', '=', item_obj.cotacao_id.id)])
                print(si_ids, item_obj.product_id.id, fornecedor_obj.partner_id.id)

                if len(si_ids):
                    res[item_obj.id] = si_ids[0]

        return res

    def _melhor_preco(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            melhor = D(0)

            for numero in range(1, 6):
                preco = D(getattr(item_obj, 'preco_%s' % numero, 0))

                if melhor == 0 and preco > 0:
                    melhor = preco
                elif preco > 0 and preco < melhor:
                    melhor = preco

            if nome_campo == 'melhor_total':
                melhor *= D(item_obj.quantidade or 0)

            res[item_obj.id] = melhor

        return res

    _columns = {
        'cotacao_id': fields.many2one('purchase.cotacao', string=u'Cotação', ondelete='cascade'),
        #'planejamento_id': fields.many2one('project.orcamento.item.planejamento', string=u'Item planejado', ondelete='restrict'),
        #'orcamento_id': fields.many2one('project.orcamento', string=u'Orçamento', ondelete='restrict'),
        #'etapa_id': fields.many2one('project.orcamento.etapa', string=u'Etapa', ondelete='restrict'),
        #'item_id': fields.many2one('project.orcamento.item', string=u'Item', ondelete='restrict'),
        'product_id': fields.many2one('product.product', string=u'Produto', ondelete='restrict'),
        'quantidade': fields.float(u'Quantidade'),
        'partner_id': fields.many2one('res.partner',string=u'Fornecedor', ondelete='restrict'),

        #
        # Dados do 1º fornecedor
        #
        'supplierinfo_1_id': fields.function(_get_supplier_info_id, type='many2one', relation='product.supplierinfo', string=u'Informações do fornecedor 1', store=True, index=True),
        'escolhido_1': fields.boolean(u'Sel. 1'),
        'preco_1': fields.related('supplierinfo_1_id', 'preco', type='float', string=u'Preço 1'),
        'condicao_pagamento_1': fields.related('supplierinfo_1_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 1'),
        'prazo_1': fields.related('supplierinfo_1_id', 'delay', type='integer', string=u'Prazo 1'),
        'total_1': fields.function(_calcula_totais, type='float', method=True, string=u'Total 1'),
        'preco_negociado_1': fields.float(u'Preço negociado 1'),
        'total_negociado_1': fields.function(_calcula_totais, type='float', method=True, string=u'Total negociado 1'),

        #
        # Dados do 2º fornecedor
        #
        'supplierinfo_2_id': fields.function(_get_supplier_info_id, type='many2one', relation='product.supplierinfo', string=u'Informações do fornecedor 2', store=True, index=True),
        'escolhido_2': fields.boolean(u'Sel. 2'),
        'preco_2': fields.related('supplierinfo_2_id', 'preco', type='float', string=u'Preço 2'),
        'condicao_pagamento_2': fields.related('supplierinfo_2_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 2'),
        'prazo_2': fields.related('supplierinfo_2_id', 'delay', type='integer', string=u'Prazo 2'),
        'total_2': fields.function(_calcula_totais, type='float', method=True, string=u'Total 2'),
        'preco_negociado_2': fields.float(u'Preço negociado 2'),
        'total_negociado_2': fields.function(_calcula_totais, type='float', method=True, string=u'Total negociado 2'),

        #
        # Dados do 3º fornecedor
        #
        'supplierinfo_3_id': fields.function(_get_supplier_info_id, type='many2one', relation='product.supplierinfo', string=u'Informações do fornecedor 3', store=True, index=True),
        'escolhido_3': fields.boolean(u'Sel. 3'),
        'preco_3': fields.related('supplierinfo_3_id', 'preco', type='float', string=u'Preço 3'),
        'condicao_pagamento_3': fields.related('supplierinfo_3_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 3'),
        'prazo_3': fields.related('supplierinfo_3_id', 'delay', type='integer', string=u'Prazo 3'),
        'total_3': fields.function(_calcula_totais, type='float', method=True, string=u'Total 3'),
        'preco_negociado_3': fields.float(u'Preço negociado 3'),
        'total_negociado_3': fields.function(_calcula_totais, type='float', method=True, string=u'Total negociado 3'),

        #
        # Dados do 4º fornecedor
        #
        'supplierinfo_4_id': fields.function(_get_supplier_info_id, type='many2one', relation='product.supplierinfo', string=u'Informações do fornecedor 4', store=True, index=True),
        'escolhido_4': fields.boolean(u'Sel. 4'),
        'preco_4': fields.related('supplierinfo_4_id', 'preco', type='float', string=u'Preço 4'),
        'condicao_pagamento_4': fields.related('supplierinfo_4_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 4'),
        'prazo_4': fields.related('supplierinfo_4_id', 'delay', type='integer', string=u'Prazo 4'),
        'total_4': fields.function(_calcula_totais, type='float', method=True, string=u'Total 4'),
        'preco_negociado_4': fields.float(u'Preço negociado 4'),
        'total_negociado_4': fields.function(_calcula_totais, type='float', method=True, string=u'Total negociado 4'),

        #
        # Dados do 5º fornecedor
        #
        'supplierinfo_5_id': fields.function(_get_supplier_info_id, type='many2one', relation='product.supplierinfo', string=u'Informações do fornecedor 5', store=True, index=True),
        'escolhido_5': fields.boolean(u'Sel. 5'),
        'preco_5': fields.related('supplierinfo_5_id', 'preco', type='float', string=u'Preço 5'),
        'condicao_pagamento_5': fields.related('supplierinfo_5_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 5'),
        'prazo_5': fields.related('supplierinfo_5_id', 'delay', type='integer', string=u'Prazo 5'),
        'total_5': fields.function(_calcula_totais, type='float', method=True, string=u'Total 5'),
        'preco_negociado_5': fields.float(u'Preço negociado 5'),
        'total_negociado_5': fields.function(_calcula_totais, type='float', method=True, string=u'Total negociado 5'),

        'melhor_preco': fields.function(_melhor_preco, type='float', method=True, string=u'Melhor preço'),
        'melhor_total': fields.function(_melhor_preco, type='float', method=True, string=u'Melhor total'),
        ###
        ### Dados do 6º fornecedor
        ###
        ##'supplierinfo_6_id': fields.many2one('product.supplierinfo', u'Informações do fornecedor 6'),
        ##'escolhido_6': fields.boolean(u'Sel. 6'),
        ##'preco_6': fields.related('supplierinfo_6_id', 'preco', type='float', string=u'Preço 6'),
        ##'condicao_pagamento_6': fields.related('supplierinfo_6_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 6'),
        ##'prazo_6': fields.related('supplierinfo_6_id', 'delay', type='integer', string=u'Prazo 6'),
        ##'total_6': fields.function(_calcula_totais, type='float', method=True, string=u'Total 6'),

        ###
        ### Dados do 7º fornecedor
        ###
        ##'supplierinfo_7_id': fields.many2one('product.supplierinfo', u'Informações do fornecedor 7'),
        ##'escolhido_7': fields.boolean(u'Sel. 7'),
        ##'preco_7': fields.related('supplierinfo_7_id', 'preco', type='float', string=u'Preço 7'),
        ##'condicao_pagamento_7': fields.related('supplierinfo_7_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 7'),
        ##'prazo_7': fields.related('supplierinfo_7_id', 'delay', type='integer', string=u'Prazo 7'),
        ##'total_7': fields.function(_calcula_totais, type='float', method=True, string=u'Total 7'),

        ###
        ### Dados do 8º fornecedor
        ###
        ##'supplierinfo_8_id': fields.many2one('product.supplierinfo', u'Informações do fornecedor 8'),
        ##'escolhido_8': fields.boolean(u'Sel. 8'),
        ##'preco_8': fields.related('supplierinfo_8_id', 'preco', type='float', string=u'Preço 8'),
        ##'condicao_pagamento_8': fields.related('supplierinfo_8_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 8'),
        ##'prazo_8': fields.related('supplierinfo_8_id', 'delay', type='integer', string=u'Prazo 8'),
        ##'total_8': fields.function(_calcula_totais, type='float', method=True, string=u'Total 8'),

        ###
        ### Dados do 9º fornecedor
        ###
        ##'supplierinfo_9_id': fields.many2one('product.supplierinfo', u'Informações do fornecedor 9'),
        ##'escolhido_9': fields.boolean(u'Sel. 9'),
        ##'preco_9': fields.related('supplierinfo_9_id', 'preco', type='float', string=u'Preço 9'),
        ##'condicao_pagamento_9': fields.related('supplierinfo_9_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 9'),
        ##'prazo_9': fields.related('supplierinfo_9_id', 'delay', type='integer', string=u'Prazo 9'),
        ##'total_9': fields.function(_calcula_totais, type='float', method=True, string=u'Total 9'),

        ###
        ### Dados do 10º fornecedor
        ###
        ##'supplierinfo_10_id': fields.many2one('product.supplierinfo', u'Informações do fornecedor 10'),
        ##'escolhido_10': fields.boolean(u'Sel. 10'),
        ##'preco_10': fields.related('supplierinfo_10_id', 'preco', type='float', string=u'Preço 10'),
        ##'condicao_pagamento_10': fields.related('supplierinfo_10_id', 'condicao_pagamento', type='char', string=u'Cond. pag. 10'),
        ##'prazo_10': fields.related('supplierinfo_10_id', 'delay', type='integer', string=u'Prazo 10'),
        ##'total_10': fields.function(_calcula_totais, type='float', method=True, string=u'Total 10'),
    }

    def onchange_planejamento_id(self, cr, uid, ids, planejamento_id, context={}):
        if not planejamento_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        planejamento_obj = self.pool.get('project.orcamento.item.planejamento').browse(cr, uid, planejamento_id)

        valores['orcamento_id'] = planejamento_obj.orcamento_id.id
        valores['etapa_id'] = planejamento_obj.etapa_id.id
        valores['item_id'] = planejamento_obj.item_id.id
        valores['product_id'] = planejamento_obj.product_id.id
        valores['quantidade'] = planejamento_obj.quantidade

        return res


purchase_cotacao_item()


class purchase_cotacao_fornecedor(orm.Model):
    _name = 'purchase.cotacao.fornecedor'
    _description = u'Fornecedor da Cotação'
    _rec_name = 'email'

    def _numero(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for forn_obj in self.browse(cr, uid, ids):
            sql = """select id from purchase_cotacao_fornecedor where cotacao_id = {cotacao_id} order by id;"""
            sql = sql.format(cotacao_id=forn_obj.cotacao_id.id)
            cr.execute(sql)

            ordem = []
            dados = cr.fetchall()
            for id, in dados:
                ordem.append(id)

            res[forn_obj.id] = ordem.index(forn_obj.id) + 1

        return res

    def _get_condicao_pagamento(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = ''

            if obj.cotacao_id and obj.cotacao_id.item_ids:
                item_obj = obj.cotacao_id.item_ids[0]

                if getattr(item_obj, 'supplierinfo_%s_id' % obj.numero, False):
                    supplierinfo_obj = getattr(item_obj, 'supplierinfo_%s_id' % obj.numero)
                    res[item_obj.id] = supplierinfo_obj.condicao_pagamento

        return res

    _columns = {
        'numero': fields.function(_numero, string=u'Nº', type='integer'),
        'cotacao_id': fields.many2one('purchase.cotacao',string=u'Cotação', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', string=u'Fornecedor', ondelete='restrict'),
        'address_id': fields.many2one('res.partner.address', string=u'Endereço', ondelete='restrict'),
        'email': fields.char(u'Email', size=60),
        'condicao_pagamento': fields.function(_get_condicao_pagamento, string=u'Condição de pagamento', type='char', size=60),
    }

    def onchange_partner_id(self, cursor, user_id, ids, partner_id, context=None):
        valores = {}
        retorno = {'value': valores}

        address_ids = self.pool.get('res.partner.address').search(cursor, user_id, [('partner_id','=', partner_id)], context=context)
        address_objs = self.pool.get('res.partner.address').browse(cursor, user_id, address_ids)
        for address_obj in  address_objs:
            if address_obj.type == 'purchase' or address_obj.type == 'compras':
                valores['email'] = address_obj.email or ''
                valores['address_id'] = address_obj.id
            else:
                valores['email'] = ''
                valores['address_id'] = False

        return retorno


purchase_cotacao_fornecedor()
