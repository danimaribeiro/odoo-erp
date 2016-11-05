# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields

CAMPOS_LIBERADOS = [
    'contabilizacao_ids',

                      
] 

class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lote'),
    }
    
    def write(self, cr, uid, ids, dados, context={}):
        
        for documento_obj in self.browse(cr, uid, ids):
            print(dados)
            
            libera_alteracao = True
            for campo in dados:
                if campo not in CAMPOS_LIBERADOS:
                    libera_alteracao = False
                    break
            
            if documento_obj.lote_id and not libera_alteracao:
                raise osv.except_osv(u'Inválido !', u'NF ja importado para contabildade! Lote: ' + str(documento_obj.lote_id.codigo)) 

        res = super(sped_documento, self).write(cr, uid, ids, dados, context)
        
        return res
    
    def unlink(self, cr, uid, ids, context={}):
        
        for documento_obj in self.browse(cr, uid, ids):
            if documento_obj.lote_id:
                raise osv.except_osv(u'Inválido !', u'NF ja importado para contabildade! Lote: ' + str(documento_obj.lote_id.codigo)) 

        res = super(sped_documento, self).unlink(cr, uid, ids, context)
        
        return res

sped_documento()
