# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_payroll_structure(orm.Model):
    _name = 'hr.payroll.structure'
    _inherit = 'hr.payroll.structure'
    _description = 'Struture Model'

    _columns = {
        'lo_modelo_ids': fields.many2many('lo.modelo', 'lo_modelo_hr_structure', 'hr_struct_id', 'lo_modelo_id', u'Modelos LibreOffice'),
    }


hr_payroll_structure()
