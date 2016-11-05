# -*- encoding: utf-8 -*-

from osv import osv, fields


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    _columns = {
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo'),
        'modelo_id': fields.related('veiculo_id', 'modelo_id', type='many2one', relation='frota.modelo', string=u'Marca/modelo', store=True),
        'product_ids': fields.related('modelo_id', 'product_ids', type='many2many', obj='product.product')
    }


sale_order()


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    _columns = {
        'veiculo_id': fields.related('order_id', 'veiculo_id', type='many2one', relation='frota.veiculo', string=u'Veículo', store=True),
        'modelo_id': fields.related('order_id', 'modelo_id', type='many2one', relation='frota.modelo', string=u'Marca/modelo', store=True),
        'product_ids': fields.related('modelo_id', 'product_ids', type='many2many', obj='product.product')
    }


sale_order_line()
