# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_07(orm.Model):
    _name = 'esocial.tabela_07'
    _description = u'Riscos Ocupacionais Específicos'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código Tipo de Risco', required=True, select=True),
        'descricao': fields.text(u'Agentes Nocivos',size=250, required=True),
    }


