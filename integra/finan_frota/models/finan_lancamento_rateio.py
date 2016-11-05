# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_lancamento_rateio(osv.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.lancamento.rateio'
    _inherit = 'finan.lancamento.rateio'

    _columns = {
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', select=True, ondelete='restrict'),
    }


finan_lancamento_rateio()
