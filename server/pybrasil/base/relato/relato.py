# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
#from reportlab.lib.colors import HexColor
from copy import deepcopy
from StringIO import StringIO
import base64

from geraldo import ReportBand, Report, DetailBand, FIELD_ACTION_SUM, FIELD_ACTION_COUNT
from geraldo import ObjectValue, Label, SystemField, ReportGroup
from geraldo.generators import PDFGenerator, CSVGenerator

from .registra_fontes import LISTA_FONTES_DEJAVU_SANS, FONTE_DEJAVU_SANS, FONTE_DEJAVU_SANS_NEGRITO
from .registra_fontes import LISTA_FONTES_DEJAVU_SANS_MONO, FONTE_DEJAVU_SANS_MONO, FONTE_DEJAVU_SANS_MONO_NEGRITO
from .estilo import (DESCRITIVO_CAMPO, TITULO_CAMPO, DADO_CAMPO, DESCRITIVO_BLOCO,
                     DADO_CAMPO_NUMERICO, DADO_CAMPO_NEGRITO, DADO_CAMPO_NUMERICO_NEGRITO,
                     DADO_CAMPO_CENTRALIZADO, DESCRITIVO_PRODUTO, DADO_PRODUTO, DADO_PRODUTO_NUMERICO,
                     DADO_PRODUTO_CENTRALIZADO, DESCRITIVO_CAMPO_CENTRALIZADO)
from pybrasil.valor import formata_valor
from pybrasil.data import data_hora_horario_brasilia, parse_datetime


#
# Margens e tamanhos padronizados
#
RETRATO = A4
PAISAGEM = landscape(A4)
MARGEM_SUPERIOR = 2 * cm
MARGEM_INFERIOR = 2 * cm
MARGEM_ESQUERDA = 2 * cm
MARGEM_DIREITA = 2 * cm
LARGURA_RETRATO = 17
LARGURA_PAISAGEM = 25.7

#
# Caracteres por centímetro para a fonte DejaVu Sans Mono
#
CPC = 40.0
CPC_MINIMO_DETALHE = 6.0


class LabelMargemEsquerda(Label):
    def __init__(self):
        super(LabelMargemEsquerda, self).__init__()
        #self.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
        self.borders = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': False}
        self.padding_top = 0.08 * cm
        self.padding_left = 0.08 * cm
        self.padding_bottom = 0.08 * cm
        self.padding_right = 0.08 * cm
        self.style = DESCRITIVO_CAMPO
        self.height = 0.80 * cm


class LabelMargemDireita(LabelMargemEsquerda):
    def __init__(self):
        super(LabelMargemDireita, self).__init__()
        self.borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': 0.1}


class Titulo(Label):
    def __init__(self, *args, **kwargs):
        super(Titulo, self).__init__(*args, **kwargs)
        #self.borders = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': False}
        self.padding_top = 0.1 * cm
        self.padding_left = 0.1 * cm
        self.padding_bottom = 0.1 * cm
        self.padding_right = 0.1 * cm
        self.style = TITULO_CAMPO
        self.height = 0.52 * cm
        self.default_object_value = ''


class Campo(ObjectValue):
    def __init__(self, *args, **kwargs):
        super(Campo, self).__init__(*args, **kwargs)
        self.padding_top = 0.1 * cm
        self.padding_left = 0.1 * cm
        self.padding_bottom = 0.1 * cm
        self.padding_right = 0.1 * cm
        self.style = DADO_CAMPO
        self.height = 0.52 * cm
        self.default_object_value = ''


class Texto(Label):
    def __init__(self, *args, **kwargs):
        super(Texto, self).__init__(*args, **kwargs)
        self.padding_top = 0.1 * cm
        self.padding_left = 0.1 * cm
        self.padding_bottom = 0.1 * cm
        self.padding_right = 0.1 * cm
        self.style = DADO_CAMPO
        self.height = 0.80 * cm
        self.default_object_value = ''


