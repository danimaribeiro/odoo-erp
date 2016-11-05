# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D



class produto_composicao(osv.Model):
    _name = 'produto.composicao'    
    _description = u'Composição item do orçamento'
    
    
    def _get_valor(self, cr, uid, ids, nome_campo, args, context=None):
        
        res = {}
        
        total = D('0')                  
        for componente_obj in self.browse(cr, uid, ids):
            if componente_obj.standard_price and componente_obj.quantidade:
               valor_unitario =  D(str(componente_obj.standard_price))
               quantidade =  D(str(componente_obj.quantidade))               
               total += valor_unitario * quantidade 
               
        res[componente_obj.id] = total.quantize(D('0.01'))   
                    
        return res

    _columns = {
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do orçamento', ondelete='restrict'),                
        'product_id': fields.many2one('product.product', u'Produto', ondelete='restrict'),
        'componente_id': fields.many2one('product.product', u'Componente'),
        'uom_id': fields.related('componente_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade'),
        'list_price': fields.related('componente_id', 'list_price', type='float', string=u'Preço de venda'),
        'standard_price': fields.related('componente_id', 'standard_price', type='float', string=u'Preço de custo'),
        'quantidade': fields.float(u'Quantidade'),
        'risco': fields.float(u'% risco'),
        'vr_total': fields.function(_get_valor, type='float', store=True, digits=(18, 2), string=u'Valor total'),        
    }
    
    def onchange_componente_id(self, cr, uid, ids, componente_id):
        if not componente_id:
            return {}
        
        res = {}
        valores = {}
        res['value'] = valores
        
        componente_obj = self.pool.get('product.product').browse(cr, uid, componente_id)
        
        valores['uom_id'] = componente_obj.uom_id.id
        valores['list_price'] = componente_obj.list_price or 0
        valores['standard_price'] = componente_obj.standard_price or 0
        
        return res


produto_composicao()
