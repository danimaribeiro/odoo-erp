# -*- coding: utf-8 -*-


from osv import fields, osv
from integra_sesmt.constante_sesmt import *


class sesmt_epi(osv.Model):
    _name = 'sesmt.epi'
    _description = u'EPI'
    _rec_name = 'nome'
    _order = 'nome'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}
        #txt = u''
        #for registro in self.browse(cursor, user_id, ids):
            #txt = registro.codigo #+ ' - Entrando às ' + registro.ocupacao

            #if registro.hora_saida_intervalo_1 and registro.hora_retorno_intervalo_1:
                #txt += u', 1º interv. de ' + float_time(registro.hora_saida_intervalo_1)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_1)[:5]

            #if registro.hora_saida_intervalo_2 and registro.hora_retorno_intervalo_2:
                #txt += u', 2º interv. de ' + float_time(registro.hora_saida_intervalo_2)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_2)[:5]

            #if registro.hora_saida_intervalo_3 and registro.hora_retorno_intervalo_3:
                #txt += u', 3º interv. de ' + float_time(registro.hora_saida_intervalo_3)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_3)[:5]

            #if registro.hora_saida_intervalo_4 and registro.hora_retorno_intervalo_4:
                #txt += u', 4º interv. de ' + float_time(registro.hora_saida_intervalo_4)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_4)[:5]

            #if registro.hora_saida_intervalo_5 and registro.hora_retorno_intervalo_5:
                #txt += u', 5º interv. de ' + float_time(registro.hora_saida_intervalo_5)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_5)[:5]

            #retorno[registro.id] = txt

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #('codigo', 'like', texto)
        #]
        #return procura

    _columns = {
        'data_inicial': fields.date(u'Data inicial', required=True, select=True),
        'data_final': fields.date(u'Data final', select=True),
        'ca': fields.char(u'Certificado de aprovação', size=6, select=True, required=True),
        'data_validade_ca': fields.date(u'Validade do CA', required=True),
        'nome': fields.char(u'Descrição', size=50, select=True, required=True),
        'marca': fields.char(u'Marca', size=50),
        'descartavel': fields.boolean(u'Descartável?'),
        'tipo_vida_util': fields.selection(TIPO_VIDA_UTIL, u'Vida útil em'),
        'tempo_vida_util': fields.float(u'Vida útil'),
        'auditivo': fields.boolean(u'Auditivo?'),
        'nrr': fields.float(u'NRR', digits=(15, 2)),
        'nrr_sf': fields.float(u'NRR (SF)', digits=(15, 2)),

        'treinamento_ids': fields.many2many('sesmt.treinamento', 'sesmt_epi_treinamento', 'epi_id', 'treinamento_id', u'Treinamentos'),
    }

    _defaults = {
        'descartavel': False,
        'auditivo': False,
        'tipo_vida_util': 'M',
        'nrr': 0,
        'nrr_sf': 0,
    }

sesmt_epi()
