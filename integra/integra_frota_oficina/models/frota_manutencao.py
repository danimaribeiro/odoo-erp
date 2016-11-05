# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, hoje, amanha
from dateutil.relativedelta import relativedelta



class frota_manutencao(osv.Model):
    _name = 'frota.manutencao'
    _description = u'Manutenção preventiva de veículo'
    _order = 'modelo_id, veiculo_id, servico_id, data_ultima_execucao desc'
    _rec_name = 'servico_id'

    def _data_prevista(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for manutencao_obj in self.browse(cr, uid, ids, context=context):
            res[manutencao_obj.id] = {'data_prevista_proxima_execucao': False, 'urgencia': False}

            if not manutencao_obj.veiculo_id:
                continue

            veiculo_obj = manutencao_obj.veiculo_id

            if manutencao_obj.os_item_id:
                res[manutencao_obj.id] = {'data_prevista_proxima_execucao': False, 'urgencia': 'azul'}
                continue

            if manutencao_obj.data_proxima_execucao:
                data_proxima_execucao = parse_datetime(manutencao_obj.data_proxima_execucao).date()

            elif (veiculo_obj.km_atual >= manutencao_obj.km_proxima_execucao):
                data_proxima_execucao = hoje()

            elif (not veiculo_obj.km_media_diaria) and manutencao_obj.data_maxima_proxima_execucao:
                data_proxima_execucao = parse_datetime(manutencao_obj.data_maxima_proxima_execucao).date()

            else:
                km_falta = D(manutencao_obj.km_proxima_execucao or 0) - D(veiculo_obj.km_atual or 0)
                dias_falta = km_falta / D(veiculo_obj.km_media_diaria or 1)

                data_ultima_execucao = parse_datetime(manutencao_obj.data_ultima_execucao).date()
                data_proxima_execucao = data_ultima_execucao + relativedelta(days=int(dias_falta.quantize(D(1))))

                if manutencao_obj.data_maxima_proxima_execucao and str(data_proxima_execucao) > manutencao_obj.data_maxima_proxima_execucao:
                    data_proxima_execucao = parse_datetime(manutencao_obj.data_maxima_proxima_execucao).date()

            if data_proxima_execucao < hoje():
                dias = hoje() - data_proxima_execucao
                if dias.days > 10:
                    urgencia = 'preto'
                elif dias.days >= 5:
                    urgencia = 'amarelo'
                else:
                    urgencia = 'vermelho'

            else:
                urgencia = 'vermelho'

            res[manutencao_obj.id] = {'data_prevista_proxima_execucao': str(data_proxima_execucao), 'urgencia': urgencia}

        return res

    _columns = {
        'tipo_id': fields.many2one('frota.tipo', u'Tipo', ondelete='cascade'),
        'modelo_id': fields.many2one('frota.modelo', u'Modelo', ondelete='cascade'),
        'servico_id': fields.many2one('frota.servico', u'Serviço', ondelete='restrict'),
        'km_a_cada': fields.float(u'Executar a cada X km'),

        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', ondelete='restrict'),
        'km_ultima_execucao': fields.float(u'km última execução'),
        'data_ultima_execucao': fields.date(u'Data da última execução'),
        'km_proxima_execucao': fields.float(u'km próxima execução'),
        'data_maxima_proxima_execucao': fields.date(u'Data máxima da próxima execução'),
        'data_prevista_proxima_execucao': fields.function(_data_prevista, type='date', string=u'Data prevista da próxima execução', multi='data'),
        'urgencia': fields.function(_data_prevista, type='char', string=u'Urgência', multi='data'),
        'data_proxima_execucao': fields.date(u'Data da próxima execução'),
        'os_item_id': fields.many2one('frota.os_item', u'Item atendido', ondelete='restrict'),
        'os_id': fields.related('os_item_id', 'os_id', type='many2one', relation='frota.os', string=u'OS atendida', store=True),
    }

    def onchange_km_ultima_execucao(self, cr, uid, ids, km_a_cada, km_ultima_execucao, data_ultima_execucao, context={}):
        valores = {}
        res = {'value': valores}

        if not (km_a_cada and km_ultima_execucao):
            return res

        km_proxima_execucao = D(km_ultima_execucao or 0) + D(km_a_cada or 0)
        valores['km_proxima_execucao'] = km_proxima_execucao

        if 'km_media_diaria' in context and 'km_atual' in context and data_ultima_execucao:
            km_media_diaria = D(context['km_media_diaria'] or 0)
            km_atual = D(context['km_atual'] or 0)

            if km_atual < km_proxima_execucao:
                km_falta = km_proxima_execucao - km_atual
                dias_falta = km_falta / km_media_diaria
                data_ultima_execucao = parse_datetime(data_ultima_execucao).date()

                data_proxima_execucao += relativedelta(days=dias_falta.quantize(D(1)))
                data_proxima_execucao = str(data_proxima_execucao)

            else:
                km_falta = 0
                dias_falta = 0
                data_proxima_execucao = str(hoje())

            valores['data_prevista_proxima_execucao'] = data_proxima_execucao

        return res


frota_manutencao()
