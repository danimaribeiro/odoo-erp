# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_12(orm.Model):
    _name = 'esocial.tabela_12'
    _description = u'Tipos de Contribuição'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
    }


