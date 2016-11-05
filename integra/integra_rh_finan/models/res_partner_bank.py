# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class res_partner_bank(orm.Model):
    _name = 'res.partner.bank'
    _inherit = 'res.partner.bank'

    _columns = {
        'codigo_convenio': fields.char(u'Código do convênio no banco', size=10),
    }


res_partner_bank()
