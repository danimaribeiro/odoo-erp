# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_motivo_distrato(osv.Model):
    _description = u'Motivos de Distrato'
    _name = 'finan.motivo_distrato'

    _columns = {
        'nome': fields.char(u'Descrição', size=60, required=True),
    }

    _sql_constraints = [
        ('nome_unique', 'unique(nome)',
            u'A descrição não pode se repetir!'),
    ]

    _rec_name = 'nome'
    _order = 'nome'


finan_motivo_distrato()
