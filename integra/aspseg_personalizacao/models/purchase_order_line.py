# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class purchase_order_line(osv.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'


    _columns = {
      
    }



purchase_order_line()
