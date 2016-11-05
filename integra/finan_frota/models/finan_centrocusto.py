# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


# from datetime import datetime
from osv import fields, osv


class finan_rateio(osv.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.rateio'
    _inherit = 'finan.rateio'

    _columns = {
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', select=True, ondelete='restrict'),
    }


finan_rateio()
