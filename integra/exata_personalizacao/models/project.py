# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64


PROJETO_TIPO = [
    ('P', u'Próprio'),
    ('T', u'Terceiro'),
    ('S', u'Sócio'),
    ('SO',u'Sociedade'),
]


class project(osv.Model):
    _name = "project.project"
    _inherit = 'project.project'

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária'),
        'tipo': fields.selection(PROJETO_TIPO, u'Classificação'),
    }


project()
