# -*- encoding: utf-8 -*-

from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    _columns = {
        'margem_fixa': fields.float(u'Margem (%)', digits=(18,10)),
        'preco_fixo': fields.float(u'Preço fixo'),
    }

    def onchange_preco_fixo(self, cr, uid, ids, preco_fixo, price_unit, proporcao_imposto):
        if not price_unit or not proporcao_imposto:
            return

        res = {}
        valor = {}
        res['value'] = valor

        margem_fixa = D(preco_fixo) * D(proporcao_imposto) / D(100)
        margem_fixa /= price_unit
        margem_fixa -= D(1)
        margem_fixa *= D(100)
        margem_fixa = margem_fixa.quantize(D('0.0000000001'))

        if margem_fixa < 0:
            margem_fixa = 0

        valor['margem_fixa'] = margem_fixa

        return res


sale_order_line()
