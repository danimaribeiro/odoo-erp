# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _inherit = 'frota.veiculo'
    
    _columns = {
        'partner_address_id': fields.many2one('res.partner.address', u'Proprietário', ondelete='restrict'),
    }

frota_veiculo()
