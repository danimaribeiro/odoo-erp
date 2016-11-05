# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields


class finan_documento(orm.Model):
    _name = 'finan.documento'
    _inherit = 'finan.documento'

    _columns = {
        'provisionado': fields.boolean(u'Provisiona lançamento no pedido de compra?'),
    }
    
    _defaults = {
        'provisionado': True,
    }


finan_documento()