class Descritivo(Label):
    def __init__(self):
        super(Descritivo, self).__init__()
        #self.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
        #self.borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': False}
        self.padding_top = 0.03 * cm
        self.padding_left = 0.1 * cm
        #self.padding_bottom = 0.05 * cm
        self.padding_right = 0.1 * cm
        self.style = DESCRITIVO_BLOCO
        self.height = 0.52 * cm
        self.default_object_value = ''


class BandaRelato(ReportBand):
    def __init__(self):
        super(BandaRelato, self).__init__()

    def _inclui_titulo(self, nome, titulo, top, left, width, height=None, margem_direita=False):
        # Prepara o Label com o título
        if margem_direita:
            lbl = LabelMargemDireita()
        else:
            lbl = LabelMargemEsquerda()

        lbl.name = 'lbl_' + nome
        lbl.text = titulo
        lbl.top = top
        lbl.left = left
        lbl.width = width

        if height:
            lbl.height = height

        return lbl

    def _inclui_campo(self, nome, conteudo, top, left, width, height=None):
        fld = Campo()
        fld.name = 'fld_' + nome
        fld.attribute_name = conteudo
        fld.top = top
        fld.left = left
        fld.width = width

        if height:
            fld.height = height

        return fld

    def _inclui_texto(self, nome, texto, top, left, width, height=None):
        lbl = Texto()
        lbl.name = 'txt_' + nome
        lbl.text = texto
        lbl.top = top
        lbl.left = left
        lbl.width = width

        if height:
            lbl.height = height

        return lbl

    def inclui_campo(self, nome, titulo, conteudo, top, left, width, height=None, margem_direita=False):
        lbl = self._inclui_titulo(nome, titulo, top, left, width, height, margem_direita)
        self.elements.append(lbl)

        fld = self._inclui_campo(nome, conteudo, top, left, width, height)
        fld.padding_top = 0.35 * cm
        self.elements.append(fld)

        return lbl, fld

    def inclui_campo_numerico(self, nome, titulo, conteudo, top, left, width, height=None, margem_direita=False):
        lbl, fld = self.inclui_campo(nome, titulo, conteudo, top, left, width, height, margem_direita)
        fld.style = DADO_CAMPO_NUMERICO

        return lbl, fld

    def inclui_campo_imposto(self, nome, titulo, conteudo, top, left, width, height=None, margem_direita=False):
        borda = self._inclui_titulo(nome, '', top, left, width, height, margem_direita)
        borda.height = 0.8 * cm
        self.elements.append(borda)

        lbl = self._inclui_campo(nome, titulo, top, left, width, height)
        lbl.style = DESCRITIVO_CAMPO
        lbl.padding_top = 0.08 * cm
        lbl.padding_bottom = 0.08 * cm
        lbl.height = 0.28 * cm
        self.elements.append(lbl)

        top += 0.28 * cm
        fld = self._inclui_campo(nome, conteudo, top, left, width, height)
        fld.style = DADO_CAMPO_NUMERICO
        fld.padding_top = 0.08 * cm
        fld.padding_bottom = 0.08 * cm
        fld.height = 0.52 * cm
        self.elements.append(fld)

        return lbl, fld

    def inclui_texto(self, nome, titulo, texto, top, left, width, height=None, margem_direita=False):
        lbl = self._inclui_titulo(nome, titulo, top, left, width, height, margem_direita)
        self.elements.append(lbl)

        if texto:
            txt = self._inclui_texto(nome, texto, top, left, width, height)
            txt.padding_top = 0.25 * cm
            self.elements.append(txt)
        else:
            txt = None

        return lbl, txt

    def inclui_texto_numerico(self, nome, titulo, texto, top, left, width, height=None, margem_direita=False):
        lbl, txt = self.inclui_texto(nome, titulo, texto, top, left, width, height, margem_direita)

        if txt:
            txt.style = DADO_CAMPO_NUMERICO

        return lbl, txt

    def inclui_descritivo(self, nome, titulo, top, left, width, height=None):
        lbl = Descritivo()

        lbl.name = 'dsc_' + nome
        lbl.text = titulo
        lbl.top = top
        lbl.left = left
        lbl.width = width

        if height:
            lbl.height = height

        self.elements.append(lbl)

        return lbl

    def inclui_texto_sem_borda(self, nome, texto, top, left, width, height=None, margem_direita=False):
        txt = self._inclui_texto(nome, texto, top, left, width, height)
        txt.padding_top = 0.1 * cm
        self.elements.append(txt)

        return txt

    def inclui_campo_sem_borda(self, nome, conteudo, top, left, width, height=None, margem_direita=False):
        fld = self._inclui_campo(nome, conteudo, top, left, width, height)
        fld.padding_top = 0.1 * cm
        self.elements.append(fld)

        return fld

    def inclui_descritivo_item(self, nome, titulo, top, left, width, height=None, margem_direita=False):
        lbl = self._inclui_titulo(nome, titulo, top, left, width, height, margem_direita)
        lbl.style = DESCRITIVO_PRODUTO
        lbl.padding_top = 0.05 * cm
        lbl.padding_left = 0.05 * cm
        lbl.padding_bottom = 0.05 * cm
        lbl.padding_right = 0.05 * cm

        if height:
            lbl.height = height
        else:
            lbl.height = 0.42 * cm

        self.elements.append(lbl)
        return lbl

    def inclui_campo_item(self, nome, conteudo, top, left, width, height=None, margem_direita=False):
        fld = self._inclui_campo(nome, conteudo, top, left, width, height)

        if margem_direita:
            fld.borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': 0.1}
        else:
            fld.borders = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': False}

        fld.style = DADO_PRODUTO
        fld.padding_top = 0.05 * cm
        fld.padding_left = 0.05 * cm
        fld.padding_bottom = 0.05 * cm
        fld.padding_right = 0.05 * cm
        fld.auto_expand_height = True

        if height:
            fld.height = height
        else:
            fld.height = 0.28 * cm

        self.elements.append(fld)

        return fld

    def inclui_campo_numerico_item(self, nome, conteudo, top, left, width, height=None, margem_direita=False):
        fld = self.inclui_campo_item(nome, conteudo, top, left, width, height, margem_direita)

        fld.style = DADO_PRODUTO_NUMERICO

        return fld

    def inclui_texto_produto(self, nome, texto, top, left, width, height=None, margem_direita=False):
        txt = self._inclui_texto(nome, texto, top, left, width, height)
        txt.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}

        if margem_direita:
            txt.borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': 0.1}
        else:
            txt.borders = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': False}

        txt.style = DADO_PRODUTO
        txt.padding_top = 0.05 * cm
        txt.padding_left = 0.05 * cm
        txt.padding_bottom = 0.05 * cm
        txt.padding_right = 0.05 * cm
        txt.auto_expand_height = True

        if height:
            txt.height = height
        else:
            txt.height = 0.28 * cm

        self.elements.append(txt)

        return txt

    def inclui_texto_numerico_produto(self, nome, texto, top, left, width, height=None, margem_direita=False):
        txt = self.inclui_texto_produto(nome, texto, top, left, width, height, margem_direita)

        txt.style = DADO_PRODUTO_NUMERICO

        return txt

    def inclui_texto_centralizado_produto(self, nome, texto, top, left, width, height=None, margem_direita=False):
        txt = self.inclui_texto_produto(nome, texto, top, left, width, height, margem_direita)

        txt.style = DADO_PRODUTO_CENTRALIZADO

        return txt


