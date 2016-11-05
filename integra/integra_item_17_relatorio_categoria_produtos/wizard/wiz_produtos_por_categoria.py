# -*- coding: utf-8 -*-


from osv import osv, fields
from tools.translate import _


class wiz_produtos_por_categoria(osv.osv_memory):
    _name = 'wiz.produtos.por.categoria'
    _columns = {}

    def print_report(self, cr, uid, ids,data):
        data['active_ids'] = data['active_ids']
        return {'type': 'ir.actions.report.xml', 'report_name': 'relatorio_produtos_por_categoria', 'datas': data}


wiz_produtos_por_categoria()
