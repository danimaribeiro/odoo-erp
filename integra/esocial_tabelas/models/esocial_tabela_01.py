# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_01(orm.Model):
    _name = 'esocial.tabela_01'
    _description = u'Categorias de Trabalhadores'
    _order = 'grupo'
    _rec_name = 'grupo'

    _columns = {
        'grupo': fields.char(u'Grupo', size=40, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
    }


