# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_tipo(osv.Model):
    _name = 'frota.tipo'
    _description = 'Tipos de veículo'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Tipo', size=30),
    }


frota_tipo()
