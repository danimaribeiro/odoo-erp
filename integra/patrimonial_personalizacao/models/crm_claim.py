# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


class crm_claim(osv.Model):
    _name = 'crm.claim'
    _inherit = 'crm.claim'    

    _columns = {
        'user_atendimento': fields.many2one('res.users', u'Responsável pelo atendimento'),    
        'departamento_id': fields.many2one('hr.department', u'Setor envolvido'),    
        'employee_id': fields.many2one('hr.employee', u'Funcionário envolvido'),    
          
    }
    
crm_claim()