class Relato(Report):
    def __init__(self, *args, **kargs):
        super(Relato, self).__init__(*args, **kargs)
        self.title = 'Relatório padrão'
        self.author = 'PyBrasil'
        self.subject = ''
        self.keywords = ''
        self.producer = 'PyBrasil'
        self.additional_fonts = {FONTE_DEJAVU_SANS: LISTA_FONTES_DEJAVU_SANS, FONTE_DEJAVU_SANS_MONO: LISTA_FONTES_DEJAVU_SANS_MONO}

        self.page_size = RETRATO
        self.margin_top = MARGEM_SUPERIOR
        self.margin_bottom = MARGEM_INFERIOR
        self.margin_left = MARGEM_ESQUERDA
        self.margin_right = MARGEM_DIREITA

    def format_date(self, data, formato):
        data = data_hora_horario_brasilia(data)
        return  data.strftime(formato.encode('utf-8')).decode('utf-8')

    class ObsImpressao(SystemField):
        name = 'obs_impressao'
        expression = 'Impresso em %(now:%d/%m/%Y, %H:%M:%S)s'
        top = 0 * cm
        left = 0.1 * cm
        width = 19.4 * cm
        height = 0.2 * cm
        style = DADO_PRODUTO
        borders = {'top': 0.1}


class RelatoPaisagem(Relato):
    def __init__(self, *args, **kargs):
        super(RelatoPaisagem, self).__init__(*args, **kargs)

        self.page_size = PAISAGEM
        self.largura_maxima = LARGURA_PAISAGEM


