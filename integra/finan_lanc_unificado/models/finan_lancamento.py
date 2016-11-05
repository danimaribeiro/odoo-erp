# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from time import time
from mako.template import Template
from copy import copy
from pybrasil.valor.decimal import Decimal as D



class finan_lancamento(osv.Model):
    _description = u'Lançamentos'
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'unificado_id': fields.many2one('finan.lanc.unificado', u'Unificado/Renegociado', ondelete='restrict'),
    }


finan_lancamento()
