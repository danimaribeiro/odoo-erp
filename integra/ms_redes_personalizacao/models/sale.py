# -*- encoding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class sale_order(osv.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    _columns = {
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento'),
    }

    _defaults = {
        'dias_validade': 10000,
    }


sale_order()



class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    _columns = {
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do Orçamento'),
        'risco': fields.float(u'Margem', digits=(18,2)),
    }

    def onchange_preco_base_risco(self, cr, uid, ids, vr_unitario_base, risco, quantidade, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        vr_unitario_base = D(vr_unitario_base or 1)
        risco = D(risco or 0)
        quantidade = D(quantidade or 0)

        valores['vr_produto_base'] = vr_unitario_base * quantidade
        valores['vr_produto_base_readonly'] = vr_unitario_base * quantidade

        valores['price_unit'] = vr_unitario_base * (1 + (risco / 100))

        return res

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        vr_unitario_base = D(context.get('vr_unitario_base', 1) or 1)

        if 'price_unit' in context:
            price_unit = D(context['price_unit'] or 0)
            risco = ((price_unit / vr_unitario_base) - 1) * 100
            res['value']['risco'] = risco

        elif 'price_unit' in res['value']:
            price_unit = D(res['value']['price_unit'] or 0)
            risco = ((price_unit / vr_unitario_base) - 1) * 100
            res['value']['risco'] = risco

        return res


sale_order_line()

