# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from openerp import SUPERUSER_ID
#from product import product
import re


class product_category(orm.Model):
    _name = 'product.category'
    _inherit = 'product.category'

    _columns = {
        'percentual_acessorios': fields.float(u'Markup de acessórios'),
    }


product_category()
