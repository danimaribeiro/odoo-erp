# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class Rota(orm.Model):
    _description = u'Rota'
    _name = 'partner.rota'

    _columns = {
        'codigo': fields.char('Código', size=7, required=True),
        'descricao': fields.char('Descrição', size=255, required=True),
        }

    _rec_name = 'codigo'
    _order = 'codigo'

    _sql_constraints = [
        ('codigo_unique', 'unique (codigo)',
        u'O código não pode se repetir!'),
        ('descricao_unique', 'unique (descricao)',
        u'A descrição não pode se repetir!'),
        ]

Rota()
