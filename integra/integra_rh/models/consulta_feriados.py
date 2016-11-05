# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
#from osv import osv
import urllib2
import json
from dateutil.parser import parse as parse_date
from datetime import date
from pybrasil.feriado import (conta_feriados_sem_domingo, data_eh_feriado)

FERIADOS_PERIODO = {}


#def conta_feriados_sem_domingo(data_inicial, data_final, estado, municipio):
    #url = u'http://live.erpintegra.com.br:8237/conta_feriados_sem_domingo'
    #url += u'/' + estado
    #url += u'/' + municipio
    #url += u'/' + str(data_inicial)[:10]
    #url += u'/' + str(data_final)[:10]

    #print(url)
    #try:
        #resposta = urllib2.urlopen(url.encode('utf-8'))
        #texto_resposta = resposta.read().decode('utf-8')
        #resposta = json.loads(texto_resposta)
    #except:
        #resposta = {'total': 0}

    #print(resposta)

    #return resposta['total']


#def data_eh_feriado(data, estado, municipio):
    #url = u'http://live.erpintegra.com.br:8237/data_eh_feriado'
    #url += u'/' + estado
    #url += u'/' + municipio
    #url += u'/' + str(data)[:10]

    #print(url)
    ##try:
    #resposta = urllib2.urlopen(url.encode('utf-8'))
    #texto_resposta = resposta.read().decode('utf-8')
    #resposta = json.loads(texto_resposta)
    ##except:
        ##resposta = {}

    #print(resposta)

    #return resposta


def feriados_no_periodo(data_inicial, data_final, estado, municipio):
    data_inicial = parse_date(data_inicial).date().toordinal()
    data_final = parse_date(data_final).date().toordinal()

    periodo = str(data_inicial) + '_' + str(data_final)

    if estado in FERIADOS_PERIODO:
        if municipio in FERIADOS_PERIODO[estado]:
            if periodo in FERIADOS_PERIODO[estado][municipio]:
                return FERIADOS_PERIODO[estado][municipio][periodo]

    data = data_inicial
    feriados = {}
    while data <= data_final:
        feriados[data] = None
        feriado = data_eh_feriado(date.fromordinal(data), estado, municipio)

        if feriado:
            feriados[data] = feriado

        data += 1

    if not estado in FERIADOS_PERIODO:
        FERIADOS_PERIODO[estado] = {}

    if not municipio in FERIADOS_PERIODO[estado]:
        FERIADOS_PERIODO[estado][municipio] = {}

    if not periodo in FERIADOS_PERIODO[estado][municipio]:
        FERIADOS_PERIODO[estado][municipio][periodo] = feriados

    return FERIADOS_PERIODO[estado][municipio][periodo]


def dias_sem_feriado(data_inicial, data_final, estado, municipio, dias_semana):
    feriados = feriados_no_periodo(data_inicial, data_final, estado, municipio)
    data_inicial = parse_date(data_inicial).date().toordinal()
    data_final = parse_date(data_final).date().toordinal()

    data = data_inicial
    dias = 0
    while data <= data_final:
        if date.fromordinal(data).weekday() in dias_semana:
            print(date.fromordinal(data), feriados[data])
            if not feriados[data]:
                dias += 1

        data += 1

    return dias
