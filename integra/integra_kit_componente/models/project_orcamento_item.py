# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D



class project_orcamento_item(osv.Model):
    _inherit = 'project.orcamento.item'
    _description = u'Item do orçamento do projeto'
    
    def _qtd_componentes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for item_obj in self.browse(cr, uid, ids):
            res[item_obj.id] = len(item_obj.itens_componente_ids)
            
        return res

    _columns = {        
        'itens_componente_ids': fields.one2many('project.orcamento.item', 'parent_id', u'Componentes'),                
        'quantidade_componente': fields.float(u'Quantidade componente'),
        'qtd_componentes': fields.function(_qtd_componentes, type='float', string=u'Qtde. componentes', store=True),
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id, project_id):
        if not product_id or not project_id:
            return {}
        
        res = super(project_orcamento_item, self).onchange_product_id(cr, uid, ids, product_id, project_id)  
                
        project_obj = self.pool.get('project.project').browse(cr, uid, project_id)
        produto_obj = self.pool.get('product.product').browse(cr, uid, product_id, context={'company_id': project_obj.company_id.id})
                
        composicao_ids = []

        if len(produto_obj.composicao_ids):
            for composicao_obj in produto_obj.composicao_ids:                        
                dados = {                                        
                    'product_id': composicao_obj.componente_id.id, 
                    'uom_id': composicao_obj.uom_id.id,
                    'vr_unitario':  composicao_obj.standard_price,
                    'vr_produto':  composicao_obj.vr_total,
                    'quantidade_componente': composicao_obj.quantidade,
                    'quantidade': composicao_obj.quantidade,
                    'risco': composicao_obj.risco,
                }
                
                composicao_ids.append([0,False,dados])
                
            res['value']['itens_componente_ids'] = composicao_ids

        return res

    def onchange_quantidade_componente(self, cr, uid, ids, quantidade_componente, quantidade, vr_unitario, risco):
        if not quantidade_componente:
            quantidade_componente = D('0')
        else:
            quantidade_componente = D(quantidade_componente)

        if not quantidade:
            quantidade = D('0')
        else:
            quantidade = D(quantidade)
            
        quantidade *= quantidade_componente

        if not vr_unitario:
            vr_unitario = D('0')
        else:
            vr_unitario = D(vr_unitario)

        if not risco:
            risco = D('0')
        else:
            risco = D(risco)

        vr_produto = quantidade * vr_unitario
        vr_produto = vr_produto.quantize(D('0.01'))
        vr_risco = vr_produto * risco / D('100')
        vr_risco = vr_risco.quantize(D('0.01'))
        vr_risco += vr_produto
        quantidade_risco = quantidade * risco / D('100')
        quantidade_risco = quantidade_risco.quantize(D('0.01'))

        res = {
            'value': {
                'quantidade': quantidade,
                'vr_produto': vr_produto,
                'risco': risco,
                'vr_risco': vr_risco,
                'quantidade_risco': quantidade_risco,
            }
        }

        return res

project_orcamento_item()
