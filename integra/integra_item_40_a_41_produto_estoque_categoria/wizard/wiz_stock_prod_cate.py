# -*- coding: utf-8 -*-

from osv import osv, fields


class wiz_stock_prod_cate(osv.osv_memory):
    _name = 'wiz.stock.prod.cate'
    _columns = {
   }

    def print_report(self, cr, uid, ids,data):
        data['active_ids'] = data['active_ids']
        return {'type': 'ir.actions.report.xml', 'report_name': 'stock_product', 'datas':data}

wiz_stock_prod_cate()
