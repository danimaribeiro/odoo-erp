# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


class finan_conta(orm.Model):
    _description = 'Conta Financeira'
    _name = 'finan.conta'
    _inherit = 'finan.conta'

    _columns = {
        'exige_contrato': fields.boolean('Exige contrato no rateio?'),
    }

    _defaults = {
        'exige_contrato': False,
    }


finan_conta()
