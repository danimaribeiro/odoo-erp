# -*- coding: utf-8 -*-


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


def _tempo_noturno(hora_entrada, hora_saida, hora_saida_d_mais_1):
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

    print(hora_noturna_inicio, hora_noturna_fim, hora_entrada, hora_saida)

    if (hora_noturna_inicio <= hora_entrada < hora_noturna_fim) and (hora_noturna_inicio < hora_saida <= hora_noturna_fim):
        intervalo = hora_saida - hora_entrada
        print('intervalo 1', intervalo)
        horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

    else:
        if hora_noturna_inicio <= hora_entrada <= hora_noturna_fim_dia:
            intervalo = hora_noturna_fim_dia - hora_entrada
            print('intervalo 2', intervalo)
            horas_noturnas += D(intervalo.seconds + 1) / D(60) / D(60)

        elif hora_noturna_inicio_dia <= hora_entrada <= hora_noturna_fim:
            intervalo = hora_noturna_fim - hora_entrada
            print('intervalo 3', intervalo)
            horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

        if hora_noturna_inicio <= hora_saida <= hora_noturna_fim_dia:
            intervalo = hora_saida - hora_noturna_inicio
            print('intervalo 4', intervalo)
            horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

        elif hora_noturna_inicio_dia <= hora_saida <= hora_noturna_fim:
            intervalo = hora_saida - hora_noturna_inicio_dia
            print('intervalo 5', intervalo)
            horas_noturnas += D(intervalo.seconds) / D(60) / D(60)

    return horas_noturnas

