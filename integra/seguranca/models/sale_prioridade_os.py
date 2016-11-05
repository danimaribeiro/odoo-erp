# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class sale_prioridade_os(osv.Model):
    _description = u'Prioridade da OS'
    _name = 'sale.prioridade.os'
    _rec_name = 'nome'
    _order = 'dias'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            res[os_obj.id] = str(os_obj.id).zfill(4)

        return res


    _columns = {
        'codigo': fields.function(_codigo, type='char', method=True, string=u'Código', size=20, store=False, select=True),
        'nome': fields.char(u'Nome', size=180),
        'dias': fields.integer(u'Dias'),
    }


sale_prioridade_os()
