# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class sale_taxa_administrativa(orm.Model):
    _description = u'Taxa administrativa'
    _name = 'sale.taxa_administrativa'
    _order = 'valor'
    _rec_name = 'valor'

    _columns = {
        'valor': fields.float(u'Valor'),
        'taxa': fields.float(u'Taxa'),
        }


sale_taxa_administrativa()
