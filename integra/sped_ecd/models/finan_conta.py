# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class finan_conta(osv.Model):
    _inherit = 'finan.conta'          
    
    _columns = {
        'plano_id': fields.many2one('ecd.plano.conta', string=u'Plano de contas', ondelete='restrict'),                       
           
    }
    
    _defaults = {
    }

finan_conta()
