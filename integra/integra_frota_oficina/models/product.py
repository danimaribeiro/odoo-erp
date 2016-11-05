# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class product_product(osv.Model):
    _inherit = 'product.product'

    _columns = {
        'frota_modelo_ids': fields.many2many('frota.modelo', 'frota_modelo_produto', 'product_id', 'modelo_id', u'Marcas/modelos'),
        'qualquer_marca_modelo': fields.boolean(u'Para qualquer marca/modelo?'),
    }

    _defauls = {
        'qualquer_marca_modelo': True,
    }


product_product()
