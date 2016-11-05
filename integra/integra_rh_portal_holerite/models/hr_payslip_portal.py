# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv


class hr_payslip_portal(osv.Model):
    _name = 'hr.payslip.portal'
    _description = u'Holerites no portal do funcionário'
    _order = 'descricao desc, company_id'
    
    _columns = {
        'payslip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='restrict'),
        'contract_id': fields.related('payslip_id', 'contract_id', type='many2one', relation='hr.contract', string=u'Contrato', store=True),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa/Unidade', store=True),
        'employee_id': fields.related('contract_id', 'employee_id', type='many2one', relation='hr.employee', string=u'Funcionário', store=True),
        'cpf': fields.related('employee_id', 'cpf', type='char', string=u'CPF', store=True),
        'descricao': fields.related('payslip_id', 'descricao', type='char', size=128, string=u'Holerite', store=True, select=True),
        'nome_arquivo': fields.char(u'Nome arquivo', size=120),
        'arquivo': fields.binary(u'Arquivo'),
    }


hr_payslip_portal()
