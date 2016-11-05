# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class sale_order_line_referencia(osv.Model):
    _name = 'sale.order.line.referencia'
    _description = u'Itens do orçamento de referência'

    _columns = {
        'order_id': fields.many2one('sale.order.referencia', u'Orçamento', ondelete='cascade'),
        'tipo_item': fields.selection((('P', u'Produto'), ('S', u'Serviço'), ('M', u'Mensalidade')), u'Tipo'),
        'product_id': fields.many2one('product.product', u'Produto', ondelete='restrict'),
        'quantidade': fields.float(u'Quantidade', digits=(18, 4)),
    }

    _defaults = {
        'quantidade': 1,
    }

sale_order_line_referencia()
