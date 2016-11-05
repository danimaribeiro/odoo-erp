# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_sindicato(osv.Model):
    _name = 'hr.sindicato'
    _inherit = 'hr.sindicato'

    _columns = {
        'beneficio_ids': fields.one2many('hr.sindicato.beneficio', 'sindicato_id', u'Benefícios'),        
    }


hr_sindicato()

