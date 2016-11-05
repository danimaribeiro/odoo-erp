# -*- coding: utf-8 -*-

from osv import osv, fields


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'sale_order_id': fields.many2one('sale.order', u'Pedido'),
        'comissao_revenda_id': fields.many2one('finan.lancamento', u'Comissão revenda'),
    }


finan_lancamento()
