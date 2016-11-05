# -*- coding: utf-8 -*-

from osv import orm, fields, osv


class esocial_tabela_06(orm.Model):
    _name = 'esocial.tabela_06'
    _description = u'Clas. de Serv. Suj. a Retenção de Contrib. Previdenciária'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        #'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'codigo': fields.integer(u'Código', required=True, select=True),
        'descricao': fields.text(u'Tipo de Serviço',size=250, required=True),
    }


