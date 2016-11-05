# -*- coding: utf-8 -*-

from osv import osv, fields
from const_imovel import *


class crm_lead(osv.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'const.imovel']

    _columns = {
        'imovel_ids': fields.many2many('const.imovel', 'crm_lead_imovel', 'lead_id', 'imovel_id', u'Imóveis'),
        'codigo': fields.char(u'Código', size=20, required=False),
        'valor_documento_from': fields.float(u'De valor'),
        'valor_documento_to': fields.float(u'A valor'),
        'finan_contrato_ids': fields.one2many('finan.contrato', 'crm_lead_id', u'Propostas'),
    }


crm_lead()
