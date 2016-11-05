# -*- encoding: utf-8 -*-


from decimal import Decimal as D
from osv import osv, fields


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _parent_order = 'sequence, codigo_completo'
    _order = 'order_id, sequence, codigo_completo'

    def _amount_line(self, cr, uid, ids, field_name, arg, context={}):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')

        res = {}

        for line in self.browse(cr, uid, ids, context=context):
            price = (line.price_unit or 0) * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            
        return res

    _columns = {
        'price_unit': fields.float('Unit Price', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal'),
    }
    

sale_order_line()
