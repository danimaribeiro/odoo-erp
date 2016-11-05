# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_03(orm.Model):
    _name = 'esocial.tabela_03'
    _description = u'Rubricas da Folha de Pagamento'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Nome da Rubrica', size=40, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Descrição da Rubrica',size=250, required=True),
    }


