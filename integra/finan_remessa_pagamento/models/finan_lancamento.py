# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from pybrasil.febraban.banco import BANCO_CODIGO, Remessa
from pybrasil.febraban.pessoa import Beneficiario


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

linha digitável
23790.34305 90000.010000 20014.644908 3 65950000017381 

código de barras
23793659500000173810343090000010002001464490


    _columns = {
        'codigo_barras': fields.char(u'Código de barras', size=44),
        'linha_digitavel': fields.char(u'Linha digitável', size=44),
    }



finan_remessa_pagamento()
