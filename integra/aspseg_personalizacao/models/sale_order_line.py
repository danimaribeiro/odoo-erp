# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    def get_qtd_estoque(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        produto_custo_pool = self.pool.get('product.custo')
        item_compra_pool = self.pool.get('purchase.order.line')

        for item_obj in self.browse(cr, uid, ids):
            qtd = D(0)

            if item_obj.product_id:
                if nome_campo == 'qtd_ambulante':
                    unit, qtd, total = produto_custo_pool.busca_custo(cr, uid, 7, 20, item_obj.product_id.id)
                else:
                    sql = """
                    select sum(coalesce(product_qty, 0.00)) as quantidade_comprada
                    from purchase_order_line ioc
                    join purchase_order oc on oc.id = ioc.order_id
                    where
                        ioc.product_id = {produto_id}
                        and oc.state = 'approved';
                    """

                    cr.execute(sql.format(produto_id=item_obj.product_id.id))
                    dados = cr.fetchall()
                    qtd = dados[0][0] or 0.00

            res[item_obj.id] = qtd

        return res

    _columns = {
        'virtual_available': fields.related('product_id', 'virtual_available', string=u'Qtd. disponível'),
        'qtd_ambulante': fields.function(get_qtd_estoque, type='float', method=True, string=u'Qtde. Amb.'),
        'qtd_comprada': fields.function(get_qtd_estoque, type='float', method=True, string=u'Qtde. Comprada'),
        ##'qtd_estoque': fields.function(get_qtd_estoque, type='float', method=True, string=u'Qtde. Est.'),
        'motivo_cancelamento_id': fields.many2one('sale.motivocancelamento', u'Motivo do Cancelamento', select=True),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        resposta = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context)

        if not product_id:
            return resposta

        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)

        produto_custo_pool = self.pool.get('product.custo')

        dados = resposta['value']

        dados.update({
            #'product_uom_qty': product_obj.qty_available,
            'virtual_available': product_obj.virtual_available,
        })

        #
        # Busca as quantidades no estoque da ASP
        #

        #
        # Ambulante ASPSEG Comercio
        #
        unit, qtd, total = produto_custo_pool.busca_custo(cr, uid, 7, 20, product_id)
        dados['qtd_ambulante'] = qtd or 0

        sql = """
        select sum(coalesce(product_qty, 0.00)) as quantidade_comprada
        from purchase_order_line ioc
        join purchase_order oc on oc.id = ioc.order_id
        where
            ioc.product_id = {produto_id}
            and oc.state = 'approved';
        """

        cr.execute(sql.format(produto_id=product_id))
        dados_comprados = cr.fetchall()
        try:
            qtd = dados_comprados[0][0]
            dados['qtd_comprada'] = qtd or 0
        except:
            dados['qtd_comprada'] = 0

        #dados['vr_unitario_venda_impostos'] = dados['price_unit'] or 0
        #dados['vr_total_venda_impostos'] = dados['price_unit'] or 0

        return resposta

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            #if line.invoiced:
                #raise osv.except_osv(_('Invalid action !'), _('You cannot cancel a sale order line that has already been invoiced!'))

            for move_line in line.move_ids:
                if move_line.sped_documentoitem_id or (move_line.picking_id and move_line.picking_id.sped_documento_id):
                    raise osv.except_osv(u'Erro!', u'Você não pode cancelar pois já há notas faturadas para esse item/pedido!')
                #if move_line.state != 'cancel':
                    #raise osv.except_osv(
                            #_('Could not cancel sales order line!'),
                            #_('You must first cancel stock moves attached to this sales order line.'))

        pickings = []
        for line in self.browse(cr, uid, ids, context=context):
            for move_line in line.move_ids:
                if move_line.picking_id and move_line.picking_id.id not in pickings:
                    pickings += [move_line.picking_id.id]

        for pid in pickings:
            cr.execute("update stock_move set state='cancel' where picking_id = " + str(pid) + ";")
            cr.execute("update stock_picking set state='cancel' where id = " + str(pid) + ";")

        self.pool.get('stock.picking').unlink(cr, 1, pickings)

        return self.write(cr, uid, ids, {'state': 'cancel'})


sale_order_line()
