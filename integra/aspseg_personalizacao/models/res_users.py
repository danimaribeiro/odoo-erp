# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields

class res_users(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'
    _description = 'Users Operacão'
    

    _columns = {
         'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal', select=True),
   
    } 

    
res_users()
