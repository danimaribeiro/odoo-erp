# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje



class sale_etapa_historico(osv.Model):
    _name = 'sale.etapa.historico'
    _description = u'Histórico de etapas'

    def _tempo_etapa(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = 0

            if sale_obj.data_ultima_etapa and sale_obj.data_proxima_etapa:
                data_inicial = parse_datetime(sale_obj.data_ultima_etapa)
                data_final = parse_datetime(sale_obj.data_proxima_etapa)
            elif sale_obj.data_proxima_etapa:
                data_inicial = parse_datetime(sale_obj.create_date)
                data_final = parse_datetime(sale_obj.data_proxima_etapa)
            else:
                data_inicial = parse_datetime(sale_obj.create_date)
                data_final = parse_datetime(fields.datetime.now())

            intervalo = data_final - data_inicial

            res[sale_obj.id] = intervalo.days

        return res

    _columns = {
        'sale_id': fields.many2one('sale.order', u'Orçamento', ondelet='cascade'),
        'etapa_id': fields.many2one('sale.etapa', u'Etapa', ondelete='restrict'),
        'data_ultima_etapa': fields.datetime(u'Data da última etapa'),
        'data_proxima_etapa': fields.datetime(u'Data da próxima etapa'),
        'tempo_etapa': fields.function(_tempo_etapa, type='integer', string=u'Tempo (dias)', store=True),
    }

    _defaults = {
        'data_ultima_etapa': fields.datetime.now,
        'data_proxima_etapa': fields.datetime.now,
    }


sale_etapa_historico()
