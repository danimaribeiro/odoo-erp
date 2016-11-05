# -*- coding: utf-8 -*-


from osv import fields, osv
from tools.safe_eval import safe_eval as eval


SINAL_CATEGORIA = [
    ('-', u'Dedução'),
    ('+', u'Provento'),
    ('0', u'Base de cálculo/demonstrativo'),
]


class hr_salary_rule_category(osv.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'
    _inherit = 'hr.salary.rule.category'

    _columns = {
        #'name':fields.char('Name', size=64, required=True, readonly=False),
        #'code':fields.char('Code', size=64, required=True, readonly=False),
        #'parent_id':fields.many2one('hr.salary.rule.category', 'Parent', help="Linking a salary category to its parent is used only for the reporting purpose."),
        #'children_ids': fields.one2many('hr.salary.rule.category', 'parent_id', 'Children'),
        #'note': fields.text('Description'),
        #'company_id':fields.many2one('res.company', 'Company', required=False),
        'sinal': fields.selection(SINAL_CATEGORIA, u'Sinal'),
    }

    _defaults = {
        'sinal': '+',
    }


hr_salary_rule_category()
