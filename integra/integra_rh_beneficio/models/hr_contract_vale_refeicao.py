# -*- coding: utf-8 -*-


from osv import osv, fields
from datetime import datetime, date, timedelta


class hr_contract_vale_refeicao(osv.Model):
    _name = 'hr.contract.vale.refeicao'
    _description = 'Contrato Vale Refeicao/Alimentacção'

    _columns = {        
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),        
        'quantidade': fields.float(u'Quantidade'),        
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
    }
    
    _defaults = {
        'data_inicial': fields.date.today, 
        #'data_final': fields.date.today,
    }
    
hr_contract_vale_refeicao()

