# -*- coding: utf-8 -*-

from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64
from pybrasil.valor.decimal import Decimal as D
from pybrasil.base import DicionarioBrasil
from copy import copy


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')
TIPO_INTERNO = (
    ('R', u'Retorno'),
)

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)



class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _name = 'stock.picking'
    _rec_name = 'descricao'
    _order = 'name desc, date desc'

    def _get_descricao_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.name or ''

            if obj.partner_id:
                res[obj.id] += ' - '
                res[obj.id] += obj.partner_id.name or ''

        return res

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('name', 'ilike', texto),
            ('partner_id', 'ilike', texto)
        ]

        return procura

    def _get_trata_locacao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for picking_obj in self.browse(cr, uid, ids):
            res[picking_obj.id] = 0

            if picking_obj.sale_id and picking_obj.sale_id.orcamento_aprovado == 'locacao' and picking_obj.state == 'done':
                if len(picking_obj.sped_documento_ids) or len(picking_obj.entrega_ids):
                    res[picking_obj.id] = 1

        return res

    def _valor_padrao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for picking_obj in self.browse(cr, uid, ids, context=context):
            sql = """
            select
                m.{campo}
            from
                stock_move m
            where
                m.picking_id = {picking_id}
            order by
                m.id desc
            limit 1;
            """
            filtro = {
                'campo': nome_campo.replace('_padrao', ''),
                'picking_id': picking_obj.id,
            }
            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                res[picking_obj.id] = dados[0][0]

            else:
                res[picking_obj.id] = False

        return res
    
    def _saldo_zero(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for picking_obj in self.browse(cr, uid, ids, context=context):
            
            if len(picking_obj.sped_documento_ids) > 0:
                res[picking_obj.id] = True
            else:
                res[picking_obj.id] = False                
            
        return res

    _columns = {
        'address_id': fields.many2one('res.partner.address', u'Endereço', select=True),
        'partner_id': fields.many2one('res.partner', u'Cliente/Fornecedor', select=True),

        'cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'CNPJ'),

        'descricao': fields.function(_get_descricao_funcao, type='char', string=u'Descrição', fnct_search=_procura_descricao, store=True, select=True),
        'romaneio': fields.integer(u'Romaneio', select=True),
        'picking_id': fields.many2one('stock.picking', u'Lista de separação', select=True),
        'tipo': fields.selection(TIPO_INTERNO, u'Tipo interno'),
        'operacao_id': fields.many2one('stock.operacao', u'Operação', select=True),
        'saldo_obra_liberado': fields.boolean(u'Saldo da obra já liberado?'),
        'sped_documento_ids': fields.one2many('sped.documento', 'stock_picking_id', u'Notas Fiscais'),

        'picking_ids': fields.one2many('stock.picking', 'picking_id', u'Listas de separação derivadas'),
        'entrega_ids': fields.one2many('stock.picking', 'picking_id', u'Listas de separação derivadas', domain=[('type', '=', 'out')]),
        #'orcamento_aprovado': fields.related('sale_id', 'orcamento_aprovado', string=u'Orçamento aprovado para', store=True),
        'vendedor_id': fields.related('sale_id', 'user_id', type='many2one',relation='res.users',string='Vendedor',store=True),

        'trata_locacao_notas': fields.function(_get_trata_locacao, type='boolean', string=u'Precisa gerar notas de remessa', method=True),
        'trata_locacao_baixas': fields.function(_get_trata_locacao, type='boolean', string=u'Precisa gerar movimentações de baixa', method=True),

        'contrato_picking_ids': fields.many2many('stock.picking', 'stock_pickng_contrato_picking', 'picking_contrato_id', 'picking_id', u'Listas de separação dos contratos'),
        'contrato_nota_emitida_ids': fields.many2many('sped.documento', 'stock_picking_contrato_nf_emitida', 'picking_contrato_id', 'documento_id', u'NFs emitidas'),
        'contrato_nota_recebida_ids': fields.many2many('sped.documento', 'stock_picking_contrato_nf_recebida', 'picking_contrato_id', 'documento_id', u'NFs recebidas'),
        'contrato_inventario_ids': fields.related('finan_contrato_id', 'contrato_inventario_ids', type='one2many', relation='finan.contrato_inventario', string=u'Inventário no cliente'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'saldo_zero': fields.function(_saldo_zero, type='boolean', string=u'Saldo Zero', method=True, store=True),

        #
        # Campos para padrão
        #
        'date_padrao': fields.function(_valor_padrao, type='datetime', string=u'Data padrão'),
        'nota_origem_padrao': fields.function(_valor_padrao, type='char', string=u'Nota origem padrão'),
        'nota_retorno_padrao': fields.function(_valor_padrao, type='char', string=u'Nota retorno padrão'),
        'cnpj_padrao': fields.function(_valor_padrao, type='char', string=u'CNPJ padrão'),
    }

    _defaults = {
        'tipo': 'R',
        'formato': 'pdf',
    }

    def _valida_operacao_empresa(self, cr, uid, operacao_id, company_id):
        if not operacao_id or not company_id:
            return True

        operacao_obj = self.pool.get('stock.operacao').browse(cr, uid, operacao_id)

        if (not operacao_obj.company_id) and (not operacao_obj.company_ids):
            empresa_pode_usar = True
        else:
            empresa_pode_usar = False
            if operacao_obj.company_id and operacao_obj.company_id.id == company_id:
                empresa_pode_usar = True
            print(empresa_pode_usar)

            if len(operacao_obj.company_ids):
                for c_obj in operacao_obj.company_ids:
                    print('company_id', company_id, c_obj.id)
                    if c_obj.id == company_id:
                        empresa_pode_usar = True

        print(empresa_pode_usar)
        if not empresa_pode_usar:
            raise osv.except_osv(u'Inválido!', u'Operação não permitida para essa empresa/unidade!')

        return True

    def onchange_operacao_id(self, cr, uid, ids, operacao_id, company_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not operacao_id:
            return res

        operacao_obj = self.pool.get('stock.operacao').browse(cr, uid, operacao_id)
        self._valida_operacao_empresa(cr, uid, operacao_id, company_id)

        #valores['company_id'] = operacao_obj.company_id.id
        if operacao_obj.location_id:
            valores['location_id'] = operacao_obj.location_id.id
        if operacao_obj.location_dest_id:
            valores['location_dest_id'] = operacao_obj.location_dest_id.id
        valores['note'] = operacao_obj.obs

        if getattr(operacao_obj, 'familiatributaria_ids', False):
            familiatributaria_ids = []
            for ft_obj in operacao_obj.familiatributaria_ids:
                familiatributaria_ids.append(ft_obj.id)

            valores['familiatributaria_ids'] = familiatributaria_ids

        return res

    def onchange_picking_id(self, cr, uid, ids, picking_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not picking_id:
            return res

        picking_obj = self.pool.get('stock.picking').browse(cr, uid, picking_id)
        if picking_obj.sale_id:
            valores['sale_id'] = picking_obj.sale_id.id
        if picking_obj.purchase_id:
            valores['purchase_id'] = picking_obj.purchase_id.id

        return res

    def proximo_romaneio(self, cr, uid, ids, context={}):
        for picking_obj in self.browse(cr, uid, ids):
            ultimo_romaneio = 0
            for move_obj in picking_obj.move_lines:
                if move_obj.romaneio and move_obj.romaneio > ultimo_romaneio:
                    ultimo_romaneio = move_obj.romaneio

            picking_obj.write({'romaneio': ultimo_romaneio + 1})

    def imprime_romaneio(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        picking_obj = self.browse(cr, uid, id)

        if not picking_obj.formato:
            raise osv.except_osv(u'Inválido!', u'Adicionar um formato para impressão!')


        if not picking_obj.romaneio:
            picking_obj.romaneio = 2

        #
        # Ajusta romaneios
        #
        for move_obj in picking_obj.move_lines:
            if move_obj.state == 'done':
                self.pool.get('stock.move').ajusta_romaneio(cr, uid, [move_obj.id])

        for i in range(picking_obj.romaneio - 1):
            rel = Report('Romaneio de Ordem de Entrega', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_movimento_almoxarifado.jrxml')
            rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
            rel.parametros['ROMANEIO'] = i + 1
            rel.parametros['UID'] = uid

            if picking_obj.operacao_id and picking_obj.operacao_id.tipo == 'E':
                rel.parametros['TITULO'] = u'Termo de Compromisso de Entrega de E.P.I. (Equipamento de Proteção Individual)'
                rel.parametros['EPI'] = True
                #rel.parametros['ROMANEIO'] = '%' + str(picking_obj.id) + '%'
            elif 'saida' in context:
                rel.parametros['TITULO'] = u'SAÍDA - ROMANEIO ' + picking_obj.name + u'-' + str(i+1).zfill(2)
            else:
                rel.parametros['TITULO'] = u'ROMANEIO ' + picking_obj.name + u'-' + str(i+1).zfill(2)

            rel.outputFormat = picking_obj.formato

            nome_relatorio = u'romaneio_' + picking_obj.name + '_' + str(i+1).zfill(2) + '.' + picking_obj.formato
            pdf, formato = rel.execute()

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.picking'), ('res_id', '=', id), ('name', '=', nome_relatorio)])
            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_relatorio,
                'datas_fname': nome_relatorio,
                'res_model': 'stock.picking',
                'res_id': id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        #
        # 1 vez gerada a impressão, muda o nº para o próximo romaneio
        #
        self.proximo_romaneio(cr, uid, [id], context=context)

        return True

    def imprime_romaneio_zero(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        picking_obj = self.browse(cr, uid, id)

        rel = Report('Romaneio de Ordem de Entrega', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_movimento_almoxarifado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['ROMANEIO'] = 0
        rel.parametros['UID'] = uid

        if picking_obj.operacao_id and picking_obj.operacao_id.tipo == 'E':
            rel.parametros['TITULO'] = u'Termo de Compromisso de Entrega de E.P.I. (Equipamento de Proteção Individual)'
            rel.parametros['EPI'] = True
            rel.parametros['ROMANEIO'] = '%'
        elif 'saida' in context:
            rel.parametros['TITULO'] = u'SAÍDA - ROMANEIO DE PENDÊNCIA ' + picking_obj.name + u'-00'
        else:
            rel.parametros['TITULO'] = u'RETORNO - ROMANEIO DE PENDÊNCIA ' + picking_obj.name + u'-00'

        nome_relatorio = u'romaneio_pendencia_' + picking_obj.name + '_00.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.picking'), ('res_id', '=', id), ('name', '=', nome_relatorio)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_relatorio,
            'datas_fname': nome_relatorio,
            'res_model': 'stock.picking',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def imprime_saldo(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        picking_obj = self.browse(cr, uid, id)

        rel = Report('Saldo de Ordem de Entrega', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_saldo_almoxarifado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid
        rel.parametros['TITULO'] = u'SALDO DE INSTALAÇÃO ' + picking_obj.name

        nome_relatorio = u'saldo_' + picking_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.picking'), ('res_id', '=', id), ('name', '=', nome_relatorio)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_relatorio,
            'datas_fname': nome_relatorio,
            'res_model': 'stock.picking',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def imprimir_inventario_atulizado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        picking_obj = self.browse(cr, uid, id)

        rel = Report('Saldo de Inventário Cliente', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_inventario_atualizado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid
        rel.parametros['TITULO'] = u'SALDO INVENTÁRIO DE CLIENTE ' + picking_obj.name

        nome_relatorio = u'saldo_inventario_cliente_' + picking_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.picking'), ('res_id', '=', id), ('name', '=', nome_relatorio)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_relatorio,
            'datas_fname': nome_relatorio,
            'res_model': 'stock.picking',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def create(self, cr, uid, dados, context={}):
        if 'operacao_id' in dados and dados['operacao_id'] and 'company_id' in dados and dados['company_id']:
            self._valida_operacao_empresa(cr, uid, dados['operacao_id'], dados['company_id'])

        return super(stock_picking, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        for pick_obj in self.browse(cr, uid, ids):
            operacao_id = None
            if 'operacao_id' in dados:
                if dados['operacao_id']:
                    operacao_id = dados['operacao_id']

            elif pick_obj.operacao_id:
                operacao_id = pick_obj.operacao_id.id

            company_id = None
            if 'company_id' in dados:
                if dados['company_id']:
                    company_id = dados['company_id']

            elif pick_obj.company_id:
                company_id = pick_obj.company_id.id

            if operacao_id and company_id:
                self._valida_operacao_empresa(cr, uid, operacao_id, company_id)

        return super(stock_picking, self).write(cr, uid, ids, dados, context=context)

    def forca_novo(self, cr, uid, ids, context={}):
        for id in ids:
            cr.execute("update stock_picking set state = 'draft' where id = " + str(id) + ";")
            cr.execute("update stock_picking set saldo_obra_liberado = False where id = " + str(id) + ";")
            cr.execute("""
                update sale_order s set
                    saldo_obra_liberado = False

                where
                    s.id = (select sp.sale_id from stock_picking sp where sp.id = {picking_id});
            """.format(picking_id=id))

    def forca_concluido(self, cr, uid, ids, context={}):
        for id in ids:
            cr.execute("update stock_picking set state = 'done' where id = " + str(id) + ";")

    def forca_cancelamento_pedido_venda(self, cr, uid, ids, context={}):
        for pick_obj in self.browse(cr, uid, ids):
            pedido_obj = pick_obj.sale_id

            if pedido_obj.state != 'manual':
                raise osv.except_osv(u'Inválido!', u'O pedido de venda já foi concluído, e não pode mais ser cancelado!')

            #
            # Desvincula as ordens de entrega do pedido
            #
            cr.execute('update stock_picking set sale_id = null where sale_id = ' + str(pedido_obj.id))

            #
            # Agora, cancela pedido
            #
            pedido_obj.action_cancel()

        return True

    def ajusta_proposta_saldo(self, cr, uid, ids, context={}):
        picking_pool = self.pool.get('stock.picking')
        item_pool = self.pool.get('sale.order.line')
        produto_pool = self.pool.get('product.product')

        for pick_obj in self.browse(cr, uid, ids):
            if not pick_obj.sale_id:
                raise osv.except_osv(u'Inválido!', u'Sem proposta comercial vinculada!')

            #
            # Somente as propostas aprovadas podem ser alimentadas
            #
            print('pick_obj.sale_id.state', pick_obj.sale_id.state)
            if pick_obj.sale_id.state == 'done':
                raise osv.except_osv(u'Inválido!', u'A proposta comercial já foi concluída e não pode mais ser alterada!')
            elif pick_obj.sale_id.state != 'manual':
                raise osv.except_osv(u'Inválido!', u'A proposta comercial não está aprovada, e por isso não pode ser alterada através do saldo!')

            sale_obj = pick_obj.sale_id

            if not (sale_obj.pdf_versao_cliente and sale_obj.pdf_versao_detalhada):
                sale_obj.imprime_pdfs_aprovacao()


            sql = """
select

ss.orcamento_categoria_id,
ss.product_id,
ss.product_qty as produto_quantidade

from stock_saldo_separacao ss

where
  ss.picking_id = {picking_id}
  and ss.product_qty > 0

order by
  ss.product_id;
            """

            sql = sql.format(picking_id=pick_obj.id)
            print(sql)

            cr.execute(sql)
            dados = cr.fetchall()

            print('dados')
            print(dados)
            if not len(dados):
                continue

            saldo = {}
            for orcamento_categoria_id, product_id, quantidade in dados:
                chave = str(orcamento_categoria_id) + '_' + str(product_id)
                if chave not in saldo:
                    saldo[chave] = D(0)

                saldo[chave] += D(quantidade or 0)

            #
            # Agora que temos o saldo, vamos buscar os itens da proposta
            #
            itens_excluir = []
            produtos_excluir = []
            itens_alterar = []
            produtos_alterar = []
            itens_incluir = []
            for item_obj in sale_obj.order_line:
                #
                # Acessórios, mão de obra e mensalidades estão fora da análise
                #
                if item_obj.orcamento_categoria_id.id in (4, 6, 9):
                    continue

                chave = str(item_obj.orcamento_categoria_id.id) + '_' + str(item_obj.product_id.id)

                #
                # O produto não existe mais no saldo, vamos excluir
                #
                if chave not in saldo:
                    itens_excluir.append(item_obj.id)
                    produtos_excluir.append(chave)
                    continue

                #
                # Verifica se o produto já estava na prosposta (itens duplicados)
                #
                if chave in produtos_alterar:
                    itens_excluir.append(item_obj.id)
                    continue

                #
                # O produto já estava na proposta, vamos só alterar a quantidade
                #
                itens_alterar.append(item_obj.id)
                produtos_alterar.append(chave)

            #
            # Agora, agrupamos os novos itens que serão inseridos na proposta
            #
            for chave in saldo:
                if (chave not in produtos_excluir) and (chave not in produtos_alterar):
                    itens_incluir.append(chave)

            print('itens_excluir', itens_excluir)
            print('itens_alterar', itens_alterar)
            print('itens_incluir', itens_incluir)

            #
            # Agora, excluímos os itens efetivamente
            #
            print('vai excluir itens')
            item_pool.unlink(cr, uid, itens_excluir, context={'alimenta_saldo_obra': True})
            print('itens excluidos')

            #
            # Alteramos a quantidade dos itens
            #
            print('vai alterar os itens')
            for item_id in itens_alterar:
                print('vai alterar os itens', item_id)
                item_obj = item_pool.browse(cr, uid, item_id)
                chave = str(item_obj.orcamento_categoria_id.id) + '_' + str(item_obj.product_id.id)
                quantidade = saldo[chave]

                if item_obj.product_uom_qty == quantidade:
                    continue

                contexto_item = {
                    'partner_id': sale_obj.partner_id.id,
                    'quantity': quantidade,
                    'pricelist': sale_obj.pricelist_id.id,
                    'shop': sale_obj.shop_id.id,
                    'uom': item_obj.product_uom.id,
                    'operacao_fiscal_produto_id': sale_obj.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': sale_obj.operacao_fiscal_servico_id.id,
                    'company_id': sale_obj.company_id.id,
                }

                dados = item_obj.on_change_quantidade_margem_desconto(sale_obj.pricelist_id.id, item_obj.product_id.id, quantidade, item_obj.product_uom.id, quantidade, item_obj.product_uom.id, item_obj.name, sale_obj.partner_id.id, False, False, sale_obj.date_order, False, False, False, item_obj.vr_unitario_custo, item_obj.vr_unitario_minimo, item_obj.vr_unitario_venda, item_obj.margem, item_obj.discount, item_obj.autoinsert, True, item_obj.usa_unitario_minimo, contexto_item)
                valores = dados['value']

                dados = {}
                for chave in valores:
                    if (not chave.startswith('default_')) and (not isinstance(valores[chave], DicionarioBrasil)):
                        dados[chave] = valores[chave]

                dados['product_uom_qty'] = quantidade
                dados['product_uos_qty'] = quantidade
                print('alterando item', dados)
                item_obj.write(dados, context={'alimenta_saldo_obra': True})

            #
            # E, por último, inserimos os itens novos
            #
            print('vai inserir itens novos')
            for chave in itens_incluir:
                print('vai inserir item novo', chave)
                quantidade = saldo[chave]
                orcamento_categoria_id, product_id = chave.split('_')
                orcamento_categoria_id = int(orcamento_categoria_id)
                product_id = int(product_id)

                print('orcamento_categoria_id, product_id')
                print(orcamento_categoria_id, product_id)

                contexto_item = {
                    'partner_id': sale_obj.partner_id.id,
                    'quantity': quantidade,
                    'pricelist': sale_obj.pricelist_id.id,
                    'shop': sale_obj.shop_id.id,
                    'uom': item_obj.product_uom.id,
                    'force_product_uom': True,
                    'operacao_fiscal_produto_id': sale_obj.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': sale_obj.operacao_fiscal_servico_id.id,
                    'company_id': sale_obj.company_id.id,
                    'orcamento_aprovado': sale_obj.orcamento_aprovado,
                }

                dados = item_pool.product_id_change(cr, uid, [], sale_obj.pricelist_id.id, product_id, quantidade, item_obj.product_uom.id, quantidade, item_obj.product_uom.id, item_obj.name, sale_obj.partner_id.id, False, True, sale_obj.date_order, False, False, False, contexto_item)

                valores = dados['value']

                dados = {}
                for chave in valores:
                    if (not chave.startswith('default_')) and (not isinstance(valores[chave], DicionarioBrasil)):
                        dados[chave] = valores[chave]

                dados['order_id'] = sale_obj.id
                dados['product_id'] = product_id
                dados['orcamento_categoria_id'] = orcamento_categoria_id
                dados['product_uom_qty'] = quantidade
                dados['product_uos_qty'] = quantidade

                #produto_obj = produto_pool.browse(cr, uid, product_id)
                #if produto_obj.orcamento_categoria_id:
                    #dados['orcamento_categoria_id'] = produto_obj.orcamento_categoria_id.id
                #else:
                    #dados['orcamento_categoria_id'] = 1

                print('criando item novo', dados)
                item_novo_id = item_pool.create(cr, uid, dados, context={'alimenta_saldo_obra': True})
                print('item novo criado', item_novo_id)

            sale_obj.write({'saldo_obra_liberado': True})
            pick_obj.write({'saldo_obra_liberado': True})
            picking_pool.log(cr, uid, pick_obj.id, u'Proposta alimentada com o saldo da obra!')

    def gerar_notas_remessa_locacao(self, cr, uid, ids, context={}):
        res = {}
        nf_pool = self.pool.get('sped.documento')
        item_pool = self.pool.get('sped.documentoitem')

        for saida_obj in self.browse(cr, uid, ids):
            if not saida_obj.sale_id:
                continue

            if not saida_obj.sale_id.orcamento_aprovado == 'locacao':
                raise osv.except_osv(u'Erro!', u'Não é possível gerar a nota de remessa, pois a proposta comercial não é de locação!')

            if saida_obj.state != 'done':
                raise osv.except_osv(u'Erro!', u'Não é permitido gerar a nota de remessa antes de concluir o ordem de entrega!')

            #if saida_obj.trata_locacao_notas:
                #raise osv.except_osv(u'Erro!', u'Não é mais necessário gerar as notas de remessa!')

            #
            # Agora, vamos verificar as operações a serem usadas, e quais produtos
            # devem ir em cada nota
            #
            sql = """
            select
                ss.product_id,
                sum(ss.product_qty) as quantidade

            from
                stock_saldo_separacao ss
                join product_product p on p.id = ss.product_id

            where
                ss.picking_id = {saida_id}
                and ss.product_qty > 0
                and ss.location_id in ({local_ids})
                and p.familiatributaria_id in ({familiatributaria_ids})

            group by
                ss.product_id
            """

            operacao_produtos_novos_obj = saida_obj.sale_id.company_id.operacao_fiscal_remessa_locacao_novo_id
            itens_novos = {}
            if operacao_produtos_novos_obj:
                local_ids = []
                familiatributaria_ids = []

                for item_operacao_obj in operacao_produtos_novos_obj.nota_locacao_ids:
                    if item_operacao_obj.location_id.id not in local_ids:
                        local_ids.append(item_operacao_obj.location_id.id)
                    if item_operacao_obj.familiatributaria_id.id not in familiatributaria_ids:
                        familiatributaria_ids.append(item_operacao_obj.familiatributaria_id.id)

                local_ids = str(local_ids)
                local_ids = local_ids.replace('[', '')
                local_ids = local_ids.replace(']', '')

                familiatributaria_ids = str(familiatributaria_ids)
                familiatributaria_ids = familiatributaria_ids.replace('[', '')
                familiatributaria_ids = familiatributaria_ids.replace(']', '')

                sql_novos = sql.format(saida_id=saida_obj.id, local_ids=local_ids, familiatributaria_ids=familiatributaria_ids)
                print(sql_novos)
                cr.execute(sql_novos)
                dados = cr.fetchall()
                for product_id, quantidade in dados:
                    itens_novos[product_id] = quantidade

            operacao_produtos_usados_obj = saida_obj.sale_id.company_id.operacao_fiscal_remessa_locacao_usado_id
            itens_usados = {}
            if operacao_produtos_usados_obj:
                local_ids = []
                familiatributaria_ids = []

                for item_operacao_obj in operacao_produtos_usados_obj.nota_locacao_ids:
                    if item_operacao_obj.location_id.id not in local_ids:
                        local_ids.append(item_operacao_obj.location_id.id)
                    if item_operacao_obj.familiatributaria_id.id not in familiatributaria_ids:
                        familiatributaria_ids.append(item_operacao_obj.familiatributaria_id.id)

                local_ids = str(local_ids)
                local_ids = local_ids.replace('[', '')
                local_ids = local_ids.replace(']', '')

                familiatributaria_ids = str(familiatributaria_ids)
                familiatributaria_ids = familiatributaria_ids.replace('[', '')
                familiatributaria_ids = familiatributaria_ids.replace(']', '')

                sql_usados = sql.format(saida_id=saida_obj.id, local_ids=local_ids, familiatributaria_ids=familiatributaria_ids)
                cr.execute(sql_usados)
                dados = cr.fetchall()
                for product_id, quantidade in dados:
                    itens_usados[product_id] = quantidade

            if len(itens_novos):
                saida_obj._gerar_nota_remessa_locacao(saida_obj, operacao_produtos_novos_obj, itens_novos)

            if len(itens_usados):
                saida_obj._gerar_nota_remessa_locacao(saida_obj, operacao_produtos_usados_obj, itens_usados)

        return {}

    def _gerar_nota_remessa_locacao(self, cr, uid, ids, saida_obj, operacao_obj, itens):
        nf_pool = self.pool.get('sped.documento')
        item_pool = self.pool.get('sped.documentoitem')

        dados_nota = {}
        dados_nota['company_id'] = saida_obj.sale_id.company_id.id
        dados_nota['partner_id'] = saida_obj.sale_id.partner_id.id
        dados_nota['operacao_id'] = operacao_obj.id
        dados_nota['stock_picking_id'] = saida_obj.id

        nota_id = nf_pool.create(cr, uid, dados_nota, context={'modelo': '55', 'default_modelo': '55', 'default_company_id': saida_obj.sale_id.company_id.id, 'company_id': saida_obj.sale_id.company_id.id})
        nota_obj = nf_pool.browse(cr, uid, nota_id)

        dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)
        print('dados_operacao')
        print(dados_operacao)
        nota_obj.write(dados_operacao['value'])
        dados_nota.update(dados_operacao['value'])

        nota_obj = nf_pool.browse(cr, uid, nota_id)

        contexto_item = copy(dados_nota)
        for chave in dados_nota:
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

        for product_id in itens:
            dados = {
                'documento_id': nota_obj.id,
                'produto_id': product_id,
                'quantidade': itens[product_id],
            }

            item_id = item_pool.create(cr, uid, dados, contexto_item)
            item_obj = item_pool.browse(cr, uid, item_id)
            dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)
            item_obj.write(dados_item['value'])
            item_obj = item_pool.browse(cr, uid, item_id)

            dados_item = item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
            item_obj.write(dados_item['value'])

        nota_obj.ajusta_impostos_retidos()


    def gerar_movimentacao_baixa_locacao(self, cr, uid, ids, context={}):
        res = {}
        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')

        for saida_obj in self.browse(cr, uid, ids):
            if not saida_obj.sale_id:
                continue

            if not saida_obj.sale_id.orcamento_aprovado == 'locacao':
                raise osv.except_osv(u'Erro!', u'Não é possível gerar a movimentação de baixa, pois a proposta comercial não é de locação!')

            if saida_obj.state != 'done':
                raise osv.except_osv(u'Erro!', u'Não é permitido gerar a movimentação de baixa antes de concluir o ordem de entrega!')

            #if saida_obj.trata_locacao_notas:
                #raise osv.except_osv(u'Erro!', u'Não é mais necessário gerar as movimentações de baixa!')

            print('chegou aqui')

            #
            # Agora, vamos verificar as operações a serem usadas, e quais produtos
            # devem ir em cada nota
            #
            sql = """
            select
                ss.product_id,
                ss.product_qty as quantidade,
                ss.orcamento_categoria_id

            from
                stock_saldo_separacao ss
                join product_product p on p.id = ss.product_id

            where
                ss.picking_id = {saida_id}
                and ss.product_qty > 0
                and ss.location_id in ({local_ids})
                and p.familiatributaria_id in ({familiatributaria_ids})
            """

            operacao_produtos_novos_obj = saida_obj.sale_id.company_id.operacao_estoque_baixa_locacao_novo_id
            itens_novos = {}
            if operacao_produtos_novos_obj:
                local_ids = []
                familiatributaria_ids = []

                for item_operacao_obj in operacao_produtos_novos_obj.nota_locacao_ids:
                    if item_operacao_obj.location_id.id not in local_ids:
                        local_ids.append(item_operacao_obj.location_id.id)
                    if item_operacao_obj.familiatributaria_id.id not in familiatributaria_ids:
                        familiatributaria_ids.append(item_operacao_obj.familiatributaria_id.id)

                local_ids = str(local_ids)
                local_ids = local_ids.replace('[', '')
                local_ids = local_ids.replace(']', '')

                familiatributaria_ids = str(familiatributaria_ids)
                familiatributaria_ids = familiatributaria_ids.replace('[', '')
                familiatributaria_ids = familiatributaria_ids.replace(']', '')

                sql_novos = sql.format(saida_id=saida_obj.id, local_ids=local_ids, familiatributaria_ids=familiatributaria_ids)
                print(sql_novos)
                cr.execute(sql_novos)
                dados = cr.fetchall()
                for product_id, quantidade, orcamento_categoria_id in dados:
                    if product_id not in itens_novos:
                        itens_novos[product_id] = []

                    itens_novos[product_id].append([quantidade, orcamento_categoria_id])

            operacao_produtos_usados_obj = saida_obj.sale_id.company_id.operacao_estoque_baixa_locacao_usado_id
            itens_usados = {}
            if operacao_produtos_usados_obj:
                local_ids = []
                familiatributaria_ids = []

                for item_operacao_obj in operacao_produtos_usados_obj.nota_locacao_ids:
                    if item_operacao_obj.location_id.id not in local_ids:
                        local_ids.append(item_operacao_obj.location_id.id)
                    if item_operacao_obj.familiatributaria_id.id not in familiatributaria_ids:
                        familiatributaria_ids.append(item_operacao_obj.familiatributaria_id.id)

                local_ids = str(local_ids)
                local_ids = local_ids.replace('[', '')
                local_ids = local_ids.replace(']', '')

                familiatributaria_ids = str(familiatributaria_ids)
                familiatributaria_ids = familiatributaria_ids.replace('[', '')
                familiatributaria_ids = familiatributaria_ids.replace(']', '')

                sql_usados = sql.format(saida_id=saida_obj.id, local_ids=local_ids, familiatributaria_ids=familiatributaria_ids)
                cr.execute(sql_usados)
                dados = cr.fetchall()
                for product_id, quantidade, orcamento_categoria_id in dados:
                    if product_id not in itens_usados:
                        itens_usados[product_id] = []

                    itens_usados[product_id].append([quantidade, orcamento_categoria_id])

            if len(itens_novos):
                saida_obj._gerar_movimentacao_baixa_locacao(saida_obj, operacao_produtos_novos_obj, itens_novos)

            if len(itens_usados):
                saida_obj._gerar_movimentacao_baixa_locacao(saida_obj, operacao_produtos_usados_obj, itens_usados)

        return {}

    def _gerar_movimentacao_baixa_locacao(self, cr, uid, ids, saida_obj, operacao_obj, itens):
        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')

        dados_movimentacao = {
            'company_id': saida_obj.sale_id.company_id.id,
            'partner_id': saida_obj.sale_id.partner_id.id,
            'operacao_id': operacao_obj.id,
            'picking_id': saida_obj.id,
            'type': 'out',
            'origin': saida_obj.name,
            'date': fields.date.today(),
            'location_id': operacao_obj.location_id.id,
            'location_dest_id': operacao_obj.location_dest_id.id,
        }

        picking_id = picking_pool.create(cr, uid, dados_movimentacao)
        picking_obj = picking_pool.browse(cr, uid, picking_id)
        dados_operacao = picking_obj.onchange_operacao_id(saida_obj.operacao_id.sped_operacao_id.id, saida_obj.company_id.id)
        picking_obj.write(dados_operacao['value'])
        dados_movimentacao.update(dados_operacao['value'])

        contexto_item = copy(dados_movimentacao)
        contexto_item['picking_type'] = 'out'

        if 'address_id' in dados_movimentacao:
            contexto_item['address_out_id'] = dados_movimentacao['address_id']

        for chave in dados_movimentacao:
            if 'default_' not in chave:
                contexto_item['default_' + chave] = contexto_item[chave]

        for product_id in itens:
            for item_produto in itens[product_id]:
                dados_item = move_pool.onchange_product_id(cr, uid, False, product_id, operacao_obj.location_id.id, operacao_obj.location_dest_id.id)
                dados = dados_item['value']
                dados['picking_id'] = picking_id
                dados['product_id'] = product_id
                dados['product_qty'] = item_produto[0]
                dados['product_uos_qty'] = item_produto[0]
                dados['state'] = 'done'
                dados['orcamento_categoria_id'] = item_produto[1]

                move_pool.create(cr, uid, dados, contexto_item)

        picking_obj.write({'state': 'done'})


    def gerar_notas_remessa_baixa_locacao(self, cr, uid, ids, context={}):
        print(ids, context)
        self.pool.get('stock.picking').gerar_movimentacao_baixa_locacao(cr, uid, ids, context=context)
        self.pool.get('stock.picking').gerar_notas_remessa_locacao(cr, uid, ids, context=context)

    def liberar_proposta_faturamento(self, cr, uid, ids, context={}):
        picking_pool = self.pool.get('stock.picking')

        for saida_obj in self.browse(cr, uid, ids):
            if not saida_obj.sale_id:
                continue

            pedido_obj = saida_obj.sale_id

            if not pedido_obj.orcamento_aprovado == 'venda':
                raise osv.except_osv(u'Erro!', u'Não é possível liberar uma proposta de locação para faturamento, somente propostas de venda!')

            if saida_obj.state != 'done':
                raise osv.except_osv(u'Erro!', u'Não é permitido liberar uma proposta para faturamento antes de concluir o ordem de entrega!')

            if not pedido_obj.saldo_obra_liberado:
                raise osv.except_osv(u'Erro!', u'Não é permitido liberar uma proposta para faturamento se o saldo da obra ainda não tiver sido liberado!')

            if pedido_obj.state != 'manual':
                raise osv.except_osv(u'Erro!', u'Não é permitido liberar uma proposta para faturamento se ela não estiver aprovada, ou se já tiver sido concluída!')

            pedido_obj.encerrar_pedido()
            picking_pool.log(cr, uid, saida_obj.id, u'Proposta liberada para faturamento!')

        return True

    def abre_ordem_entrega(self, cr, uid, ids, context={}):
        return {
            'type': 'ir.actions.act_window',
            'name': u'Ordem de baixa',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': ids[0],
            'target': 'current',
        }

    def onchange_finan_contrato_id(self, cr, uid, ids, finan_contrato_id):
        if not finan_contrato_id:
            return res

        valores = {}
        res = {'value': valores}

        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, finan_contrato_id)
        valores['company_id'] = contrato_obj.company_id.id
        valores['partner_id'] = contrato_obj.partner_id.id
        valores['cnpj_cpf'] = contrato_obj.company_id.cnpj_cpf

        return res

    def gera_inventario_cliente(self, cr, uid, ids, context={}):
        inventario_pool = self.pool.get('finan.contrato_inventario')

        for picking_obj in self.browse(cr, uid, ids, context=context):
            if picking_obj.type != 'invcli':
                continue

            if not picking_obj.finan_contrato_id:
                continue

            picking_ids = [picking_obj.id]
            for p_obj in picking_obj.contrato_picking_ids:
                picking_ids.append(p_obj.id)

            nf_emitida_ids = []
            for nota_obj in picking_obj.contrato_nota_emitida_ids:
                nf_emitida_ids.append(nota_obj.id)

            nf_recebida_ids = []
            for nota_obj in picking_obj.contrato_nota_recebida_ids:
                nf_recebida_ids.append(nota_obj.id)


            #
            # Calculamos agora o saldo da instalação do cliente
            # para o local 19 - Cliente LOCADO
            #
            sql = """
                select
                    sm.product_id,
                    max(sm.date) as data,
                    sum(
                    case
                    {qtd_nf_emitida}
                    {qtd_nf_recebida}
                    when sm.location_id = 19 then coalesce(sm.product_qty, 0) * -1
                    when sm.location_dest_id = 19 then coalesce(sm.product_qty, 0)
                    end) as quantidade

                from
                    stock_move sm
                    join product_product p on p.id = sm.product_id
                    left join stock_picking sp on sp.id = sm.picking_id
                    left join sped_documentoitem di on di.id = sm.sped_documentoitem_id
                    left join sped_documento d on d.id = di.documento_id

                where
                    (sm.location_id = 19 or sm.location_dest_id = 19)
                    -- and sm.state = 'done'
                    and (sp.id in {picking_ids}
                    {filtro_notas})

                group by
                    sm.product_id
            """
            filtro = {
                'picking_ids': str(tuple(picking_ids)).replace(',)', ')'),
                'qtd_nf_emitida': '',
                'qtd_nf_recebida': '',
                'filtro_notas': '',
            }

            if len(nf_recebida_ids) or len(nf_emitida_ids):
                nf_ids = nf_recebida_ids + nf_emitida_ids

                filtro['filtro_notas'] = 'or d.id in ' + str(tuple(nf_ids)).replace(',)', ')')

                if nf_recebida_ids:
                    filtro['qtd_nf_recebida'] = 'when d.id is not null and d.id in {nf_recebida_ids} then coalesce(sm.product_qty, 0) * -1'.format(nf_recebida_ids=str(tuple(nf_recebida_ids)).replace(',)', ')'))

                if nf_emitida_ids:
                    filtro['qtd_nf_emitida'] = 'when d.id is not null and d.id in {nf_emitida_ids} then coalesce(sm.product_qty, 0)'.format(nf_emitida_ids=str(tuple(nf_emitida_ids)).replace(',)', ')'))

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            inventario = cr.fetchall()

            #
            # Apagamos o inventário atual
            #
            contrato_obj = picking_obj.finan_contrato_id

            for i_obj in contrato_obj.contrato_inventario_ids:
                i_obj.unlink()

            for product_id, data, quantidade in inventario:
                if not quantidade:
                    continue

                sql = """
                select
                    coalesce((
                        select
                            cm.vr_unitario_custo
                        from
                            custo_medio(5, 27, {produto_id}) cm
                        where
                            cm.data <= '{data}'
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc
                        limit 1), 0) as custo_medio,
                    t.standard_price

                from
                    product_product p
                    join product_template t on t.id = p.product_tmpl_id

                where
                    p.id = {produto_id};
                """
                sql = sql.format(produto_id=product_id, data=data)
                cr.execute(sql)
                dados = cr.fetchall()

                vr_unitario = D(0)

                if len(dados):
                    vr_unitario = D(dados[0][0] or 0)

                if vr_unitario <= 0 and len(dados):
                    vr_unitario = D(dados[0][1] or 0)

                if quantidade > 0:
                    dados = {
                        'contrato_id': contrato_obj.id,
                        'product_id': product_id,
                        'data': data,
                        'quantidade': quantidade,
                        'vr_unitario': vr_unitario,
                        'vr_total': vr_unitario * quantidade,
                    }
                else:
                    dados = {
                        'contrato_id': contrato_obj.id,
                        'product_id': product_id,
                        'data': data,
                        'quantidade': quantidade,
                        'vr_unitario': 0,
                        'vr_total': 0,
                    }

                if product_id == 1138:
                    print(dados)

                inventario_pool.create(cr, uid, dados)


stock_picking()
