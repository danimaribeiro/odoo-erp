# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from integra_frota.models.frota_veiculo import COMBUSTIVEL


class frota_modelo(osv.Model):
    _name = 'frota.modelo'
    _inherit = 'frota.modelo'

    _columns = {
        'manutencao_ids': fields.one2many('frota.manutencao', 'modelo_id', u'Manutenção preventiva'),
    }

    def onchange_tipo_id(self, cr, uid, ids, tipo_id, context={}):
        valores = {}
        res = {'value': valores}

        if not tipo_id:
            return res

        tipo_obj = self.pool.get('frota.tipo').browse(cr, uid, tipo_id)

        if tipo_obj.manutencao_ids:
            manutencao_ids = [[5, 0, {}]]

            for manutencao_obj in tipo_obj.manutencao_ids:
                print('manutencao_obj.servico_id.id', manutencao_obj.servico_id.id)
                manutencao_ids.append([0, 0, {'servico_id': manutencao_obj.servico_id.id, 'km_a_cada': manutencao_obj.km_a_cada}])

            valores['manutencao_ids'] = manutencao_ids
            print(manutencao_ids)

        return res


frota_modelo()
