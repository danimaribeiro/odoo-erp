# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class product_product(orm.Model):
    _inherit = "product.product"
    _description = "Product"

    _columns = {
        'acessorio_ids': fields.one2many('product.acessorio', 'product_id', u'Acessórios'),
        'acessorio_selecao_ids': fields.many2many('product.product', 'product_acessorio', 'product_id', 'acessorio_id', u'Acessórios'),

        'acessorio_obrigatorio_ids': fields.one2many('product.acessorio.obrigatorio', 'product_id', u'Acessórios obrigatórios'),
        'acessorio_obrigatorio_selecao_ids': fields.many2many('product.product', 'product_acessorio_obrigatorio', 'product_id', 'acessorio_id', u'Acessórios obrigatórios'),
    }


product_product()
