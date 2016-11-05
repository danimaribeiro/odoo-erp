# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class Estado(orm.Model):
    #_inherit = 'res.country.state'
    _description = 'Estados do Brasil'
    _name = 'sped.estado'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            retorno[registro.id] = registro.uf + ' - ' + registro.nome

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|', # Isto define o OR para os dois parâmetros seguintes
            ('uf', '=', texto.upper()),
            ('nome', 'ilike', texto),
            ]
        return procura

    _columns = {
        'uf': fields.char('UF', size=2, required=True, select=True),
        'nome': fields.char('Nome', size=20, required=True, select=True),
        'codigo_ibge': fields.char(u'Código IBGE', size=2),
        'res_country_state_id': fields.many2one('res.country.state', 'Estado OpenERP'),
        'descricao': fields.function(_descricao, method=True, type='char', fnct_search=_procura_descricao),
        'fuso_horario': fields.char(u'Fuso horário', size=20),
        }

    _rec_name = 'descricao'
    _order = 'uf'

    _sql_constraints = [
        ('uf_unique', 'unique (uf)',
        u'A UF não pode se repetir!'),
        ('nome_unique', 'unique (nome)',
        u'O nome não pode se repetir!'),
        ]

Estado()
