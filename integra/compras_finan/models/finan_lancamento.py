# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class finan_lancamento(osv.Model):
    _inherit = 'finan.lancamento'

    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', u'Pedido de compra'),
    }


finan_lancamento()
