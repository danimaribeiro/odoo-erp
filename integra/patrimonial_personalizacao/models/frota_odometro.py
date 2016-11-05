# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from datetime import datetime
from osv import osv, fields
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia, UTC
from pybrasil.valor.decimal import Decimal as D


class frota_odometro(osv.Model):
    _name = 'frota.odometro'
    _inherit = 'frota.odometro'

    def fecha_odometro(self, cr, uid, ids, context={}):
        if not ids:
            return

        for os_obj in self.browse(cr, uid, ids):
            if not os_obj.valor_anterior:
                raise osv.except_osv(u'Erro!', u'Não é permitido fechar sem o preenchimento da quilometragem anterior!')

            if not os_obj.valor_atual:
                raise osv.except_osv(u'Erro!', u'Não é permitido fechar sem o preenchimento da quilometragem atual!')

            #
            # Acima de 200 km de distância, somente gerentes para fechar o
            # odômetro
            #
            if os_obj.distancia > 200:
                usuario_obj = self.pool.get('res.users').browse(cr, 1, uid)
                pode_fechar = False
                for grupo_obj in usuario_obj.groups_id:
                    if grupo_obj.name == 'Integra / Gerente de Frota':
                        pode_fechar = True

                if not pode_fechar:
                    raise osv.except_osv(u'Erro!', u'Você não tem permissão de fechar esse registro, pois a quilometragem é maior do que 200 km!')

                if not os_obj.justificativa:
                    raise osv.except_osv(u'Erro!', u'Você não pode fechar esse registro sem justificativa!')

            if not os_obj.data_fechamento:
                raise osv.except_osv(u'Erro!', u'Você não pode fechar esse registro sem preencher a data de fechamento!')

        return self.write(cr, uid, ids, {'state': 'F'})


frota_odometro()
