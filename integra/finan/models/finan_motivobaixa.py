# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import fields, osv


class finan_motivobaixa(osv.Model):
    _name = 'finan.motivobaixa'
    _description = 'Motivos para baixa'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Motivo para baixa', size=60, required=True, select=True),
    }


finan_motivobaixa()
