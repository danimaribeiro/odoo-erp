# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class project_orcamento_medicao(osv.Model):
    _inherit = 'project.orcamento.medicao'
    
    _columns = {        
        'partner_id': fields.related('orcamento_id', 'partner_id', type='many2one', string=u'Cliente', relation='res.partner', store=True),       
                       
    }

project_orcamento_medicao()  