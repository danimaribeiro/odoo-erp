# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class const_imovel(osv.Model):
    _name = 'const.imovel'
    _inherit = 'const.imovel'
    
    _columns = {
        'morador_ids': fields.many2many('res.partner.address', 'const_imovel_morador', 'imovel_id', 'address_id', u'Moradores'),
        'veiculo_ids': fields.many2many('frota.veiculo', 'const_imovel_veiculo', 'imovel_id', 'veiculo_id', u'Veículos'),
    }


const_imovel()
