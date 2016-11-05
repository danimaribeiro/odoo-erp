# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class purchase_solicitacao_cotacao_item_orcado(osv.Model):
    _name = 'purchase.solicitacao.cotacao.item.orcado'

    _columns = {
        'solicitacao_id': fields.many2one('purchase.solicitacao.cotacao', u'Solicitação de materiais', ondelete='cascade'),
        #'project_id': fields.related('item_id', 'project_id', type='many2one', relation='project.project', string=u'Projeto', store=True, select=True, ondelete='restrict'),
        'project_id': fields.many2one('project.project', string=u'Projeto', ondelete='restrict'),
        'item_id': fields.many2one('project.orcamento.item', u'Item do orçamento', ondelete='restrict'),
        
        'orcamento_id': fields.related('item_id', 'orcamento_id', type='many2one', relation='project.orcamento', string=u'Orçamento', store=True, select=True, ondelete='restrict'),
        'etapa_id': fields.related('item_id', 'etapa_id', type='many2one', relation='project.orcamento.etapa', string=u'Etapa', store=True, select=True, ondelete='restrict'),
        'codigo_completo': fields.related('item_id', 'codigo_completo', type='char', size=30, string=u'Código completo', store=True, select=True, ondelete='restrict'),
        'produto_orcado_id': fields.related('item_id', 'product_id', type='many2one', relation='product.product', string=u'Produto/Serviço', store=True, select=True, ondelete='restrict'),
        
        'centrocusto_id': fields.many2one('finan.centrocusto', string=u'Centro de custo/modelo de rateio', ondelete='restrict'),
        'quantidade_orcada': fields.related('item_id', 'quantidade', type='float', string=u'Quantidade', store=True),

        'product_id': fields.many2one('product.product', u'Produto/Serviço solicitado', ondelete='restrict'),
        'quantidade': fields.float(u'Quantidade solicitada'),
        'data_compra_solicitacao': fields.date(u'Data da compra'),
        
        'planejamento_id': fields.many2one('project.orcamento.item.planejamento', u'Planejamento', ondelete='restrict'),
        
        'aprovado': fields.boolean(u'Aprovado'),
        
        'cotacao_aprovada_id': fields.many2one('purchase.cotacao', u'Cotação', ondelete='restrict'),
    }

    _defaults = {
        'data_compra_solicitacao': fields.date.today,
    }
    
    def onchange_item_id(self, cr, uid, ids, item_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores
        
        if not item_id:
            return res
        
        item_obj = self.pool.get('project.orcamento.item').browse(cr, uid, item_id)
        
        valores['project_id'] = item_obj.project_id.id
        valores['etapa_id'] = item_obj.etapa_id.id
        valores['orcamento_id'] = item_obj.orcamento_id.id
        valores['codigo_completo'] = item_obj.codigo_completo
        valores['produto_orcado_id'] = item_obj.product_id.id
        valores['product_id'] = item_obj.product_id.id
        valores['quantidade_orcada'] = item_obj.quantidade or 0
        valores['centrocusto_id'] = item_obj.centrocusto_id.id if item_obj.centrocusto_id else False
        
        return res
    
    def cria_planejamento(self, cr, uid, ids):
        planejamento_pool = self.pool.get('project.orcamento.item.planejamento')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for orcado_obj in self.pool.get('purchase.solicitacao.cotacao.item.orcado').browse(cr, uid, ids):
            item_obj = orcado_obj.item_id
            
            if (not orcado_obj.data_compra_solicitacao):
                continue

            data_execucao = parse_datetime(orcado_obj.data_compra_solicitacao).date()
            dias = item_obj.product_id.sale_delay or 7
            data_execucao += relativedelta(days=dias)

            dados = {
                'item_id': item_obj.id,
                'quantidade': orcado_obj.quantidade,
                'percentual': D(orcado_obj.quantidade or 0) / D(item_obj.quantidade or 1) * 100,
                'data_inicial_execucao': str(data_execucao)[:10],
                'data_final_execucao': str(data_execucao)[:10],
            }
            
            if orcado_obj.planejamento_id:
                planejamento_pool.write(cr, uid, [orcado_obj.planejamento_id.id], dados)
                
            else:
                plan_id = planejamento_pool.create(cr, uid, dados)
                cr.execute("""
                    update purchase.solicitacao.cotacao.item.orcado
                        set planejamento_id = {plan_id}
                        where id = {id};""".format(plan_id = plan_id, id=orcado_obj.id))

    def create(self, cr, uid, dados, context={}):
        res = super(purchase_solicitacao_cotacao_item_orcado, self).create(cr, uid, dados, context=context)

        #self.pool.get('project.orcamento.item').cria_planejamento(cr, uid, res)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(purchase_solicitacao_cotacao_item_orcado, self).write(cr, uid, ids, dados, context=context)

        #self.pool.get('project.orcamento.item').cria_planejamento(cr, uid, ids)

        return res
    

purchase_solicitacao_cotacao_item_orcado()
