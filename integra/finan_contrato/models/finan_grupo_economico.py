# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_grupo_economico(osv.Model):
    _description = u'Grupos econômicos'
    _name = 'finan.grupo.economico'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Descrição', size=60, required=True),
        'vendedor_id': fields.many2one('res.users', u'Vendedor'),
    }

    _sql_constraints = [
        ('nome_unique', 'unique(nome)',
            u'O grupo econômico não pode se repetir!'),
    ]


finan_grupo_economico()
