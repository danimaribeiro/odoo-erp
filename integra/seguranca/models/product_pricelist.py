# -*- coding: utf-8 -*-

from osv import fields, osv


class product_pricelist(osv.Model):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    _columns = {
        'name': fields.char(u'Nome da lista de preços',size=64, required=True, translate=False),
        'meses_retorno_locacao': fields.integer(u'Meses para retorno'),
        'tipo_os_id': fields.many2one('sale.tipo.os', u'Tipo da OS'),
        'contrato_terceirizado': fields.boolean(u'Gera contrato terceirizado?'),
    }

    _defaults = {
        'meses_retorno_locacao': 0,
    }


product_pricelist()
