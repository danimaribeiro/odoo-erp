# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class Veiculo(orm.Model):
    #_inherit = 'res.partner'
    _description = u'Veículos'
    _name = 'sped.veiculo'

    _columns = {
        #
        # Chave primária natural
        #
        'placa': fields.char(u'Placa', size=8, required=True),
        'estado_id': fields.many2one('sped.estado', u'Estado', required=True),
        'rntrc': fields.char(u'RNTRC', size=20),
        'transportadora_id': fields.many2one('sped.participante', u'Transportadora'),
        'motorista_id': fields.many2one('sped.participante', u'Motorista'),
        }

    _sql_constraints = [
        ('placa_unique', 'unique (placa)',
        u'A placa não pode se repetir!'),
        ]

    _defaults = {
        'rntrc': '',
        }

    _rec_name = 'placa'
    _order = 'placa'

Veiculo()