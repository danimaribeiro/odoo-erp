# -*- coding:utf-8 -*-

from osv import fields, osv


class hr_payslip_afastamento(osv.Model):
    _name = 'hr.payslip_afastamento'
    _description = u'Afastamentos no holerite'

    _columns = {
        'payslip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='cascade'),
        'data_inicial_afastamento': fields.date(u'Data inicial'),
        'data_final_afastamento': fields.date(u'Data final'),
        'afastamento_id': fields.many2one('hr.afastamento', u'Afastamento'),
        'rule_id': fields.related('afastamento_id', 'rule_id', type='many2one', string=u'Rubrica de afastamento', relation='hr.salary.rule', store=True),
        'dias_afastamento': fields.integer(u'Dias de afastamento'),
    }


hr_payslip_afastamento()
