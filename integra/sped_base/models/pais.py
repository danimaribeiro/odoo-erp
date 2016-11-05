# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class Pais(orm.Model):
    _description = u'Pais'
    _name = 'sped.pais'
    _columns = {
        'codigo_bacen': fields.char(u'Codigo BANCO CENTRAL', size=4, required=True),
        'codigo_siscomex': fields.char(u'Codigo SISCOMEX', size=3),
        'nome': fields.char('Nome', size=60, required=True),
        'res_country_id': fields.many2one('res.country', u'Pais OpenERP'),
        }

    _rec_name = 'nome'
    _order = 'nome'

    _sql_constraints = [
        ('codigo_bacen_unique', 'unique (codigo_bacen)',
        u'O código BACEN não pode se repetir!'),
        ]

Pais()
