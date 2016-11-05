# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D


class sale_order(orm.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    _columns = {
        'hr_department_id': fields.many2one('hr.department', u'NAL'),
    }


sale_order()
