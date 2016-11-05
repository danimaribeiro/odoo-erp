# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_lancamento(orm.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'hr_sefip_id': fields.many2one('hr.sefip', u'SEFIP originário', ondelete='restrict'),
    }


finan_lancamento()


class finan_lancamento_rateio(osv.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.lancamento.rateio'
    _inherit = 'finan.lancamento.rateio'

    _columns = {
        'hr_contract_id': fields.many2one('hr.contract', u'Funcionário', select=True, ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/Posto', select=True, ondelete='restrict'),
    }


finan_lancamento_rateio()
