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


CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}
RODAPE = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT}
RODAPE_DATA = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT}

ESTILO = {
    'CABECALHO_TITULO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 14, 'alignment': TA_CENTER},
    'CABECALHO_NORMAL': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 12, 'alignment': TA_RIGHT},
    'CABECALHO_DATA':   {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT},

    #'FILTRO_TITULO':    {'fontName': 'Gentium Italic', 'fontSize': 7, 'alignment': TA_LEFT},
    #'FILTRO_NORMAL':    {'fontName': 'Gentium', 'fontSize': 7, 'alignment': TA_LEFT},

    #'RODAPE_NORMAL':    {'fontName': 'Gentium', 'fontSize': 8, 'alignment': TA_RIGHT},
    #'RODAPE_DATA':      {'fontName': 'Gentium Italic', 'fontSize': 8, 'alignment': TA_LEFT},
}


CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}
RODAPE = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT}
RODAPE_DATA = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT}

ESTILO = {
    'CABECALHO_TITULO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 14, 'alignment': TA_CENTER},
    'CABECALHO_NORMAL': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 12, 'alignment': TA_RIGHT},
    'CABECALHO_DATA':   {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT},
    'CABECALHO_FILTRO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT},

    #'FILTRO_TITULO':    {'fontName': 'Gentium Italic', 'fontSize': 7, 'alignment': TA_LEFT},
    #'FILTRO_NORMAL':    {'fontName': 'Gentium', 'fontSize': 7, 'alignment': TA_LEFT},

    #'RODAPE_NORMAL':    {'fontName': 'Gentium', 'fontSize': 8, 'alignment': TA_RIGHT},
    #'RODAPE_DATA':      {'fontName': 'Gentium Italic', 'fontSize': 8, 'alignment': TA_LEFT},
}


class LogoBanco(Image):
    def _get_image(self):
        try:
            import Image as PILImage
        except ImportError:
            from PIL import Image as PILImage

        if get_attr_value(self.instance, 'company_id.logo'):
            if self.instance.company_id.logo:
                arq_logo = StringIO()
                logo = base64.decodestring(self.instance.company_id.logo)
                arq_logo.write(logo)
                arq_logo.seek(0)
                logo = PILImage.open(arq_logo)
                largura, altura = logo.size

                razao_largura = 215.0 / float(largura)
                razao_altura = 132.0 / float(altura)

                if razao_largura < razao_altura:
                    largura *= razao_largura
                    altura *= razao_largura
                elif razao_altura < razao_largura:
                    largura *= razao_altura
                    altura *= razao_altura

                logo = logo.resize((int(largura), int(altura)), PILImage.ANTIALIAS)
                print(logo)
                self._image = logo

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


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


class RHRelatorioAutomaticoPaisagem(RelatoAutomaticoPaisagem):
    def __init__(self, *args, **kwargs):
        super(RHRelatorioAutomaticoPaisagem, self).__init__(*args, **kwargs)
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

        self.band_page_footer = Rodape()

        for elemento in self.band_page_footer.elements:
            elemento.width = self.largura_maxima *  cm


class RHRelatorioAutomaticoRetrato(RelatoAutomatico):
    def __init__(self, *args, **kwargs):
        super(RHRelatorioAutomaticoRetrato, self).__init__(*args, **kwargs)
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

        self.band_page_footer = Rodape()

        for elemento in self.band_page_footer.elements:
            elemento.width = self.largura_maxima *  cm


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
    impresso.generate_by(CSVGenerator, filename=retorno_csv,writer=csv_writer)

    csv_texto = retorno_csv.getvalue()
    csv_texto = csv_texto.decode('utf-8').encode('iso-8859-1')  
        
    return csv_texto
