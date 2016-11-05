# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class ordem_servico(osv.Model):
    _name = 'ordem.servico'
    _inherit = 'ordem.servico'
    
    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            res[os_obj.id] = os_obj.id + 34169  # início da numeração da ASP

        return res
    
    _columns = {                
        'numero': fields.function(_codigo, type='integer', method=True, string=u'Nº OS', store=True, select=True),
    }


ordem_servico()
