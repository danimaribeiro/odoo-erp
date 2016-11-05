# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv



class stock_move(orm.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'sale_order_id': fields.many2one('sale.order', type='many2one', string=u'Proposta/OS', ondelete='restrict'),
        'tipo_os_id': fields.many2one('sale.tipo.os', u'Tipo da OS'),
        'eh_saida': fields.boolean(u'É saída?'),
    }

    def create(self, cr, uid, dados, context={}):
        if 'name' not in dados and 'sale_order_id' in dados:
            sale_obj = self.pool.get('sale.order').browse(cr, uid, dados['sale_order_id'])
            produto_obj = self.pool.get('product.product').browse(cr, uid, dados['product_id'])
            dados['name'] = sale_obj.name + '; ' + produto_obj.name

        return super(stock_move, self).create(cr, uid, dados, context=context)


stock_move()
