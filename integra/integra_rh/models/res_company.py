# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'avisoprevioproporcional_ids': fields.many2many('hr.aviso_previo_proporcional', 'hr_aviso_previo_proporcional_company', 'company_id', 'avisoprevioproporcional_id', string=u'Tabela de aviso prévio indenizado'),
    }

res_company()