class BandTituloAutomatico(ReportBand):
    height = 0.5 * cm
    borders = {'top': False, 'bottom': True}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}


class BandDetailAutomatico(DetailBand):
    height = 0.5 * cm
    borders = {'top': False, 'bottom': False}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}


class BandSummaryAutomatico(ReportBand):
    height = 3 * cm
    borders = {'top': False, 'bottom': True}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
    #default_style = ESTILO['DETALHE_TITULO_DIREITA']


class RelatoAutomatico(Relato):
    def __init__(self, *args, **kargs):
        super(RelatoAutomatico, self).__init__(*args, **kargs)

        self.estilo_automatico = {
            #'DETALHE_TITULO': {'fontName': FONTE_DEJAVU_SANS_MONO_NEGRITO, 'fontSize': 10, 'leading': 12,'alignment': TA_LEFT},
            #'DETALHE_TITULO_CENTRO': {'fontName': FONTE_DEJAVU_SANS_MONO_NEGRITO, 'fontSize': 10, 'leading': 12, 'alignment': TA_CENTER},
            #'DETALHE_TITULO_DIREITA': {'fontName': FONTE_DEJAVU_SANS_MONO_NEGRITO, 'fontSize': 10, 'leading': 12, 'alignment': TA_RIGHT},
            #'DETALHE_NORMAL': {'fontName': FONTE_DEJAVU_SANS_MONO, 'fontSize': 10, 'leading': 12, 'alignment': TA_LEFT},
            #'DETALHE_NORMAL_CENTRO': {'fontName': FONTE_DEJAVU_SANS_MONO, 'fontSize': 10, 'leading': 12, 'alignment': TA_CENTER},
            #'DETALHE_NORMAL_DIREITA': {'fontName': FONTE_DEJAVU_SANS_MONO, 'fontSize': 10, 'leading': 12, 'alignment': TA_RIGHT},

            #
            # Comentando negritos
            #
            #'DETALHE_TITULO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 10, 'leading': 12,'alignment': TA_LEFT},
            #'DETALHE_TITULO_CENTRO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 10, 'leading': 12, 'alignment': TA_CENTER},
            #'DETALHE_TITULO_DIREITA': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 10, 'leading': 12, 'alignment': TA_RIGHT},

            'DETALHE_TITULO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12,'alignment': TA_LEFT},
            'DETALHE_TITULO_CENTRO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12, 'alignment': TA_CENTER},
            'DETALHE_TITULO_DIREITA': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12, 'alignment': TA_RIGHT},

            'DETALHE_NORMAL': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12, 'alignment': TA_LEFT},
            'DETALHE_NORMAL_CENTRO': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12, 'alignment': TA_CENTER},
            'DETALHE_NORMAL_DIREITA': {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 10, 'leading': 12, 'alignment': TA_RIGHT},
        }

        self.band_titulos = BandTituloAutomatico()
        self.band_detail = BandDetailAutomatico()

        self.largura_maxima = LARGURA_RETRATO
        self.cpc = 10.0
        self.cpc_minimo_detalhe = CPC_MINIMO_DETALHE
        self.margem_superior = 0.5
        self.altura_titulo = 2.5
        self.altura_detalhe = 2.5
        self.monta_contagem = False

    def monta_detalhe_automatico(self, colunas):
        campos = []
        tipos = []
        tamanhos = []
        titulos = []
        somas = []
        widgets_soma = []
        widgets_contagem = []
        alinhamentos = []

        if len(colunas[0]) == 5:
            for campo, tipo, tamanho, titulo, soma in colunas:
                campos.append(campo)
                tipos.append(tipo)
                tamanhos.append(tamanho)
                titulos.append(titulo)
                somas.append(soma)
                alinhamentos.append(None)
        else:
            for campo, tipo, tamanho, titulo, soma, alinhamento in colunas:
                campos.append(campo)
                tipos.append(tipo)
                tamanhos.append(tamanho)
                titulos.append(titulo)
                somas.append(soma)
                alinhamentos.append(alinhamento)

        #
        # Primeiro, soma o tamanho dos campos, para determinar o tamanho da fonte
        #
        tam = 0
        for t in tamanhos:
            tam += t + 1
        tam -= 1

        if (tam / self.largura_maxima) <= self.cpc_minimo_detalhe:
            self.cpc = self.cpc_minimo_detalhe
        else:
            self.cpc = tam / self.largura_maxima

        print('tamanho', tam, self.cpc)

        #if tam > 80:
            #self.cpc = tam / (self.largura_maxima - 0.2)
        #else:
            #self.cpc = 80 / (self.largura_maxima - 0.2)

        #if self.cpc > (self._cpc / 11.0):
            #self.cpc = self._cpc / 11.00

        #
        # Modifica o tamanho das fontes dos estilos automáticos
        #
        for estilo in self.estilo_automatico:
            tamanho_fonte = 40.0 / self.cpc
            self.estilo_automatico[estilo]['fontSize'] = tamanho_fonte
            self.estilo_automatico[estilo]['leading'] = tamanho_fonte

        #
        # Modifica a fonte padrão e a altura do detalhe de acordo com o tamanho da fonte calculado
        #
        altura_titulo = (self.altura_titulo / self.cpc) * cm
        self.band_titulos.height = altura_titulo

        self.band_titulos.default_style = self.estilo_automatico['DETALHE_TITULO']

        altura_detalhe = (self.altura_detalhe / self.cpc) * cm
        self.band_detail.height = altura_detalhe
        self.band_detail.default_style = self.estilo_automatico['DETALHE_NORMAL']

        #
        # Percorre agora os campos, montando o cabeçalho e o detalhe
        #
        self.band_titulos.elements = []
        self.band_detail.elements = []

        topo = (self.margem_superior / self.cpc) * cm
        #topo = 0.1 * cm
        esquerda = 0 * cm

        for i in range(len(campos)):
            tamanho_campo = tamanhos[i]
            largura = ((tamanho_campo + 1) / self.cpc) * cm
            largura_texto = (tamanho_campo / self.cpc) * cm
            altura = self.band_titulos.height - (topo * 1.8)

            if tipos[i] in ['F', 'I']:
                widget_titulo = Label(text=titulos[i], left=esquerda, top=topo, width=largura_texto, style={'alignment': TA_RIGHT}, truncate_overflow=True, height=altura)
            else:
                widget_titulo = Label(text=titulos[i], left=esquerda, top=topo, width=largura_texto, truncate_overflow=True, height=altura)

            if tipos[i] in ['F', 'I']:
                widget_campo = ObjectValue(attribute_name=campos[i], left=esquerda, top=topo, width=largura_texto, truncate_overflow=True, height=altura, style={'alignment': TA_RIGHT}, default_object_value=0)
                if tipos[i] == 'I':
                    widget_campo.get_text = lambda objeto, valor: unicode(formata_valor(valor, casas_decimais=0))
                else:
                    widget_campo.get_text = lambda objeto, valor: unicode(formata_valor(valor))

            elif tipos[i] in ['D', 'H', 'DH']:
                widget_campo = ObjectValue(attribute_name=campos[i], left=esquerda, top=topo, width=largura_texto, truncate_overflow=True, height=altura, default_object_value=False)
                if tipos[i] == 'D':
                    widget_campo.get_text = lambda objeto, valor: unicode(parse_datetime(valor).strftime('%d/%m/%Y') if valor else '          ')
                else:
                    widget_campo.get_text = lambda objeto, valor: unicode(parse_datetime(valor).strftime('%d/%m/%Y %H:%M:%S') if valor else '                   ')

            elif tipos[i] in ['B']:
                widget_campo = ObjectValue(attribute_name=campos[i], left=esquerda, top=topo, width=largura_texto, truncate_overflow=True, height=altura, default_object_value=False)
                widget_campo.get_text = lambda objeto, valor: u'SIM' if valor else u'NÃO'

            else:
                widget_campo = ObjectValue(attribute_name=campos[i], left=esquerda, top=topo, width=largura_texto, truncate_overflow=True, height=altura, default_object_value=u'')
                widget_campo.get_text = lambda objeto, valor: valor if isinstance(valor, (str, unicode)) else u''

            if alinhamentos[i]:
                if alinhamentos[i] == 'E':
                    widget_titulo.style = {'alignment': TA_LEFT}
                    widget_campo.style = {'alignment': TA_LEFT}
                elif alinhamentos[i] == 'D':
                    widget_titulo.style = {'alignment': TA_RIGHT}
                    widget_campo.style = {'alignment': TA_RIGHT}
                elif alinhamentos[i] == 'C':
                    widget_titulo.style = {'alignment': TA_CENTER}
                    widget_campo.style = {'alignment': TA_CENTER}

            self.band_titulos.elements.append(widget_titulo)
            self.band_detail.elements.append(widget_campo)

            if tipos[i] in ['I', 'F', 'B'] and somas[i]:
                widget_soma = ObjectValue(attribute_name=campos[i], left=esquerda, top=topo + altura_titulo, width=largura_texto, truncate_overflow=True, height=altura, style={'alignment': TA_RIGHT}, action=FIELD_ACTION_SUM, default_object_value=0)

                if tipos[i] in ['I', 'B']:
                    widget_soma.get_text = lambda objeto, valor: unicode(formata_valor(valor, casas_decimais=0))
                else:
                    widget_soma.get_text = lambda objeto, valor: unicode(formata_valor(valor))

                if not isinstance(somas[i], bool):
                    widget_soma.get_text = somas[i]

                widgets_soma.append(widget_soma)

            esquerda += largura

        self.banda_grupo_somas = None

        #
        # Prepara os totais e o sumário
        #
        titulo = Label(text='Total geral', left=0.1 * cm, top=((self.margem_superior / self.cpc) * cm), width=18.9 * cm, style={'alignment': TA_LEFT}, height=altura_titulo)
        widget_contagem = ObjectValue(attribute_name=campos[0], left=0, top=-4, width=self.largura_maxima * cm, truncate_overflow=True, height=altura_titulo, style={'alignment': TA_RIGHT}, action=FIELD_ACTION_COUNT, default_object_value=0)
        widget_contagem.get_text = lambda objeto, valor: u'Contagem [' + formata_valor(valor if valor else 0, casas_decimais=0) +u']'

        self.band_summary = BandSummaryAutomatico()
        self.band_summary.default_style = self.estilo_automatico['DETALHE_TITULO_DIREITA']
        self.band_summary.height = altura_titulo
        self.band_summary.elements.append(titulo.clone())

        if self.monta_contagem:
            self.band_summary.elements.append(widget_contagem.clone())

        self.band_summary.borders = {'top': True, 'right': False, 'bottom': True, 'left': False}
        self.band_summary.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}

        #
        # Prepara as somas para os grupos
        #
        self.banda_grupo_somas = BandSummaryAutomatico()
        self.banda_grupo_somas.default_style = self.estilo_automatico['DETALHE_TITULO_DIREITA']
        self.banda_grupo_somas.height = altura_titulo
        self.banda_grupo_somas.elements.append(titulo.clone())

        if self.monta_contagem:
            self.banda_grupo_somas.elements.append(widget_contagem.clone())

        self.banda_grupo_somas.borders = {'top': True, 'right': False, 'bottom': True, 'left': False}
        self.banda_grupo_somas.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}

        if len(widgets_soma) > 0:
            self.band_summary.elements += deepcopy(widgets_soma)
            self.band_summary.height = altura_titulo * 2
            self.banda_grupo_somas.elements += deepcopy(widgets_soma)
            self.banda_grupo_somas.height = altura_titulo * 2

    def monta_grupos(self, campos_grupo):
        campos = []
        titulos = []
        novas_paginas = []

        for campo, titulo, nova_pagina in campos_grupo:
            campos.append(campo)
            titulos.append(titulo)
            novas_paginas.append(nova_pagina)

        self.groups = []

        for i in range(len(campos)):
            campo = campos[i]
            titulo = titulos[i]
            nova_pagina = novas_paginas[i]

            grupo = ReportGroup(attribute_name=campo, force_new_page=nova_pagina)

            grupo.band_header = ReportBand(height=self.band_titulos.height * 2, default_style=self.band_titulos.default_style, borders={'bottom': True})
            grupo.band_header.borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}

            topo = ((self.margem_superior / self.cpc) * cm) + self.band_titulos.height

            titulo_grupo = ObjectValue(attribute_name=campo, left=0.1 * cm, top=topo, width=self.largura_maxima * cm, default_object_value='')
            titulo_grupo.get_value = eval("lambda obj: '" + titulo + ": ' + obj." + campo)
            grupo.band_header.elements = [titulo_grupo]

            # Se tem totais tem rodapé
            if self.banda_grupo_somas is not None:
                grupo.band_footer = deepcopy(self.banda_grupo_somas)
                topo = (self.margem_superior / self.cpc) * cm
                titulo_grupo = ObjectValue(attribute_name=campo, left=0.1 * cm, top=topo, width=self.largura_maxima * cm, style={'alignment': TA_LEFT}, default_object_value='')
                titulo_grupo.get_value = eval("lambda obj: 'Total - " + titulo + ": ' + obj." + campo)
                grupo.band_footer.elements[0] = titulo_grupo

            self.groups.append(grupo)
            grupo.parent = self
            grupo.set_parent_on_children()


class RelatoAutomaticoPaisagem(RelatoAutomatico):
    def __init__(self, *args, **kargs):
        super(RelatoAutomaticoPaisagem, self).__init__(*args, **kargs)

        self.page_size = PAISAGEM
        self.largura_maxima = LARGURA_PAISAGEM


def gera_relatorio_pdf(relatorio, queryset):
    impresso = relatorio

    retorno_pdf = StringIO()

    impresso.queryset = queryset
    impresso.generate_by(PDFGenerator, filename=retorno_pdf)

    pdf = retorno_pdf.getvalue()

    return pdf
