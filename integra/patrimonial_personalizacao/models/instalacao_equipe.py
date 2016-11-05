# -*- encoding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class instalacao_equipe(osv.Model):
    _name = 'instalacao.equipe'
    _rec_name = 'codigo'
    _order = 'codigo'
    

    _columns = {
        'codigo': fields.char(u'Código', size=20, select=True),
        'partner_id': fields.many2one('res.partner', u'Fornecedor'),
    }


instalacao_equipe()
