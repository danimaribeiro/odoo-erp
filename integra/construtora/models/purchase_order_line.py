# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do orçamento', ondelete='restrict'),
        'orcamento_planejamento_id': fields.many2one('project.orcamento.item.planejamento', u'Planejamento do orçamento', ondelete='restrict'),

        'project_id': fields.related('orcamento_item_id', 'project_id', type='many2one', relation='project.project', string=u'Projeto', store=True, select=True, ondelete='restrict'),
        'orcamento_id': fields.related('orcamento_item_id', 'orcamento_id', type='many2one', relation='project.orcamento', string=u'Orçamento', store=True, select=True, ondelete='restrict'),
        'etapa_id': fields.related('orcamento_item_id', 'etapa_id', type='many2one', relation='project.orcamento.etapa', string=u'Etapa', store=True, select=True, ondelete='restrict'),
        'produto_orcado_id': fields.related('orcamento_item_id', 'product_id', type='many2one', relation='product.product', string=u'Produto/Serviço', store=True, select=True, ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/rateio', ondelete='restrict'),
    }


    def onchange_orcamento_item_id(self, cr, uid, ids, orcamento_item_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        item_obj = self.pool.get('project.orcamento.item').browse(cr, uid, orcamento_item_id)

        if item_obj:
            valores['project_id'] = item_obj.project_id.id
            valores['orcamento_id'] = item_obj.orcamento_id.id
            valores['etapa_id'] = item_obj.etapa_id.id
            valores['produto_orcado_id'] = item_obj.product_id.id

        return res


purchase_order_line()
