# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_15(orm.Model):
    _name = 'esocial.tabela_15'
    _description = u'Agente Causador / Sit. Ger. Doença Prof.'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
    }


