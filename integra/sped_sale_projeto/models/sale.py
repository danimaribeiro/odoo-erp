# -*- encoding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class sale_order(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto'),
    }


sale_order()
