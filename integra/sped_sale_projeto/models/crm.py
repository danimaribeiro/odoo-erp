# -*- encoding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class crm_lead(osv.Model):
    _inherit = 'crm.lead'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto'),
    }


crm_lead()
