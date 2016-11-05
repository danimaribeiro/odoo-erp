# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields,osv
from pybrasil.valor.decimal import Decimal as D


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'composicao_ids': fields.one2many('produto.composicao', 'product_id', u'Composição'),    
    }
    
    def ajusta_custo_composto(self, cr, uid, ids):
        for prod_obj in self.browse(cr, uid, ids):
            if not prod_obj.composicao_ids:
                continue
            
            print(prod_obj.default_code)
            
            vr_total = D(0)
            for composicao_obj in prod_obj.composicao_ids:
                vr_total += D(composicao_obj.vr_total or 0)
                
            preco_custo = D(prod_obj.standard_price or 0).quantize(D('0.01'))
            vr_total = vr_total.quantize(D('0.01'))

            if preco_custo != vr_total:
                prod_obj.write({'standard_price': vr_total})                

    def create(self, cr, uid, dados, context={}):
        res = super(product_product, self).create(cr, uid, dados, context=context)
        
        self.pool.get('product.product').ajusta_custo_composto(cr, uid, [res])
        
        return res
    
    def write(self, cr, uid, ids, dados, context={}):
        res = super(product_product, self).write(cr, uid, ids, dados, context=context)
        
        self.pool.get('product.product').ajusta_custo_composto(cr, uid, ids)
        
        return res
    

product_product()