# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class crm_lead(orm.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'
    _description = 'Crm'

    _columns = {
          'receita_vendas_patrimonial': fields.float(u'Receia de Vendas'),    
          'receita_servico': fields.float(u'Receia de Vendas'),    
    }
    
    def onchange_receita(self, cr, uid, ids, receita_servico=0, receita_locacao=0, context={}):
        valores = {}
        res = {'value': valores}
        
        valores['planned_revenue'] = receita_servico + receita_locacao
        
        return res

crm_lead()


