# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    _columns = {
        'ref': fields.char('Código', size=6, select=1),
    }


res_partner()
