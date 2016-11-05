# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_rateio(osv.Model):
    _inherit = 'finan.rateio'

    _columns = {
        'project_orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do orçamento do projeto', ondelete='restrict'),
        'project_orcamento_item_planejamento_id': fields.many2one('project.orcamento.item.planejamento', u'Planejamento do item do orçamento do projeto', ondelete='restrict'),
    }


finan_rateio()

