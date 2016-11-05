# -*- coding: utf-8 -*-


from osv import osv, fields


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _get_sale_order_line_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        item_pool = self.pool.get('sale.order.line')

        for id in ids:
            item_ids = item_pool.search(cr, uid, [('order_id.partner_id.id', '=', id)])
            res[id] = item_ids or []

        return res

    _columns = {
        #'comissao_venda_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para venda'),
        #'comissao_locacao_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para locação'),
        'sale_order_line_ids': fields.function(_get_sale_order_line_ids, string=u'Itens comprados', method=True, type='one2many', relation='sale.order.line', store=False),
    }


res_partner()
