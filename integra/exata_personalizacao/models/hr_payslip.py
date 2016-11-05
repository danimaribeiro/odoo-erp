# -*- coding: utf-8 -*-


from osv import fields, orm , osv


class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    def imprime_recibo_pagamento(self, cr, uid, ids, context={}):
        context['exibe_ferias'] = 'S'
        return super(hr_payslip, self).imprime_recibo_pagamento(cr, uid, ids, context=context)


hr_payslip()



class hr_holerite(osv.osv_memory):
    _name = 'hr.holerite'
    _inherit = 'hr.holerite'

    def gera_holerites(self, cr, uid, ids, context={}):
        context['exibe_ferias'] = 'S'
        return super(hr_holerite, self).gera_holerites(cr, uid, ids, context=context)


hr_holerite()
