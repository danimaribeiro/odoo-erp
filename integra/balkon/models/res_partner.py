# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D


class res_partner(orm.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'eh_condomino': fields.boolean('É condômino'),
    }


res_partner()
