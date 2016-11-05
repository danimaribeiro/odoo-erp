# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields

class finan_conta(osv.Model):
    _inherit = 'finan.conta'
    
    
    def _get_numero_codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}        
        
        for conta_obj in self.browse(cr, uid, ids):        
            if conta_obj.codigo == 0:
                res[conta_obj.id] = conta_obj.id
                
        return res
    
    _columns = {                                     
        'codigo': fields.function(_get_numero_codigo, type='integer',  method=True, string=u'Conta reduzida', store=True, select=True),           
    }
    
    _defaults = {
    }

finan_conta()
