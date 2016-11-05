# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from integra_frota.models.frota_veiculo import COMBUSTIVEL


class frota_tipo(osv.Model):
    _name = 'frota.tipo'
    _inherit = 'frota.tipo'

    _columns = {
        'manutencao_ids': fields.one2many('frota.manutencao', 'tipo_id', u'Manutenção preventiva'),
    }


frota_tipo()
