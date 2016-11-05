# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields



class sped_operacao(osv.Model):
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'valida_numero_serie': fields.boolean(u'Valida produtos com nº de série?'),
        'marca_inicio_garantia': fields.boolean(u'Marca início da garantia?'),
    }

    _default = {
        'valida_numero_serie': False,
        'marca_inicio_garantia': False,
    }


sped_operacao()
