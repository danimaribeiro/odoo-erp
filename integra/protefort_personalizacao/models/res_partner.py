# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'email_nfe': fields.char(u'Email para envio da NF-e', size=256),
    }


res_partner()
