# -*- encoding: utf-8 -*-

from osv import osv, fields


class sale_order(osv.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
    
    _columns = {     
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento'),       
    }    


sale_order()

class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'
    
    _columns = {     
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do Orçamento'),       
    }    


sale_order()

