# -*- encoding: utf-8 -*-

from osv import osv, fields


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'usa_numero_serie': fields.boolean(u'Usa nº de série?'),
        'numero_serie_ids': fields.one2many('product.numero.serie', 'product_id', string=u'Números de série'),
    }

    _defauls = {
        'usa_numero_serie': False,
    }


product_product()