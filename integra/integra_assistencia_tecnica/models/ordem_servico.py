# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
import os
import base64
from finan.wizard.finan_relatorio import Report
from decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, dias_uteis
from datetime import timedelta
from .ordem_servico_etapa import TIPO_ETAPA
from .ordem_servico_cronometro import ATIVIDADE
from copy import copy
import random


TIPO_ORDEM = [
    ['1', u'Ordem de Serviço'],
    ['2', u'Orçamento de Serviço'],
]

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

class ordem_servico(osv.Model):
    _description = u'Ordem de Serviço'
    _name = 'ordem.servico'
    _inherit = 'mail.thread'
    _rec_name = 'numero'
    _order = 'data'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            if nome_campo == 'numero':
                res[os_obj.id] = os_obj.id
            else:
                res[os_obj.id] = u'[' + str(os_obj.id) + u'] - ' + os_obj.partner_id.name

        return res

    def _dias_uteis_ultima_etapa(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            tempo = 0

            if os_obj.data_ultima_etapa:
                data_inicial = parse_datetime(os_obj.data_ultima_etapa).date()
                dias = dias_uteis(data_inicial=data_inicial, estado=os_obj.company_id.partner_id.municipio_id.estado_id.uf, municipio=os_obj.company_id.partner_id.municipio_id.nome)
                tempo = len(dias) - 1

            res[os_obj.id] = tempo

        return res

    def _calcula_total(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            total = D(0)

            for item_obj in os_obj.produto_ids:
                total += D(item_obj.vr_total or 0)

            res[os_obj.id] = total

        return res

    _columns = {
        'numero': fields.function(_codigo, type='integer', method=True, string=u'Nº OS', store=True, select=True),
        'descricao': fields.function(_codigo, type='char', size=90, method=True, string=u'Nº OS', store=True, select=True),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'documentoitem_id': fields.many2one('sped.documentoitem', u'Item NF'),
        'partner_address_id': fields.many2one('res.partner.address', u'Contato'),
        'data': fields.date(u'Data'),
        'product_id': fields.many2one('product.product', u'Produto'),
        'marca': fields.related('product_id', 'variants', type='char', string=u'Marca', store=True, select=True),
        'numero_serie_id': fields.many2one('product.numero.serie', u'Número de série'),
        'laudo_cliente': fields.text(u'Laudo do cliente'),
        'tecnico_id': fields.many2one('res.users', u'Técnico'),
        #'reparo_id': fields.many2one('os.reparo', u'Reparo'),
        'defeito_constatado': fields.text(u'Defeito constatado'),
        #'servico_id': fields.many2one('product.product', u'Serviço' , domain = [('type','=','service')]),
        #'qtd_servico': fields.float(u'Serviço quantidade'),
        #'vr_unitario_servico': fields.float(u'Valor unit. Serviço'),
        'vr_frete': fields.float(u'Valor do frete'),
        'vr_total': fields.function(_calcula_total, type='float', method=True, string=u'Valor total', store=True, select=True),
        'acessorio_ids': fields.one2many('ordem.servico.acessorio','os_id',u'Acessorios'),
        'cronometro_ids': fields.one2many('ordem.servico.cronometro','os_id',u'Cronomentros'),
        'produto_ids': fields.one2many('ordem.servico.produto','os_id',u'Produtos'),
        'atividade': fields.selection(ATIVIDADE, u'Atividade'),

        'etapa_id': fields.many2one('ordem.servico.etapa', u'Etapa'),
        'codigo': fields.related('etapa_id', 'codigo', type='char', string=u'Código', store=False, select=True),
        'filtro_etapa': fields.related('etapa_id', 'filtro_etapa', type='char', string=u'filtro', store=False, select=True),
        'tipo_proxima_etapa': fields.related('etapa_id','tipo_proxima_etapa',  type='selection', relation='ordem.servico.etapa', selection=TIPO_ETAPA, string=u'Tipo Etapa', store=False),
        'proxima_etapa_id': fields.many2one('ordem.servico.etapa', u'Próxima Etapa'),
        'etapa_seguinte_ids': fields.related('etapa_id','etapa_seguinte_ids',  type='many2many', relation='ordem.servico.etapa', string=u'Proxima Etapa', store=False),

        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'ordem.servico')]),
        'crm_phonecall_ids': fields.one2many('crm.phonecall', 'ordem_servico_id', u'Ligações telefônicas'),
        'partner_fone': fields.related('partner_id', 'fone', type='char', string='Fone'),
        'partner_celular': fields.related('partner_id', 'celular', type='char', string='Celular'),
        'tipo_ordem': fields.selection(TIPO_ORDEM, u'Tipo Ordem'),
        'historico_ids': fields.one2many('ordem.servico.historico', 'os_id', u'Histórico de Etapas'),


        #
        # Dados da garantia
        #
        'sped_documento_garantia_id': fields.related('numero_serie_id', 'sped_documento_garantia_id', type='many2one', relation='sped.documento', string=u'NF início garantia'),
        'data_inicial_garantia': fields.related('numero_serie_id', 'data_inicial_garantia', type='date', string=u'Data início garantia'),
        'data_final_garantia': fields.related('numero_serie_id', 'data_final_garantia', type='date', string=u'Data final garantia'),

        #
        # Outras Notas Fiscais
        #
        'sped_documentoitem_ids': fields.one2many('sped.documentoitem', 'os_id', u'Notas Fiscais'),
        'sped_documento_ids': fields.one2many('sped.documento', 'os_id', u'Notas Fiscais'),

        'data_ultima_etapa': fields.datetime(u'Última etapa'),
        'dias_uteis_ultima_etapa': fields.function(_dias_uteis_ultima_etapa, type='integer', string=u'Dias'),

        #
        # Pagamento
        #
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict', select=True),
        'finan_carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict', select=True),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ordem.servico', context=c),
        #'qtd_servico': D(0),
        #'vr_unitario_servico':  D(0),
        'vr_frete':  D(0),
        'vr_total':  D(0),
        'atividade': 'A',
        'data': fields.datetime.now,
        'etapa_id': 1,
    }

    def calcula_valor(self, cr, uid, ids, qtd_servico, vr_unitario_servico, vr_frete):
        retorno = {}
        valores = {}

        quantidade = D(qtd_servico or 0)
        vr_unitario = D(vr_unitario_servico or 0).quantize(D('0.01'))
        vr_frete = D(vr_frete or 0).quantize(D('0.01'))

        vr_total = (quantidade * vr_unitario) + vr_frete
        vr_total = vr_total.quantize(D('0.01'))

        valores = {
            'vr_total':  vr_total,
        }
        retorno['value'] = valores

        return retorno

    def inicia_cronometro(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        cronometro_pool = self.pool.get('ordem.servico.cronometro')

        for ordem_obj in self.browse(cr, uid, ids):
            tecnico_id = ordem_obj.tecnico_id.id

            cronometro_ids = cronometro_pool.search(cr, uid, [('os_id', '=', ordem_obj.id), ('hora_final','=', False)])

            if len(cronometro_ids) > 0:
                raise osv.except_osv(u'Inválido!', u'Cronômetro está em aberto!')

            else:
                dados = {
                    'os_id': ordem_obj.id,
                    'tecnico_id': tecnico_id,
                    'atividade': ordem_obj.atividade,
                }
                cronometro_pool.create(cr, uid, dados)

        return

    def parar_cronometro(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for ordem_obj in self.browse(cr, uid, ids):
            tecnico_id = ordem_obj.tecnico_id.id

            for cronometro_obj in ordem_obj.cronometro_ids:
                if not cronometro_obj.hora_final:
                    cronometro_obj.write({'hora_final': fields.datetime.now()})

        return

    def avanca_etapa(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        historico_pool = self.pool.get('ordem.servico.historico')

        for ordem_obj in self.browse(cr, uid, ids):

            if not ordem_obj.proxima_etapa_id:
                raise osv.except_osv(u'Inválido !', u'Selecione a próxima etapa')

            ordem_obj.write({'etapa_id': ordem_obj.proxima_etapa_id.id, 'proxima_etapa_id':'' })

            dados = {
                'os_id': ordem_obj.id,
                'user_id': uid,
                'data': fields.datetime.now(),
                'etapa_id': ordem_obj.proxima_etapa_id.id,
            }
            historico_pool.create(cr, uid, dados)


        return

    def onchange_numero_serie_id(self, cr, uid, ids, numero_serie_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not numero_serie_id:
            return res

        numero_serie_obj = self.pool.get('product.numero.serie').browse(cr, uid, numero_serie_id)

        valores['data_inicial_garantia'] = numero_serie_obj.data_inicial_garantia
        valores['data_final_garantia'] = numero_serie_obj.data_final_garantia

        if numero_serie_obj.sped_documento_garantia_id:
            valores['sped_documento_garantia_id'] = numero_serie_obj.sped_documento_garantia_id.id
        else:
            valores['sped_documento_garantia_id'] = False

        return res

    def message_append(self, cr, uid, threads, subject, body_text=None, email_to=False, email_from=False, email_cc=None, email_bcc=None, reply_to=None, email_date=None, message_id=False, references=None, attachments=None, body_html=None, subtype=None, headers=None, original=None, context=None, forcar_data=False):
        if context is None:
            context = {}
        if attachments is None:
            attachments = {}

        if all(isinstance(thread_id, (int, long)) for thread_id in threads):
            model = context.get('thread_model') or self._name
            model_pool = self.pool.get(model)
            os_obj = model_pool.browse(cr, uid, threads, context=context)

            if not email_to:
                email_to = os_obj.partner_id.email_nfe or ''

        return super(ordem.servico, self).message_append(cr, uid, threads,
            subject, body_text=body_text, email_to=email_to,
            email_from=email_from, email_cc=email_cc, email_bcc=email_bcc,
            reply_to=reply_to, email_date=email_date, message_id=message_id,
            references=references, attachments=attachments, body_html=body_html,
            subtype=subtype, headers=headers, original=original, context=context,
            forcar_data=forcar_data)

    def message_new(self, cr, uid, msg_dict, custom_values=None, context=None):
        if context is None:
            context = {}
        model = context.get('thread_model') or self._name
        model_pool = self.pool.get(model)
        fields = model_pool.fields_get(cr, uid, context=context)
        data = model_pool.default_get(cr, uid, fields, context=context)
        if 'name' in fields and not data.get('name'):
            data['name'] = msg_dict.get('from','')
        if custom_values and isinstance(custom_values, dict):
            data.update(custom_values)
        res_id = model_pool.create(cr, uid, data, context=context)
        self.message_append_dict(cr, uid, [res_id], msg_dict, context=context)
        return res_id

    def agenda_ligacao(self, cr, uid, ids, hora, resumo_ligacao, descricao, fone, user_id, acao='schedule', context={}):
        """
        action :('schedule','Schedule a call'), ('log','Log a call')
        """
        ligacao_pool= self.pool.get('crm.phonecall')
        dados_ligacao = {}

        for os_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                    'name' : resumo_ligacao,
                    'ordem_servico_id': os_obj.id,
                    'user_id' : user_id or uid,
                    'categ_id' : False,
                    'description' : descricao or '',
                    'date' : hora,
                    'section_id' : False,
                    'partner_id': os_obj.partner_id and os_obj.partner_id.id or False,
                    'partner_address_id': False,
                    'partner_phone' : fone or '',
                    'partner_mobile' : '',
                    #'priority': saleorder_obj.priority,
            }

            ligacao_id = ligacao_pool.create(cr, uid, dados, context=context)
            ligacao_pool.case_open(cr, uid, [ligacao_id])
            if acao == 'log':
                ligacao_pool.case_close(cr, uid, [ligacao_id])
            dados_ligacao[saleorder_obj.id] = ligacao_id

        return dados_ligacao

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            lancamento_id = ids[0]

        if not lancamento_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'integra_sale', 'sale_nota_wizard')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'sale.nota',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'sale.order', 'active_ids': [lancamento_id]},
        }

        return retorno

    def imprime_ordem_servico(self, cr, uid, ids, context={}):

        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        if rel_obj.etapa_id.gera_orcamento:
            rel = Report('Orçamento de Serviço', cr, uid)
            tipo_ordem = '2'
        else:
            rel = Report('Ordem de Serviço', cr, uid)
            tipo_ordem = '1'

        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'asp_ordem_servico.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['TIPO'] = tipo_ordem
        nome = u'OS_' + str(rel_obj.numero)  + '.pdf'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'ordem.servico'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'ordem.servico',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def enviar_email_os(self, cr, uid, ids, context={}):

        if not ids:
            return False

        doc_pool = self.pool.get('ordem.servico')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)
        mail_pool = self.pool.get('mail.message')
        attachment_pool = self.pool.get('ir.attachment')

        print('vai fazer')
        if user_obj.user_email:
            for doc_obj in doc_pool.browse(cr, uid, ids):

                if doc_obj.partner_id.email_nfe:
                    self.imprime_ordem_servico(cr, uid, [doc_obj.id], context={})

                    dados = {
                        'subject':  u'Envio de Ordem de Serviço',
                        'model':  'ordem.servico',
                        'res_id': doc_obj.id,
                        'user_id': uid,
                        'email_to': doc_obj.partner_id.email_nfe or '',
                        #'email_to': 'william@erpintegra.com.br',
                        'email_from': user_obj.user_email,
                        'date': str(fields.datetime.now()),
                        'headers': '{}',
                        'email_cc': '',
                        'reply_to': user_obj.user_email,
                        'state': 'outgoing',
                        'message_id': False,
                    }

                    mail_id = mail_pool.create(cr, uid, dados)

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'ordem.servico'), ('res_id', '=', doc_obj.id)])
                    if len(attachment_ids):
                        anexos = []
                        for attachment_id in attachment_ids:
                            anexos.append((4, attachment_id))
                        mail_pool.write(cr, uid, mail_id, {'attachment_ids': anexos})

                    mail_pool.process_email_queue(cr, uid, [mail_id])

        return {'value': {}}

    def create(self, cr, uid, dados, context={}):
        dados['data_ultima_etapa'] = fields.datetime.now()

        return super(ordem_servico, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'etapa_id' in dados and dados['etapa_id']:
            dados['data_ultima_etapa'] = fields.datetime.now()

        if 'proxima_etapa_id' in dados and dados['proxima_etapa_id']:
            dados['data_ultima_etapa'] = fields.datetime.now()

        return super(ordem_servico, self).write(cr, uid, ids, dados, context=context)

    def _gera_nota(self, cr, uid, os_obj, produto_ids, company_id, operacao_obj):
        documento_pool = self.pool.get('sped.documento')
        documento_item_pool = self.pool.get('sped.documentoitem')

        dados = {
            'company_id': company_id,
            'operacao_id': operacao_obj.id,
            'partner_id': os_obj.partner_id.id,
            'os_id': os_obj.id,
        }

        nota_id = documento_pool.create(cr, uid, dados, context={'modelo': operacao_obj.modelo, 'default_modelo': operacao_obj.modelo})
        nota_obj = documento_pool.browse(cr, uid, nota_id)
        dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)

        #
        # Condição de pagamento informada na OS
        #
        if os_obj.payment_term_id:
            dados_operacao['value']['payment_term_id'] = os_obj.payment_term_id.id
        if os_obj.finan_carteira_id:
            dados_operacao['value']['finan_carteira_id'] = os_obj.finan_carteira_id.id
        if os_obj.res_partner_bank_id:
            dados_operacao['value']['res_partner_bank_id'] = os_obj.res_partner_bank_id.id
        nota_obj.write(dados_operacao['value'])

        contexto_item = copy(dados)
        for chave in dados:
            if 'default_' not in chave:
                contexto_item['default_' + chave] = contexto_item[chave]

        contexto_item['entrada_saida'] = nota_obj.entrada_saida
        contexto_item['regime_tributario'] = nota_obj.regime_tributario
        contexto_item['emissao'] = nota_obj.emissao
        contexto_item['data_emissao'] = nota_obj.data_emissao
        contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
        contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
        contexto_item['default_emissao'] = nota_obj.emissao
        contexto_item['default_data_emissao'] = nota_obj.data_emissao

        for produto_obj in self.pool.get('ordem.servico.produto').browse(cr, uid, produto_ids):
            dados = {
                'documento_id': nota_obj.id,
                'produto_id': produto_obj.product_id.id,
                'quantidade': produto_obj.qtd,
                'quantidade_tributacao': produto_obj.qtd,
                'modelo': nota_obj.modelo,
                'os_id': os_obj.id,
            }

            item_id = documento_item_pool.create(cr, uid, dados, context=contexto_item)
            item_obj = documento_item_pool.browse(cr, uid, item_id)

            dados_item = documento_item_pool.onchange_produto(cr, uid, False, produto_obj.product_id.id, context=contexto_item)
            item_obj.write(dados_item['value'])
            item_obj = documento_item_pool.browse(cr, uid, item_id)

            item_obj.quantidade = produto_obj.qtd
            item_obj.vr_unitario = produto_obj.vr_unitario

            dados_item = documento_item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
            item_obj.write(dados_item['value'])

        nota_obj.write({'recalculo': int(random.random() * 100000000)})

        #
        # Agora que a nota foi gerada, muda a etapa das OSs
        #
        if operacao_obj.ordem_servico_etapa_id:
            os_obj.write({'etapa_id': gera_nota_obj.operacao_id.ordem_servico_etapa_id.id, 'proxima_etapa_id':'' })

    def gerar_nota(self, cr, uid, ids, context={}):
        for os_obj in self.browse(cr, uid, ids):
            #
            # Primeiro, separamos o que é produto do que é serviço
            #

            if context.get('produtos', True):
                produto_ids = self.pool.get('ordem.servico.produto').search(cr, uid, [('os_id', '=', os_obj.id), ('product_id.type', '!=', 'service')])

                if len(produto_ids):
                    #
                    # Agora, separamos as empresas e operações fiscais para cada caso
                    #
                    empresa_produto_id = os_obj.company_id.id
                    operacao_produto_obj = os_obj.company_id.operacao_id
                    self._gera_nota(cr, uid, os_obj, produto_ids, empresa_produto_id, operacao_produto_obj)
            else:
                servico_ids = self.pool.get('ordem.servico.produto').search(cr, uid, [('os_id', '=', os_obj.id), ('product_id.type', '=', 'service')])

                if len(servico_ids):
                    #
                    # E dos serviços
                    #
                    if os_obj.company_id.company_servico_id:
                        empresa_servico_id = os_obj.company_id.company_servico_id.id
                        operacao_servico_obj = os_obj.company_id.company_servico_id.operacao_servico_id
                    else:
                        empresa_servico_id = os_obj.company_id.id
                        operacao_servico_obj = os_obj.company_id.operacao_servico_id

                    self._gera_nota(cr, uid, os_obj, servico_ids, empresa_servico_id, operacao_servico_obj)


