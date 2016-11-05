# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor import formata_valor
from pybrasil.valor.decimal import Decimal as D
from sped_modelo_partida_dobrada import PartidaDobrada


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
        'modelo_partida_dobrada_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas'),
    }


finan_contrato()
