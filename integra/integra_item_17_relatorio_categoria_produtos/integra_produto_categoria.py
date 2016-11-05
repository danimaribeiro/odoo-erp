# -*- coding:  utf-8 -*-


import time
from report import report_sxw


class relatorio_produtos_por_categoria(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(relatorio_produtos_por_categoria, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_category': self.get_category,
            'product_info': self.product_info,
            })

    def get_category(self,data):
       result = []
       if data.has_key('active_ids') and data['active_ids']:
           for category_id in data['active_ids']:
               category = {}
               category['name'] = str(self.pool.get('product.category').browse(self.cr,self.uid,category_id).name)+str(' ')
               category['id'] = category_id
               result.append(category)
           return result

    def product_info(self,cate_id):
         product = self.pool.get('product.product')
         if cate_id:
             result = []
             product_ids = product.search(self.cr,self.uid,[('categ_id','=',cate_id)])
             for prod_obj in product.browse(self.cr,self.uid,product_ids):
                 print(prod_obj.__dict__)
                 dic = {}
                 dic['code'] = prod_obj.default_code
                 dic['name'] = prod_obj.name
                 #dic['description'] = prod_obj.description
                 dic['variants'] = prod_obj.variants
                 dic['uom'] = prod_obj.uom_id.name
                 result.append(dic)
             return result

report_sxw.report_sxw('report.relatorio_produtos_por_categoria', 'product.category', 'addons/integra_item_17/integra_produtos_por_categoria.rml', parser=relatorio_produtos_por_categoria)

