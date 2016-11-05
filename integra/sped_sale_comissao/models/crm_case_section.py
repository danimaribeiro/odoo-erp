# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class crm_case_section(osv.Model):
    _inherit = 'crm.case.section'

    _columns = {
        'comissao_vendedor': fields.float(u'Comissão do vendedor'),
        'comissao_representante': fields.float(u'Comissão do representante'),
        'comissao_revenda': fields.float(u'Comissão da revenda'),
    }


crm_case_section()
