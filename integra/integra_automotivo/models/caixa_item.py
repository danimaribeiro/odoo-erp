# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class caixa_item(orm.Model):
    _name = 'caixa.item'
    _inherit = 'caixa.item'

    _columns = {
        'frota_veiculo_id': fields.related('sale_order_id', 'frota_veiculo_id', type='many2one', relation='frota.veiculo', string=u'Veículo'),
    }


caixa_item()
