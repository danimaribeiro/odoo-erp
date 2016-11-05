# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje


class sale_agrupamento(osv.Model):
    _description = u'Agrupamento na OS'
    _name = 'sale.agrupamento'
    _rec_name = 'nome'
    _order = 'ordem, nome'

    _columns = {
        'ordem': fields.integer(u'Ordem', required=True, select=True),
        'nome': fields.char(u'Nome', size=60),
    }


sale_agrupamento()
