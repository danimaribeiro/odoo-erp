# -*- encoding: utf-8 -*-

from osv import osv, fields
import base64
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class stock_move(osv.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'familiatributaria_ids': fields.many2many('sped.familiatributaria', 'stock_operacao_familiatributaria', 'move_id', 'familiatributaria_id', u'Famílias tributárias'),
    }


stock_move()