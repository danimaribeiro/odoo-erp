# -*- coding: utf-8 -*-


from osv import fields, osv


TIPO_BENEFICIO = (
    ('VT', u'Vale transporte'),
    ('VA', u'Vale Alimentação'),
    ('VR', u'Vale Refeição'),    
)

TIPO_BENEFICIO_PERIODO = (
    ('D', u'Diário'),    
    ('M', u'Mensal'),
)


class hr_salary_rule(osv.Model):
    _name = 'hr.salary.rule'    
    _inherit = 'hr.salary.rule'
   
    _columns = {
        'tipo_beneficio': fields.selection(TIPO_BENEFICIO, u'Tipo benefício', select=True),
        'tipo_beneficio_periodo': fields.selection(TIPO_BENEFICIO_PERIODO, u'Tipo benefício periodo', select=True),
        'rule_valor_ids': fields.one2many('hr.salary.rule.valor', 'rule_id', u'Regra de salário valores'),
    }

    _defaults = {
        
    }


hr_salary_rule()

class hr_salary_rule_valor(osv.Model):
    _name = 'hr.salary.rule.valor'    
    _description = u'Regra de salário valores'
   
    _columns = {
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'valor': fields.float(u'Valor'),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),        
    }

    _defaults = {
        
    }
    
hr_salary_rule_valor()