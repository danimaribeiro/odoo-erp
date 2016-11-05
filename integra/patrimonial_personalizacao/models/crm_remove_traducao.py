# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class crm_case_stage(orm.Model):
    _name = 'crm.case.stage'
    _inherit = 'crm.case.stage'

    _columns = {       
        'name': fields.char('Stage Name', size=64, required=True, translate=False),
    }


crm_case_stage()



