# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _inherit = 'frota.veiculo'

    _columns = {
        'rateio_ids': fields.one2many('finan.rateio', 'veiculo_id', u'Rateios onde o veículo está alocado'),
        'ipva_ids': fields.one2many('finan.lancamento', 'veiculo_id', u'IPVA', domain=[('eh_ipva', '=', True)]),
        'licenciamento_ids': fields.one2many('finan.lancamento', 'veiculo_id', u'Licenciamento', domain=[('eh_licenciamento', '=', True)]),
        'dpvat_ids': fields.one2many('finan.lancamento', 'veiculo_id', u'DPVAT', domain=[('eh_dpvat', '=', True)]),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
    }


frota_veiculo()
