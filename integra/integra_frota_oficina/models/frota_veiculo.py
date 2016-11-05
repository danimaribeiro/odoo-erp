# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _inherit = 'frota.veiculo'

    _columns = {
        'manutencao_ids': fields.one2many('frota.manutencao', 'veiculo_id', u'Manutenção preventiva'),
    }

    def onchange_modelo_id(self, cr, uid, ids, modelo_id, context={}):
        valores = {}
        res = {'value': valores}

        if not modelo_id:
            return res

        modelo_obj = self.pool.get('frota.modelo').browse(cr, uid, modelo_id)

        if modelo_obj.manutencao_ids:
            manutencao_ids = [[5, 0, {}]]

            for manutencao_obj in modelo_obj.manutencao_ids:
                manutencao_ids.append([0, 0, {'servico_id': manutencao_obj.servico_id.id, 'km_a_cada': manutencao_obj.km_a_cada}])

            valores['manutencao_ids'] = manutencao_ids

        elif modelo_obj.tipo_id.manutencao_ids:
            manutencao_ids = [[5, 0, {}]]

            for manutencao_obj in modelo_obj.tipo_id.manutencao_ids:
                manutencao_ids.append([0, 0, {'servico_id': manutencao_obj.servico_id.id, 'km_a_cada': manutencao_obj.km_a_cada}])

            valores['manutencao_ids'] = manutencao_ids

        return res


frota_veiculo()
