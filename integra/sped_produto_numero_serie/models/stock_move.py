# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class stock_move(osv.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'product_id': fields.many2one('product.product', u'Produto', ondelete='cascade'),
        'numero_serie': fields.char(u'Número de série', size=64, select=True),
        'stock_move_ids': fields.many2many('stock.move', 'stock_move_numero_serie', 'numero_serie_id', 'move_id', u'Movimentação de estoque'),
        'sped_documentoitem_ids': fields.many2many('sped.documentoitem', 'sped_documentoitem_numero_serie', 'numero_serie_id', 'item_id', u'Itens de notas fiscais'),
    }

    _sql_constraints = [
        ('product_numero_serie_unique', 'unique (product_id, numero_serie)', u'O número de série não pode se repetir para esse produto!'),
    ]
