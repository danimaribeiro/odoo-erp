# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'codigo_sindical': fields.char(u'Código sindical', size=30),
        'codigo_ans': fields.char(u'Código ANS', size=6),        
    }

res_partner()
