# -*- encoding: utf-8 -*-

from StringIO import StringIO
from reportlab.graphics.barcode.common import I2of5
from geraldo.generators import PDFGenerator, CSVGenerator
from geraldo import Image, Label, ObjectValue, SystemField, BAND_WIDTH
from geraldo.utils import get_attr_value
from pybrasil.base import RelatoAutomatico, RelatoAutomaticoPaisagem, BandaRelato, cm, mm, PAISAGEM, RETRATO
from pybrasil.base.relato.estilo import *
from pybrasil.base.relato.relato import LabelMargemEsquerda, LabelMargemDireita, Titulo, Campo, Texto, Descritivo, CPC
from pybrasil.base.relato.registra_fontes import *
from pybrasil.valor import formata_valor
import base64
import csv


RODAPE = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT}
RODAPE_DATA = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT}

ESTILO = {
    'CABECALHO_TITULO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 14, 'alignment': TA_CENTER},
    #'CABECALHO_TITULO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 14, 'alignment': TA_CENTER},
    'CABECALHO_NORMAL': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 12, 'alignment': TA_RIGHT},
    'CABECALHO_DATA':   {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT},
    'CABECALHO_FILTRO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT},
    'CABECALHO_FILTRO_ESQUERDA': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT},

    #'FILTRO_TITULO':    {'fontName': 'Gentium Italic', 'fontSize': 7, 'alignment': TA_LEFT},
    #'FILTRO_NORMAL':    {'fontName': 'Gentium', 'fontSize': 7, 'alignment': TA_LEFT},

    #'RODAPE_NORMAL':    {'fontName': 'Gentium', 'fontSize': 8, 'alignment': TA_RIGHT},
    #'RODAPE_DATA':      {'fontName': 'Gentium Italic', 'fontSize': 8, 'alignment': TA_LEFT},
}


class Cabecalho(BandaRelato):
    height = 2.5 * cm
    borders = {'top': False, 'bottom': True}
    borders_stroke_width = {'top': 0, 'right': 0, 'bottom': 0.1, 'left': 0}
    elements = [
        SystemField(expression=u'%(report_title)s', left=0 * cm, top=1.0 * cm, style=ESTILO['CABECALHO_TITULO']),
        SystemField(expression=u'Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, style=ESTILO['CABECALHO_NORMAL']),
        SystemField(expression=u'%(now:%A, %d/%m/%Y, %H:%M:%S)s', top=0.65 * cm, right=0.125 * cm, style=ESTILO['CABECALHO_DATA']),
        Label(text=u'', name='filtro', left=0 * cm, top=1.95 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_FILTRO']),
        #Label(text=u'', name='usuario', left=0 * cm, top=1.5 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_NORMAL']),
        #Label(text=u'', name='filial', left=0 * cm, top=1.95 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_NORMAL']),
    ]


class Rodape(BandaRelato):
    height = 0.5 * cm
    borders = {'top': True, 'bottom': False}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
    elements = [
        SystemField(expression=u'%(now:Impresso por ERP Integra em %A, %e de %B de %Y, %H:%M:%S)s', top=0.125 * cm, left=0.125 * cm, width=19 * cm, style=RODAPE_DATA),
        SystemField(expression=u'%(report_title)s ― Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, width=19 * cm, style=RODAPE),
    ]


class FinanRelatorioAutomaticoPaisagem(RelatoAutomaticoPaisagem):
    def __init__(self, *args, **kwargs):
        super(FinanRelatorioAutomaticoPaisagem, self).__init__(*args, **kwargs)
        self.margin_top = 1 * cm
        self.margin_bottom = 1 * cm
        self.margin_left = 1 * cm
        self.margin_right = 1 * cm
        self.largura_maxima = self.largura_maxima + 2

        self.author = u'ERP Integra'

        self.band_page_header = Cabecalho()

        for elemento in self.band_page_header.elements:
            elemento.width = self.largura_maxima *  cm

        self.band_page_header.child_bands = [self.band_titulos]

        #self.band_page_footer = Rodape()

        #for elemento in self.band_page_footer.elements:
            #elemento.width = self.largura_maxima *  cm


class FinanRelatorioAutomaticoRetrato(RelatoAutomatico):
    def __init__(self, *args, **kwargs):
        super(FinanRelatorioAutomaticoRetrato, self).__init__(*args, **kwargs)
        self.margin_top = 1 * cm
        self.margin_bottom = 1 * cm
        self.margin_left = 1 * cm
        self.margin_right = 1 * cm
        self.largura_maxima = self.largura_maxima + 2

        self.author = u'ERP Integra'

        self.band_page_header = Cabecalho()

        for elemento in self.band_page_header.elements:
            elemento.width = self.largura_maxima *  cm

        self.band_page_header.child_bands = [self.band_titulos]

        #self.band_page_footer = Rodape()

        #for elemento in self.band_page_footer.elements:
            #elemento.width = self.largura_maxima *  cm


def gera_relatorio(relatorio, queryset):
    impresso = relatorio

    retorno_pdf = StringIO()

    impresso.queryset = queryset
    impresso.generate_by(PDFGenerator, filename=retorno_pdf)

    pdf = retorno_pdf.getvalue()

    return pdf


def gera_relatorio_csv(relatorio, queryset):
    impresso = relatorio

    retorno_csv = StringIO()

    csv_writer = csv.writer(retorno_csv, delimiter=';', dialect=csv.excel, quoting=csv.QUOTE_MINIMAL)

    impresso.queryset = queryset
    impresso.generate_by(CSVGenerator, filename=retorno_csv, writer=csv_writer)

    csv_texto = retorno_csv.getvalue()
    csv_texto = csv_texto.decode('utf-8')
    csv_texto = csv_texto.replace(u'\u2003', u' ')
    csv_texto = csv_texto.replace(u'\u2002', u' ')
    csv_texto = csv_texto.replace(u'\u2010', u'-')
    csv_texto = csv_texto.replace(u'\u2011', u'-')
    csv_texto = csv_texto.replace(u'\u2012', u'-')
    csv_texto = csv_texto.replace(u'\u2013', u'-')
    csv_texto = csv_texto.replace(u'\u2014', u'-')
    csv_texto = csv_texto.replace(u'\u2015', u'-')
    csv_texto = csv_texto.replace(u' ', u' ')
    csv_texto = csv_texto.replace(u'\u200b', u' ')
    csv_texto = csv_texto.encode('iso-8859-1')

    return csv_texto
