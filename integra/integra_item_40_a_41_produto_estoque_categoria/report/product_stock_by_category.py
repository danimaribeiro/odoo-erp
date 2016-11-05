# -*- coding: utf-8 -*-

import time
from tools import DEFAULT_SERVER_DATE_FORMAT
from report import report_sxw

class stock_product(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(stock_product, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_category':self.get_category,
            'product_stock_info':self.product_stock_info

        })

    def get_category(self,data):
       result=[]
       if data.has_key('active_ids') and data['active_ids']:
           for category_id in data['active_ids']:
               category={}
               category['name']=str(self.pool.get('product.category').browse(self.cr,self.uid,category_id).name)+str(' ')
               category['id']=category_id
               result.append(category)
           return result

    def product_stock_info(self,cate_id):
         product=self.pool.get('product.product')
         if cate_id:
             result=[]
             total_amt=0
             product_ids=product.search(self.cr,self.uid,[('categ_id','=',cate_id)])
             for prod_obj in product.browse(self.cr,self.uid,product_ids):
                 dic={}
                 dic['code'] = prod_obj.default_code
                 dic['name'] = prod_obj.name
                 dic['qty'] = prod_obj.qty_available
                 dic['value_unit']= prod_obj.unit_value
                 dic['total']= prod_obj.qty_available * prod_obj.unit_value
                 result.append(dic)
             return result

report_sxw.report_sxw('report.stock_product', 'product.category', 'addons/integra_item_40_a_41_produto_estoque_categoria/report/product_stock_by_category.rml', parser=stock_product,)


