# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_tipo_faturamento(osv.Model):
    _description = u'Tipos de Faturamento de Contrato'
    _name = 'finan.tipo.faturamento'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Tipo', size=60, required=True),
    }

    _sql_constraints = [
        ('nome_unique', 'unique(nome)',
            u'O tipo não pode se repetir!'),
    ]



finan_tipo_faturamento()