ordem_servico()


class os_reparo(osv.Model):
    _description = u'Reparo'
    _name = 'os.reparo'
    _rec_name = 'nome'

    _columns = {
                'nome': fields.char(u'Nome', size=30),
    }

os_reparo()



class mail_compose_message(osv.osv_memory):
    """Generic E-mail composition wizard. This wizard is meant to be inherited
       at model and view level to provide specific wizard features.

       The behavior of the wizard can be modified through the use of context
       parameters, among which are:

         * mail.compose.message.mode: if set to 'reply', the wizard is in
                      reply mode and pre-populated with the original quote.
                      If set to 'mass_mail', the wizard is in mass mailing
                      where the mail details can contain template placeholders
                      that will be merged with actual data before being sent
                      to each recipient. Recipients will be derived from the
                      records determined via  ``context['active_model']`` and
                      ``context['active_ids']``.
         * active_model: model name of the document to which the mail being
                        composed is related
         * active_id: id of the document to which the mail being composed is
                      related, or id of the message to which user is replying,
                      in case ``mail.compose.message.mode == 'reply'``
         * active_ids: ids of the documents to which the mail being composed is
                      related, in case ``mail.compose.message.mode == 'mass_mail'``.
    """

    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context=None):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'ordem.servico':
            doc_obj = self.pool.get('ordem.servico').browse(cr, uid, res_id)

            res['email_to'] = doc_obj.partner_id.email_nfe or ''
            res['subject'] = u'Envio de OS'

        return res


mail_compose_message()
