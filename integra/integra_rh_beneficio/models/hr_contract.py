# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_contract(osv.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    _columns = {
        'linha_transporte_ids': fields.one2many('hr.contract.linha.transporte', 'contract_id', u'Vale transporte'),
        'vale_refeicao_ids': fields.one2many('hr.contract.vale.refeicao', 'contract_id', u'Vale refeição/alimentacão'),
    }


hr_contract()

