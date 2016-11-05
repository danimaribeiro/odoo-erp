# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_20(orm.Model):
    _name = 'esocial.tabela_20'
    _description = u'Tabela de Tipos de Logradouros'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
    }


