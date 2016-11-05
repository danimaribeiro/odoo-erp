# -*- encoding: utf-8 -*-


from datetime import datetime
from decimal import Decimal as D
from osv import osv, fields
import os
import base64
from openerp import SUPERUSER_ID
from sale_order_line import sale_order_line
from finan.wizard.finan_relatorio import Report, JASPER_BASE_DIR
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, hoje
from tools.translate import _
import netsvc
import random

#from datetime import datetime, timedelta
#from dateutil.relativedelta import relativedelta
#import time
#import pooler
#from osv import fields, osv
#from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
#import decimal_precision as dp

sale_order_line()

STORE_TOTAL = True


SQL_LOCAL_LOCACAO = """
select
    slc.stock_location_id

from stock_location_company slc
join stock_location l on l.id = slc.stock_location_id

where
    l.padrao_locacao = True
    and slc.company_id = {company_id};
"""

SQL_LOCAL_VENDA = """
select
    slc.stock_location_id

from stock_location_company slc
join stock_location l on l.id = slc.stock_location_id

where
    l.padrao_venda = True
    and slc.company_id = {company_id};
"""

SQL_LOCAL_SAIDA = """
select
    slc.stock_location_id

from stock_location_company slc
join stock_location l on l.id = slc.stock_location_id

where
    l.saida_padrao = True
    and slc.company_id = {company_id};
"""


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def _versao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        for registro in self.browse(cursor, user_id, ids):
            txt = registro.sale_order_id.name + '/' + str(datetime.today().year) + '-' + str(len(registro.sale_order_id.orcamento_ids) + 1).zfill(2)

            retorno[registro.id] = txt

        return retorno

    def _calcula_totais(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for ol_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if nome_campo != 'vr_desconto_rateio':
                sql = """
                    select
                        sum(coalesce(oi.{campo}, 0)) as vr_total
                    from
                        orcamento_orcamento_locacao oi
                        join orcamento_categoria c on c.id= oi.orcamento_categoria_id
                    where
                        oi.sale_order_id = {orc_id}
                """
            else:
                sql = """
                    select
                        sum(coalesce(oi.discount, 0)) as vr_total
                    from
                        sale_order_line oi
                        join orcamento_categoria c on c.id= oi.orcamento_categoria_id
                    where
                        oi.order_id = {orc_id}
                """

            if nome_campo in ['vr_total_custo', 'vr_total_minimo', 'vr_total', 'vr_total_margem_desconto', 'vr_total_venda_impostos']:
                sql += """
                    and c.considera_venda = True
                """

            sql = sql.format(campo=nome_campo, orc_id=ol_obj.id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                valor = D(dados[0][0] or 0)

            res[ol_obj.id] = valor

        return res


    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa'),
        'shop_id': fields.many2one('sale.shop', u'Estabelecimento', required=False, readonly=False, states={'draft': [('readonly', False)]}),
        'crm_lead_id': fields.many2one('crm.lead', u'Oportunidade'),

        'name': fields.char('Código', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'versao': fields.char(u'Orçamento', size=20, readonly=True, states={'draft': [('readonly', False)]}),
        'orcamento_aprovado': fields.selection([('venda', 'venda'), ('locacao', u'locação')], u'Orçamento aprovado para', required=True),
        'orcamento_item_ids': fields.one2many('sale.order.line', 'order_id', u'Itens do orçamento'),
        'orcamento_item_grafico_ids': fields.one2many('sale.order.line', 'order_id', u'Itens do orçamento para o gráfico'),
        'orcamento_locacao_ids': fields.one2many('orcamento.orcamento_locacao', 'sale_order_id', u'Resumo do orçamento - locação'),
        'orcamento_locacao_grafico_ids': fields.one2many('sale.order.line', 'order_id', u'Resumo do orçamento - locação para o gráfico'),
        'orcamento_resumo_ids': fields.one2many('orcamento.orcamento_locacao', 'sale_order_id', u'Resumo do orçamento'),
        #'vr_total_custo': fields.float('Valor total de custo'),
        #'vr_total_minimo': fields.float('Valor total mínimo'),
        #'vr_total': fields.float('Valor total'),
        #'vr_total_margem_desconto': fields.float('Valor total com margem e desconto'),
        #'meses_retorno_investimento': fields.float('Meses para locação'),
        #'vr_mensal': fields.float('Valor mensal'),
        #'vr_comissao': fields.float(u'Valor comissão'),
        #'vr_comissao_locacao': fields.float(u'Valor comissão locação'),
        #'vr_total_venda_impostos': fields.float(u'Valor venda'),

        'vr_desconto_rateio': fields.function(_calcula_totais, string=u'Valor total de custo', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_total_custo': fields.function(_calcula_totais, string=u'Valor total de custo', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_total_minimo': fields.function(_calcula_totais, string=u'Total para locação', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_total': fields.function(_calcula_totais, string=u'Total', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_total_margem_desconto': fields.function(_calcula_totais, string=u'Total + margem - desconto', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_total_venda_impostos': fields.function(_calcula_totais, string=u'Valor venda', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_comissao': fields.function(_calcula_totais, string=u'Valor comissão venda', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_comissao_locacao': fields.function(_calcula_totais, string=u'Valor comissão locação', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'vr_mensal': fields.function(_calcula_totais, string=u'Valor mensal locação', type='float', method=True, store=STORE_TOTAL, digits=(18,2)),
        'meses_retorno_investimento': fields.function(_calcula_totais, string=u'Meses para locação', type='float', method=True, store=STORE_TOTAL),

        #
        # Funcoes para filtrar datas por periodo
        #
        'date_order_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De data do pedido'),
        'date_order_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A data do pedido'),

        'state': fields.selection([
            ('draft', u'Orçamento'),
            ('waiting_date', u'Aguardando agendamento'),
            ('manual', u'Para faturar'),
            ('progress', u'Em andamento'),
            ('shipping_except', u'Exceção de entrega'),
            ('invoice_except', u'Exceção de faturamento'),
            ('done', u'Concluído'),
            ('cancel', u'Cancelado')
            ], u'Situação', readonly=True, help=u"Informa a Situação do orçamento ou pedido. A Situação de Exceção é automaticamente definida quando um Cancelamento ocorre na validação do faturamento (Exceção de faturamento) ou no processo de separação (Excessão de entrega). O 'Aguardando agendamento' é definido quando a fatura está confirmada, mas está esperando o agendamento na data do pedido.", select=True),

        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'desvincula_itens': fields.boolean(u'Desvincula itens'),
    }

    _defaults = {
        'orcamento_aprovado': 'venda',
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c),
        'desvincula_itens': False,
    }

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        location_id = False

        if order.orcamento_aprovado == 'venda':
            sql = SQL_LOCAL_VENDA
        elif order.orcamento_aprovado == 'locacao':
            sql = SQL_LOCAL_LOCACAO
        else:
            sql = SQL_LOCAL_SAIDA

        sql = sql.format(company_id=order.company_id.id)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            location_id = dados[0][0]
        else:
            sql = SQL_LOCAL_SAIDA
            sql = sql.format(company_id=order.company_id.id)
            cr.execute(sql)
            dados = cr.fetchall()
            if len(dados):
                location_id = dados[0][0]

        if not location_id:
            raise osv.except_osv(u'Erro!', u'Não existe um local de estoque padrão para saídas da empresa!')

        print('Local escolhido para o estoque', location_id)

        if not order.partner_id.property_stock_customer:
            raise osv.except_osv(u'Erro!', u'Não existe um local de estoque padrão para o cliente!')

        output_id = order.partner_id.property_stock_customer.id

        res = {
            'name': line.name[:250] if line.name else '',
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'note': line.notes,
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0,
            'orcamento_categoria_id': line.orcamento_categoria_id.id,
        }

        if order.company_id.matriz_id:
            res['company_id'] = order.company_id.matriz_id.id

        return res

    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
        location_id = False

        if order.orcamento_aprovado == 'venda':
            sql = SQL_LOCAL_VENDA
        elif order.orcamento_aprovado == 'locacao':
            sql = SQL_LOCAL_LOCACAO
        else:
            sql = SQL_LOCAL_SAIDA

        sql = sql.format(company_id=order.company_id.id)
        cr.execute(sql)
        print(sql)
        dados = cr.fetchall()
        if len(dados):
            location_id = dados[0][0]
        else:
            sql = SQL_LOCAL_SAIDA
            sql = sql.format(company_id=order.company_id.id)
            cr.execute(sql)
            dados = cr.fetchall()
            if len(dados):
                location_id = dados[0][0]

        if not location_id:
            raise osv.except_osv(u'Erro!', u'Não existe um local de estoque padrão para saídas da empresa!')

        print('Local escolhido para o estoque', location_id)

        if line.name:
            nome = line.name[:250]
        else:
            nome = line.product_id.name[:250]

        res = {
            'name': nome,
            'origin': order.name,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                    or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': location_id,
            'procure_method': line.type,
            'move_id': move_id,
            'company_id': order.company_id.id,
            'note': line.notes,
            'orcamento_categoria_id': line.orcamento_categoria_id.id,
        }

        if order.company_id.matriz_id:
            res['company_id'] = order.company_id.matriz_id.id

        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        original_obj = self.browse(cr, uid, id)

        default.update({
            'state': 'draft',
            'shipped': False,
            'invoice_ids': [],
            'picking_ids': [],
            'date_confirm': False,
            'name': original_obj.versao,
            #'name': self.pool.get('ir.sequence').get(cr, uid, 'sale.order'),
            'orcamento_item_ids': [],
            'orcamento_item_grafico_ids': [],
            #'orcamento_locacao_ids': [],
            'orcamento_locacao_grafico_ids': [],
            #'orcamento_resumo_ids': [],
        })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res

    def ajusta_numero_orcamento(self, cr, uid, ped_id):
        #
        # Quantos orçamentos já existem para esse mesmo pedido?
        #
        pedido_obj = self.browse(cr, uid, ped_id)

        if pedido_obj.versao and pedido_obj.name and pedido_obj.versao != pedido_obj.name:
            return

        try:
            cr.execute("select coalesce(count(*), 0) from sale_order where versao = '" + pedido_obj.name.strip() + "' and company_id = " + str(pedido_obj.company_id.id) + ";")
            total = cr.fetchall()[0][0]
        except:
            total = None

        if total is None or total == 0:
            total = 1

        name = pedido_obj.name + '/' + str(datetime.today().year) + '-' + str(total).zfill(2)
        cr.execute("update sale_order set versao = '" + pedido_obj.name + "', name = '" + name + "' where id = " + str(ped_id) + ";")

    def create(self, cr, uid, dados, context=None):
        res = super(sale_order, self).create(cr, uid, dados, context=context)

        if context is None:
            context = {}

        copia = '__copy_data_seen' in context

        if copia:
            sale_order_id = context['__copy_data_seen']['sale.order'][0]
            #
            # Ajusta os itens vinculados, que ficaram incorretamente com o order_id do pedido anterior,
            # quando duplica o pedido
            #
            cr.execute('''
                begin;
                update sale_order_line ole
                  set order_id = (select ov.order_id from sale_order_line ov where ov.id = ole.order_line_id)
                where id in (
                    select ol.id
                    from sale_order_line ol
                    where ol.order_line_id is not null
                          and ol.order_id not in (
                          select ov.order_id from sale_order_line ov where ov.id = ol.order_line_id)
                    );
                commit work;
            ''')

            #
            # E ajusta o valor total do pedido original, que sabe lá porque foi alterado para mais
            # devido ao vinculo incorretos dos produtos relacionados
            #
            self.pool.get('sale.order.line').calcula_produtos_autocalc(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_resumo_locacao(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_total_orcamento(cr, uid, sale_order_id)

        dados['id'] = res

        self.ajusta_numero_orcamento(cr, uid, res)

        if not copia:
            self.cria_resumo_locacao(cr, uid, res)
            self.carrega_produtos_autoinsert(cr, uid, res)

        return res

    def passou_validade(self, cr, uid, sale_obj, dados):
        pass
        #for item_obj in sale_obj.order_lines:
            #contexto_novo = {
                #'company_id': item_obj.order_id.company_id.id,
                #'partner_id': item_obj.order_id.partner_id.id,
                #'operacao_fiscal_produto_id': item_obj.order_id.operacao_fiscal_produto_id.id,
                #'operacao_fiscal_servico_id': item_obj.order_id.operacao_fiscal_servico_id.id,
                #'orcamento_aprovado': item_obj.order_id.orcamento_aprovado,
                #'quantity': item_obj.product_uom_qty,
                #'pricelist': item_obj.order_id.pricelist_id.id,
                ##'shop': item_obj.order_id.shop_id,
                #'uom': item_obj.product_uom.id,
                #'force_product_uom': True,
            #}

            #impostos = item_pool.product_id_change(cr, uid, [item_obj.id], item_obj.order_id.pricelist_id.id, item_obj.product_id.id, item_obj.product_uom_qty, item_obj.product_uom.id, False, False, item_obj.name, item_obj.order_id.partner_id.id, False, False, item_obj.order_id.date_order, item_obj.product_packaging.id, False, False, contexto_novo)

            #valores = impostos['value']

            #item_pool.write(cr, uid, [item_obj.id], valores, context={'calculo_resumo': True})

        #dados['dt_validade'] = str(parse_datetime(sale_obj.dt_validade).date() + relativedelta(days=+(sale_obj.dias_validade or 7)))

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Tratando a validade da proposta
        #
        for sale_obj in self.browse(cr, uid, ids):
            if sale_obj.dt_validade and sale_obj.dt_validade < str(hoje()):
                self.passou_validade(cr, uid, sale_obj, dados)

        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        for id in ids:
            self.ajusta_numero_orcamento(cr, uid, id)
            self.cria_resumo_locacao(cr, uid, id)
            #self.carrega_produtos_autoinsert(cr, uid, id)

        return res

    def cria_resumo_locacao(self, cr, uid, sale_order_id):
        categoria_pool = self.pool.get('orcamento.categoria')
        locacao_pool = self.pool.get('orcamento.orcamento_locacao')
        ped_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        categoria_ids = categoria_pool.search(cr, uid, [])

        for categoria_id in categoria_ids:
            categoria_obj = categoria_pool.browse(cr, uid, categoria_id)

            if categoria_obj.ordem >= 1000:
                continue

            dados = {
                'sale_order_id': sale_order_id,
                'orcamento_categoria_id': categoria_id,
                'vr_total_custo': 0,
                'vr_total_minimo': 0,
                'vr_total': 0,
                'margem': categoria_obj.margem,
                'desconto': 0,
                'price_subtotal': 0,
                'meses_retorno_investimento': categoria_obj.meses_retorno_investimento,
                'vr_mensal': 0,
                'vr_total_venda_impostos': 0,
            }

            #
            # Criamos o resumo com o super-usuário, para que usuários comuns
            # possam depois alterar mas nunca excluir ou incluir registros manualmente
            #
            if not locacao_pool.search(cr, 1, [('orcamento_categoria_id', '=', categoria_id), ('sale_order_id', '=', sale_order_id)]):
                locacao_pool.create(cr, SUPERUSER_ID, dados)

    def carrega_produtos_autoinsert(self, cr, uid, sale_order_id):
        produto_pool = self.pool.get('product.product')
        item_pool = self.pool.get('sale.order.line')

        produto_ids = produto_pool.search(cr, uid, [('autoinsert', '=', True)])

        for produto_id in produto_ids:
            produto_obj = produto_pool.browse(cr, uid, produto_id)

            dados = {
                'order_id': sale_order_id,
                'product_id': produto_id,
                'name': produto_obj.name,
                'orcamento_categoria_id': produto_obj.orcamento_categoria_id.id,
                'product_uom_qty': 1,
                'vr_unitario_custo': 0,
                'vr_total_custo': 0,
                'vr_unitario_minimo': 0,
                'vr_total_minimo': 0,
                'vr_unitario_venda': 0,
                'vr_total': 0,
                'vr_unitario_margem_desconto': 0,
                'vr_total_margem_desconto': 0,
                'price_unit': 0,
                'usa_unitario_minimo': False,
                'margem': 0,
                'discount': 0,
                'autoinsert': True,
                'vr_comissao': 0,
                'vr_comissao_locacao': 0,
            }

            item_pool.create(cr, uid, dados)

    def imprime_os(self, cr, uid, ids, context={}):

        for ped_obj in self.browse(cr, uid, ids):
            titulo = u'Ordem de Serviço nº '
            titulo += ped_obj.name
            titulo += u' - '
            titulo += parse_datetime(ped_obj.date_order).strftime(u'%d/%m/%Y')

            rel = Report(titulo, cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'os.jrxml')
            rel.parametros['ORDER_ID'] = ped_obj.id

            rel.parametros['INTEGRA_REPORT_TITLE'] = titulo
            rel.parametros['COMPANY_ID'] = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')
            pdf, formato = rel.execute()

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', ped_obj.id), ('name', '=', 'os.pdf')])
            #
            # Apaga os boletos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': 'os.pdf',
                'datas_fname': 'os.pdf',
                'res_model': 'sale.order',
                'res_id': ped_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

    def recalcula(self, cr, uid, ids, context={}):
        for order_obj in self.pool.get('sale.order').browse(cr, uid, ids):
            for locacao_obj in order_obj.orcamento_locacao_ids:
                locacao_obj.write({'recalculo': int(random.random() * 100000000)})

        return {'value': {}, 'message': u'Recalculado!'}

    def remove_automatico_itens(self, cr, uid, ids, context={}):
        if isinstance(ids, int):
            ids = [ids]

        for orc_id in ids:
            cr.execute('update sale_order_line set order_line_id = null, autoinsert = False where order_id = %d' % orc_id)
            cr.execute('update sale_order set desvincula_itens = True where  id = %d' % orc_id)

        return {'value': {}, 'message': u'Itens desvinculados!'}

    # if mode == 'finished':
    #   returns True if all lines are done, False otherwise
    # if mode == 'canceled':
    #   returns True if there is at least one canceled line, False otherwise
    def test_state(self, cr, uid, ids, mode, *args):
        assert mode in ('finished', 'canceled'), _("invalid mode for test_state")
        finished = True
        canceled = False
        notcanceled = False
        write_done_ids = []
        write_cancel_ids = []
        for order in self.browse(cr, uid, ids, context={}):
            for line in order.order_line:
                if (not line.procurement_id) or (line.procurement_id.state=='done'):
                    if line.state != 'done':
                        write_done_ids.append(line.id)
                else:
                    finished = False
                if line.procurement_id:
                    if (line.procurement_id.state == 'cancel'):
                        canceled = True
                        if line.state != 'exception':
                            write_cancel_ids.append(line.id)
                    else:
                        notcanceled = True
        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'}, context={'calculo_resumo': True})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'exception'}, context={'calculo_resumo': True})

        if mode == 'finished':
            return finished
        elif mode == 'canceled':
            return canceled
            if notcanceled:
                return False
            return canceled

    def _prepare_order_picking(self, cr, uid, order_obj, context={}):
        dados = super(sale_order, self)._prepare_order_picking(cr, uid, order_obj, context=context)
        dados['partner_id'] = order_obj.partner_id.id

        if order_obj.company_id.matriz_id:
            dados['company_id'] = order_obj.company_id.matriz_id.id

        return dados

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sale order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sale order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in order_lines:
            if line.state == 'done':
                continue

            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.product_tmpl_id.type != 'product':
                    continue

                #if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                if line.product_id.product_tmpl_id.type in ('product',):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    # a service has no stock move
                    move_id = False

                proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id}, context={'calculo_resumo': True})
                self.ship_recreate(cr, uid, order, line, move_id, proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val, context={'calculo_resumo': True})
        return True

    def action_ship_end(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            val = {'shipped': True}
            if order.state == 'shipping_except':
                val['state'] = 'progress'
                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
            for line in order.order_line:
                towrite = []
                if line.state == 'exception':
                    towrite.append(line.id)
                if towrite:
                    self.pool.get('sale.order.line').write(cr, uid, towrite, {'state': 'done'}, context=context)
            self.write(cr, uid, [order.id], val, context={'calculo_resumo': True})
        return True

    #def action_wait(self, cr, uid, ids, context=None):
        ##
        ## Antes de confirmar a liberação do pedido, verificamos as validações de permissão
        ## da locação e venda
        ##
        #self.valida_aprovacao_locacao(cr, uid, ids, context=context)
        #self.valida_aprovacao_venda(cr, uid, ids, context=context)

        #for o in self.browse(cr, uid, ids):
            #if not o.order_line:
                #raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which has no line.'))
            #if (o.order_policy == 'manual'):
                #self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            #else:
                #self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            #self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
            #message = _("The quotation '%s' has been converted to a sales order.") % (o.name,)
            #self.log(cr, uid, o.id, message)
        #return True


sale_order()
