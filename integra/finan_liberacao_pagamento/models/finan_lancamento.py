# -*- coding: utf-8 -*-

from osv import fields, osv


class finan_lancamento(osv.osv):
    _inherit = 'finan.lancamento'

    _columns = {
        'pagamento_bloqueado': fields.boolean(u'Pagamento bloqueado?'),
        'aprovador_id': fields.many2one('res.users', u'Aprovado por'),
    }
    
    _defaults = {
        'pagamento_bloqueado': False,
    }
    
    def aprovar_pagamento(self, cr, uid, ids, context={}):
        self.pool.get('finan.lancamento').write({'pagamento_bloqueado': False, aprovador_id: uid})
        return {}


finan_lancamento()
 
