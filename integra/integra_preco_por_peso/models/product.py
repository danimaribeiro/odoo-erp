# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from decimal import Decimal as D


class product_product(osv.Model):
    _inherit = 'product.product'

    _columns = {
        'preco_venda_por_peso': fields.float(u'Preço de venda por peso'),
        'preco_custo_por_peso': fields.float(u'Preço de custo por peso'),
        'preco_por_parcela': fields.float(u'Valor por parcela'),
        'parcelas': fields.float(u'Nº de parcelas'),
        #'preco_minimo_por_peso': fields.float(u'Preço mínimo por peso'),
    }

    _defaults = {
        'parcelas': 10,
    }

    def onchange_weight_net(self, cr, uid, ids, weight_net, preco_venda_por_peso, preco_custo_por_peso):

        list_price = D(str(weight_net)) * D(str(preco_venda_por_peso))
        list_price = list_price.quantize(D('0.01'))

        standard_price = D(str(weight_net)) * D(str(preco_custo_por_peso))
        standard_price = standard_price.quantize(D('0.01'))

        print('list_price', list_price, 'standard_price', standard_price)

        return {'value': {'list_price': list_price, 'standard_price': standard_price}}

    def onchange_preco_venda_por_peso(self, cr, uid, ids, weight_net, preco_venda_por_peso):

        list_price = D(str(weight_net)) * D(str(preco_venda_por_peso))
        list_price = list_price.quantize(D('0.01'))

        print('list_price', list_price)

        return {'value': {'list_price': list_price}}

    def onchange_preco_custo_por_peso(self, cr, uid, ids, weight_net, preco_custo_por_peso):

        standard_price = D(str(weight_net)) * D(str(preco_custo_por_peso))
        standard_price = standard_price.quantize(D('0.01'))

        return {'value': {'standard_price': standard_price}}

    def onchange_preco_minimo_por_peso(self, cr, uid, ids, weight_net, preco_minimo_por_peso):

        preco_minimo = D(str(weight_net)) * D(str(preco_minimo_por_peso))
        preco_minimo = preco_minimo.quantize(D('0.01'))

        return {'preco_minimo': preco_minimo}

    def onchange_preco_por_parcela_parcelas(self, cr, uid, ids, preco_por_parcela, parcelas):

        list_price = D(str(preco_por_parcela)) * D(str(parcelas))
        list_price = list_price.quantize(D('0.01'))

        return {'value': {'list_price': list_price}}


product_product()
