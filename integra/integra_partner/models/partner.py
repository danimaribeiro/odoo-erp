# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    _columns = {
        'shop_id': fields.many2one('sale.shop', 'Shop'),
        'address_municipio_id': fields.related('address', 'municipio_id', type='many2one', string=u'Município', relation='sped.municipio'),
    }


res_partner()
