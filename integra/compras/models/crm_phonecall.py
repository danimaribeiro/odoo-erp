# -*- coding: utf-8 -*-

from osv import fields, osv

class crm_phonecall(osv.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', u'Pedido de compra')
    }


crm_phonecall()
