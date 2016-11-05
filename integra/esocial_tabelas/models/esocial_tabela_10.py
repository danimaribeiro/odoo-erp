# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_10(orm.Model):
    _name = 'esocial.tabela_10'
    _description = u'Tipos de Lotacao'

    _order = 'codigo'
    _rec_name = 'codigo'
    _columns = {
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição',size=250, required=True),
        'nroInscEstab': fields.char(u'Preenchimento do Campo', size=30, required=True, select=True),
    }


