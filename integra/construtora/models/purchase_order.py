# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv

class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    _columns = {
        'cotacao_id': fields.many2one('purchase.cotacao', u'Cotação'),
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento'),
        'project_id': fields.many2one('project.project', u'Projeto'),
        #
        # Campo pra tapear o open...
        #
        'cotacao_ids': fields.many2many('purchase.cotacao', 'purchase_order', 'id', 'cotacao_id', u'Cotação'),
        'lancamento_ids': fields.one2many('finan.lancamento', 'purchase_order_id', u'Vencimentos'),
    }


purchase_order()
