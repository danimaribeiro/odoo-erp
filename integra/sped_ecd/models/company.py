# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_company(osv.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    
    _columns = {
        'plano_id': fields.many2one('ecd.plano.conta', string=u'Plano de contas', ondelete='cascade'),
        
    }

    

res_company()
