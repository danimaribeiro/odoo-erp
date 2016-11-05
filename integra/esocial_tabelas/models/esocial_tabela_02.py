# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_02(orm.Model):
    _name = 'esocial.tabela_02'
    _description = u'Grau de Exposição a Agentes Noscivos'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'grupo': fields.char(u'Grupo', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
    }


