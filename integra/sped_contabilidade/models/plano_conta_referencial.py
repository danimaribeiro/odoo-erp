# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv

TIPO_CONTA = [
      ['S', u'Sintética'],
      ['A', u'Análitica'],
]


class Plano_Conta_Referencial(orm.Model):
    _name = 'plano.conta.referencial'
    _description = u'Plano de Contas Referencial'
    _order = 'codigo_pai, codigo'
    _rec_name = 'codigo'

    _columns = {
        'codigo': fields.char(u'Codigo', size=60 ),
        'nome': fields.char(u'Nome', size=240 ),
        'data_inicial': fields.char(u'Inicio', size=8 ),
        'data_final': fields.char(u'Fim', size=8 ),
        'tipo': fields.selection(TIPO_CONTA, u'Natuza'),
        'codigo_pai': fields.char(u'Conta Pai', size=60),
        
    }

    _defaults = {
       
    }

   
Plano_Conta_Referencial()

