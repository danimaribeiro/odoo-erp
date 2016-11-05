# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class condo_despesa(osv.Model):
    _name = 'condo.despesa'
    _description = u'Despesas do Condominio'

    
    _columns = {
        'project_id': fields.many2one('project.project', u'Condôminio'),
        'data': fields.date(u'Data'),    
        'data_vencimento': fields.date(u'Data vencimento'),    
        'documento_id': fields.many2one('finan.documento', u'Documento'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro Custo'),
        'valor': fields.float(u'Valor'),
        'item_ids': fields.one2many('condo.despesa.item', 'cond_despesa_id', u'Itens da Despesa'),        
    }
    
    _defaults = {
        'data': fields.datetime.now(),                        
    }


condo_despesa()

class condo_despesa_item(osv.Model):
    _name = 'condo.despesa.item'
    _description = u'Itens da Despesa'
    
    _columns = {
        'cond_despesa_id': fields.many2one('condo.despesa', u'Despesa do condoninio'),
        'project_id': fields.many2one('project.project', u'Condôminio'),
        'unidade_id': fields.many2one('const.imovel', u'Unidade'),
        'valor': fields.float(u'Valor'),        
    }
    
    _defaults = {
                                
    }


condo_despesa_item()

