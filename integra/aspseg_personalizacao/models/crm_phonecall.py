# -*- coding: utf-8 -*-

from osv import fields, osv

class crm_phonecall(osv.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    
    _columns = {
        'sale_order_id': fields.many2one('sale.order', u'Orçamento/Pedido')
    }


crm_phonecall()
