# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from finan.wizard.finan_relatorio import Report
import os
import base64
from pybrasil.data import parse_datetime, formata_data
from pybrasil.valor.decimal import Decimal as D


class frota_os_item(osv.Model):
    _name = 'frota.os_item'
    _description = 'Itens das ordens de serviço'
    #_order = 'placa asc'
    _rec_name = 'os_id'

    def _km_proximo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            km_proximo = D(item_obj.km_atual or 0)
            km_proximo += D(item_obj.km_rodado or 0)

            res[item_obj.id] = km_proximo

        return res

    _columns = {
        'os_id': fields.many2one('frota.os', u'OS'),
        'servico_id': fields.many2one('frota.servico', u'Serviço/atividade'),
        'km_atual': fields.float(u'km atual'),
        'km_rodado': fields.float(u'km rodados'),
        'km_proximo': fields.function(_km_proximo, type='float', string=u'km próximo', store=True),
        'valor': fields.float(u'Valor'),
    }

    def onchange_km_atual_km_rodado(self, cr, uid, ids, km_atual, km_rodado, context={}):
        km_proximo = D(km_atual or 0)
        km_proximo += D(km_rodado or 0)

        res = {
            'value': {'km_proximo': km_proximo}
        }

        return res


frota_os_item()
