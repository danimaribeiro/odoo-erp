# -*- coding: utf-8 -*-


from osv import fields, orm
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date
from pybrasil.valor.decimal import Decimal as D


def float_time(tempo):
    hora = int(tempo)
    tempo -= hora

    #if hora == 24:
        #hora = 0

    tempo *= 60.0
    minuto = round(tempo)
    tempo -= minuto
    tempo *= 60.0
    segundo = round(tempo)
    tempo -= segundo
    return '%02d:%02d:%02d.%d' % (hora, minuto, segundo, tempo)

def time_float(tempo):
    hora = int(tempo)

    tempo -= hora

    tempo *= 100.0
    minuto = round(tempo)
    tempo -= minuto
    tempo *= 100.0
    segundo = round(tempo)
    tempo -= segundo

    valor = hora + (minuto / 60.0) + ((segundo / 60.0) / 60.0)
    return valor

TIPO_JORNADA = (
            ('T', u'Trabalha'),
            ('F', u'Folga'),
            ('C', u'Compensa'),
            ('D', u'DSR'),
)

class hr_jornada(orm.Model):
    _name = 'hr.jornada'
    _description = u'Jornadas de trabalho'
    _rec_name = 'descricao'
    _order = 'codigo, hora_entrada, hora_saida'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''
        for registro in self.browse(cursor, user_id, ids):
            #txt = '[' + str(registro.id).zfill(4) + '] ' + registro.codigo
            #txt = '[' + str(registro.id).zfill(4) + '] '
            txt = u' de ' + float_time(registro.hora_entrada)[:5] + ' a ' + float_time(registro.hora_saida)[:5]

            if registro.hora_saida_intervalo_1 and registro.hora_retorno_intervalo_1:
                txt += u', interv. de ' + float_time(registro.hora_saida_intervalo_1)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_1)[:5]

            if registro.hora_saida_intervalo_2 and registro.hora_retorno_intervalo_2:
                txt += u', 2º interv. de ' + float_time(registro.hora_saida_intervalo_2)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_2)[:5]

            if registro.hora_saida_intervalo_3 and registro.hora_retorno_intervalo_3:
                txt += u', 3º interv. de ' + float_time(registro.hora_saida_intervalo_3)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_3)[:5]

            if registro.hora_saida_intervalo_4 and registro.hora_retorno_intervalo_4:
                txt += u', 4º interv. de ' + float_time(registro.hora_saida_intervalo_4)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_4)[:5]

            if registro.hora_saida_intervalo_5 and registro.hora_retorno_intervalo_5:
                txt += u', 5º interv. de ' + float_time(registro.hora_saida_intervalo_5)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_5)[:5]

            retorno[registro.id] = txt

        return retorno

    def _descricao_intervalo(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        for registro in self.browse(cursor, user_id, ids):
            txt = u''

            if fields == 'descricao_intervalo_1' and registro.hora_saida_intervalo_1 and registro.hora_retorno_intervalo_1:
                txt += float_time(registro.hora_saida_intervalo_1)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_1)[:5]

            #if fields == 'descricao_intervalo_2' and registro.hora_saida_intervalo_2 and registro.hora_retorno_intervalo_2:
                #txt += u', 2º interv. de ' + float_time(registro.hora_saida_intervalo_2)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_2)[:5]

            #if registro.hora_saida_intervalo_3 and registro.hora_retorno_intervalo_3:
                #txt += u', 3º interv. de ' + float_time(registro.hora_saida_intervalo_3)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_3)[:5]

            #if registro.hora_saida_intervalo_4 and registro.hora_retorno_intervalo_4:
                #txt += u', 4º interv. de ' + float_time(registro.hora_saida_intervalo_4)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_4)[:5]

            #if registro.hora_saida_intervalo_5 and registro.hora_retorno_intervalo_5:
                #txt += u', 5º interv. de ' + float_time(registro.hora_saida_intervalo_5)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_5)[:5]

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = ['|',
            ('codigo', 'like', texto)
            ('id', 'like', texto)
        ]
        return procura

    def _tempo_noturno(self, cr, uid, hora_entrada, hora_saida, hora_saida_d_mais_1):
        d1 = '2014-01-01 '
        d2_noturna = '2014-01-02 '

        hora_noturna_inicio = parse_date(d1 + '22:00:00')
        hora_noturna_fim_dia = parse_date(d1 + '23:59:59')
        hora_noturna_inicio_dia = parse_date(d2_noturna + '00:00:00')
        hora_noturna_fim = parse_date(d2_noturna + '05:00:00')

        if hora_saida <= 5 or (hora_saida < hora_entrada):
            hora_saida = parse_date(d2_noturna + float_time(hora_saida))
        else:
            hora_saida = parse_date(d1 + float_time(hora_saida))

        if hora_entrada <= 5:
            hora_entrada = parse_date(d2_noturna + float_time(hora_entrada))
        else:
            hora_entrada = parse_date(d1 + float_time(hora_entrada))

        horas_noturnas = D(0)

        #
        # Ajusta agora a hora de entrada noturna
        #
        if (hora_entrada < hora_noturna_inicio) and (hora_saida > hora_noturna_inicio):
            hora_entrada = hora_noturna_inicio

        if (hora_saida > hora_noturna_fim) and (hora_entrada < hora_noturna_fim):
            hora_saida = hora_noturna_fim

        if (hora_noturna_inicio <= hora_entrada < hora_noturna_fim) and (hora_noturna_inicio < hora_saida <= hora_noturna_fim):
            intervalo = hora_saida - hora_entrada
            horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

        else:
            if hora_noturna_inicio <= hora_entrada <= hora_noturna_fim_dia:
                intervalo = hora_noturna_fim_dia - hora_entrada
                horas_noturnas += D(intervalo.seconds + 1) / D(60) / D(60)

            elif hora_noturna_inicio_dia <= hora_entrada <= hora_noturna_fim:
                intervalo = hora_noturna_fim - hora_entrada
                horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

            if hora_noturna_inicio <= hora_saida <= hora_noturna_fim_dia:
                intervalo = hora_saida - hora_noturna_inicio
                horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

            elif hora_noturna_inicio_dia <= hora_saida <= hora_noturna_fim:
                intervalo = hora_saida - hora_noturna_inicio_dia
                horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

        return horas_noturnas

    def _horas_noturnas(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for jornada_obj in self.browse(cr, uid, ids):
            horas_noturnas = self._tempo_noturno(cr, uid, jornada_obj.hora_entrada, jornada_obj.hora_saida, jornada_obj.hora_saida_d_mais_1)

            if nome_campo != 'horas_noturnas_totais' and horas_noturnas > 0:
                #
                # Intervalo 1
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_1 and jornada_obj.hora_retorno_intervalo_1:
                    horas_noturnas -= self._tempo_noturno(cr, uid, jornada_obj.hora_saida_intervalo_1, jornada_obj.hora_retorno_intervalo_1, False)

                #
                # Intervalo 2
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_2 and jornada_obj.hora_retorno_intervalo_2:
                    horas_noturnas -= self._tempo_noturno(cr, uid, jornada_obj.hora_saida_intervalo_2, jornada_obj.hora_retorno_intervalo_2, False)

                #
                # Intervalo 3
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_3 and jornada_obj.hora_retorno_intervalo_3:
                    horas_noturnas -= self._tempo_noturno(cr, uid, jornada_obj.hora_saida_intervalo_3, jornada_obj.hora_retorno_intervalo_3, False)

                #
                # Intervalo 4
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_4 and jornada_obj.hora_retorno_intervalo_4:
                    horas_noturnas -= self._tempo_noturno(cr, uid, jornada_obj.hora_saida_intervalo_4, jornada_obj.hora_retorno_intervalo_4, False)

                #
                # Intervalo 5
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_5 and jornada_obj.hora_retorno_intervalo_5:
                    horas_noturnas -= self._tempo_noturno(cr, uid, jornada_obj.hora_saida_intervalo_5, jornada_obj.hora_retorno_intervalo_5, False)

            res[jornada_obj.id] = horas_noturnas

        return res

    def _horas_com_intervalos(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for jornada_obj in self.browse(cr, uid, ids):
            d1 = float_time(jornada_obj.hora_entrada)
            print(d1)
            d1 = parse_date(d1)
            d2 = float_time(jornada_obj.hora_saida)
            print(d2)
            d2 = parse_date(d2)
            intervalo = d2 - d1
            horas = intervalo.seconds / 60.0 / 60.0

            if nome_campo != 'horas_totais':
                #
                # Intervalo 1
                #
                if jornada_obj and jornada_obj.hora_saida_intervalo_1 and jornada_obj.hora_retorno_intervalo_1:
                    d1 = float_time(jornada_obj.hora_saida_intervalo_1)
                    d1 = parse_date(d1)
                    d2 = float_time(jornada_obj.hora_retorno_intervalo_1)
                    d2 = parse_date(d2)

                    if d2 > d1:
                        intervalo = d2 - d1
                    else:
                        intervalo = d2 - d1

                    horas -= intervalo.seconds / 60.0 / 60.0

                #
                # Intervalo 2
                #
                if jornada_obj.hora_saida_intervalo_2 and jornada_obj.hora_retorno_intervalo_2:
                    d1 = parse_date(str(jornada_obj.hora_saida_intervalo_2) + 'h')
                    d2 = parse_date(str(jornada_obj.hora_retorno_intervalo_2) + 'h')
                    intervalo = d2 - d1
                    horas -= intervalo.seconds / 60.0 / 60.0

                #
                # Intervalo 3
                #
                if jornada_obj.hora_saida_intervalo_3 and jornada_obj.hora_retorno_intervalo_3:
                    d1 = parse_date(str(jornada_obj.hora_saida_intervalo_3) + 'h')
                    d2 = parse_date(str(jornada_obj.hora_retorno_intervalo_3) + 'h')
                    intervalo = d2 - d1
                    horas -= intervalo.seconds / 60.0 / 60.0

                #
                # Intervalo 4
                #
                if jornada_obj.hora_saida_intervalo_4 and jornada_obj.hora_retorno_intervalo_4:
                    d1 = parse_date(str(jornada_obj.hora_saida_intervalo_4) + 'h')
                    d2 = parse_date(str(jornada_obj.hora_retorno_intervalo_4) + 'h')
                    intervalo = d2 - d1
                    horas -= intervalo.seconds / 60.0 / 60.0

                #
                # Intervalo 5
                #
                if jornada_obj.hora_saida_intervalo_5 and jornada_obj.hora_retorno_intervalo_5:
                    d1 = parse_date(str(jornada_obj.hora_saida_intervalo_5) + 'h')
                    d2 = parse_date(str(jornada_obj.hora_retorno_intervalo_5) + 'h')
                    intervalo = d2 - d1
                    horas -= intervalo.seconds / 60.0 / 60.0

            res[jornada_obj.id] = horas

        return res

    _columns = {
        'codigo': fields.char(u'Descrição', 30, select=True, required=True),
        'hora_entrada': fields.float(u'Hora de entrada', widget='float_time', required=True),
        'hora_saida': fields.float(u'Hora de saída', widget='float_time', required=True),
        'data_inicial': fields.date(u'Data de início'),
        'data_final': fields.date(u'Data de término'),
        'hora_saida_d_mais_1': fields.boolean(u'Hora de saída é D+1?'),
        'tipo_intervalo': fields.selection([('0', '0'), ('1', '1'), ('2', '2')], 'Tipo do intervalo'),
        'tipo_jornada': fields.selection(TIPO_JORNADA, 'Tipo jornada'),
        'hora_saida_intervalo_1': fields.float(u'Hora de saída 1º intervalo', widget='float_time'),
        'hora_saida_intervalo_2': fields.float(u'Hora de saída 2º intervalo', widget='float_time'),
        'hora_saida_intervalo_3': fields.float(u'Hora de saída 3º intervalo', widget='float_time'),
        'hora_saida_intervalo_4': fields.float(u'Hora de saída 4º intervalo', widget='float_time'),
        'hora_saida_intervalo_5': fields.float(u'Hora de saída 5º intervalo', widget='float_time'),
        'hora_retorno_intervalo_1': fields.float(u'Hora de retorno 1º intervalo', widget='float_time'),
        'hora_retorno_intervalo_2': fields.float(u'Hora de retorno 2º intervalo', widget='float_time'),
        'hora_retorno_intervalo_3': fields.float(u'Hora de retorno 3º intervalo', widget='float_time'),
        'hora_retorno_intervalo_4': fields.float(u'Hora de retorno 4º intervalo', widget='float_time'),
        'hora_retorno_intervalo_5': fields.float(u'Hora de retorno 5º intervalo', widget='float_time'),
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', fnct_search=_procura_descricao, store=True),
        'descricao_intervalo_1': fields.function(_descricao_intervalo, string=u'Descrição intervalo 1', method=True, type='char', store=True),
        'horas_noturnas': fields.function(_horas_noturnas, string=u'Horas Noturnas', method=True, type='float', store=False),
        'horas_noturnas_totais': fields.function(_horas_noturnas, string=u'Horas Noturnas', method=True, type='float', store=False),
        'horas': fields.function(_horas_com_intervalos, string=u'Horas', method=True, type='float', store=False),
        'horas_totais': fields.function(_horas_com_intervalos, string=u'Horas', method=True, type='float', store=False),
        #'percentual_hora_extra_normal': fields.float(u'Percentual para hora extra normal', digits=(5,2)),
        #'percentual_hora_extra_domingo_feriado': fields.float(u'Percentual hora extra domingos/feriados', digits=(5,2)),
        #'incidencia_adicional_notoruno': fields.boolean(u'Nesta jornada incide adicional noturno ?'),

    }

    _defaults = {
        'hora_saida_d_mais_1': False,
        'tipo_jornada': 'T',
    }

    _sql_constraints = [
        ('jornada_unique', 'unique(hora_entrada, hora_saida, hora_saida_intervalo_1, hora_saida_intervalo_2, hora_saida_intervalo_3, hora_saida_intervalo_4, hora_saida_intervalo_5, hora_retorno_intervalo_1, hora_retorno_intervalo_2, hora_retorno_intervalo_3, hora_retorno_intervalo_4, hora_retorno_intervalo_5)',
            u'Já existe uma jornada cadastrada com esses horários!'),
    ]


hr_jornada()
