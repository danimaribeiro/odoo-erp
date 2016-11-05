# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D



class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'


    _columns = {
        'quantidade_pontos': fields.integer(u'Quantidade de pontos'),
        'calcula_pontos_venda': fields.boolean(u'Calcula pontos?'),
    }


product_product()
