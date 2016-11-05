# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_contract(osv.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    _columns = {
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
    }


hr_contract()



class hr_payslip(osv.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'bank_id': fields.related('employee_id', 'bank_id', type='many2one', relation='res.bank', string=u'Banco'),
        'banco_agencia': fields.related('employee_id', 'banco_agencia', type='char', string=u'Agência'),
        'banco_conta': fields.related('employee_id', 'banco_conta', type='char', string=u'Conta'),
    }


hr_payslip()
