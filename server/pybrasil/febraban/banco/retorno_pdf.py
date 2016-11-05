# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
from reportlab.graphics.barcode.common import I2of5
from geraldo.generators import PDFGenerator
from geraldo import Image, Label, ObjectValue, SystemField
from geraldo.utils import get_attr_value
from ...base import RelatoAutomaticoPaisagem, BandaRelato, cm, mm, PAISAGEM
from ...base.relato.estilo import *
from ...base.relato.relato import LabelMargemEsquerda, LabelMargemDireita, Titulo, Campo, Texto, Descritivo
from ...base.relato.registra_fontes import *
from pybrasil.valor import formata_valor


CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}
RODAPE = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT}
RODAPE_DATA = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT}


class LogoBanco(Image):
    def __init__(self, *args, **kwargs):
        super(LogoBanco, self).__init__(*args, **kwargs)
        self.cache_logo = {}

    def _get_image(self):
        try:
            import Image as PILImage
        except ImportError:
            from PIL import Image as PILImage

        if get_attr_value(self.instance, 'banco.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'banco.arquivo_logo')

            if nome_arq_logo not in self.cache_logo or not self.cache_logo[nome_arq_logo]:
                self.cache_logo[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            arq = StringIO(self.cache_logo[nome_arq_logo])
            self._image = PILImage.open(arq)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


class Cabecalho(BandaRelato):
    def __init__(self, *args, **kwargs):
        super(Cabecalho, self).__init__(*args, **kwargs)
        self.elements = []

        #
        # 1ª linha
        #
        lbl, txt = self.inclui_texto(nome='', titulo='', texto=u'', top=0 * cm, left=0 * cm, width=3.2 * cm, height=1 * cm)

        img = LogoBanco()
        img.top = 0.1 * cm
        img.left = 0.1 * cm
        self.elements.append(img)

        lbl, fld = self.inclui_campo(nome='', titulo='', conteudo='banco.codigo_digito', top=0 * cm, left=3.2 * cm, width=2 * cm, height=1 * cm)
        fld.style = CODIGO_BANCO
        fld.padding_top = 0.2 * cm
        lbl, fld = self.inclui_texto(nome='', titulo='', texto='Arquivo de retorno de cobrança', top=0 * cm, left=5.2 * cm, width=20.5 * cm, margem_direita=True, height=1 * cm)
        fld.style = LINHA_DIGITAVEL
        fld.padding_top = 0.3 * cm
        fld.padding_left = 0 * cm
        fld.padding_right = 0 * cm

        #
        # 2ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='Beneficiário', conteudo='beneficiario.nome', top=1 * cm, left=0 * cm, width=12.95 * cm)

        lbl, fld = self.inclui_campo(nome='', titulo='CNPJ', conteudo='beneficiario.cnpj_cpf', top=1 * cm, left=12.95 * cm, width=4.25 * cm, margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='', titulo='Agência/código do beneficiário', conteudo='beneficiario.agencia_codigo_beneficiario', top=1 * cm, left=17.2 * cm, width=4.25 * cm, margem_direita=True)
        lbl, fld = self.inclui_campo_numerico(nome='', titulo='Agência/conta', conteudo='beneficiario.agencia_conta', top=1 * cm, left=21.45 * cm, width=4.25 * cm, margem_direita=True)

        ##
        ## 3ª linha
        ##
        #lbl, fld = self.inclui_campo(nome='', titulo='Beneficiário', conteudo='beneficiario.nome', top=1.8 * cm, left=0 * cm, width=12.75 * cm)


        ##
        ## 4ª linha
        ##
        #lbl, fld = self.inclui_campo(nome='', titulo='Data do documento', conteudo='documento.data_formatada', top=2.6 * cm, left=0 * cm, width=3.1875 * cm)
        #lbl, fld = self.inclui_campo(nome='', titulo='Nº do documento', conteudo='documento.numero', top=2.6 * cm, left=3.1875 * cm, width=3.1875 * cm)
        #lbl, fld = self.inclui_campo(nome='', titulo='Espécie do documento', conteudo='documento.especie', top=2.6 * cm, left=6.375 * cm, width=2.1875 * cm)
        #fld.style = DADO_CAMPO_CENTRALIZADO
        #lbl, fld = self.inclui_campo(nome='', titulo='Aceite', conteudo='aceite', top=2.6 * cm, left=8.5625 * cm, width=1 * cm)
        #fld.style = DADO_CAMPO_CENTRALIZADO
        #lbl, fld = self.inclui_campo(nome='', titulo='Data do processamento', conteudo='data_processamento_formatada', top=2.6 * cm, left=9.5625 * cm, width=3.1875 * cm)

        #lbl, fld = self.inclui_campo_numerico(nome='', titulo='Carteira/nosso número', conteudo='carteira_nosso_numero', top=2.6 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ##
        ## 5ª linha
        ##
        #lbl, txt = self.inclui_texto(nome='', titulo='Uso do banco', texto='', top=3.4 * cm, left=0 * cm, width=3.1875 * cm)
        #lbl, fld = self.inclui_campo(nome='', titulo='Carteira', conteudo='banco.carteira', top=3.4 * cm, left=3.1875 * cm, width=1 * cm)
        #fld.style = DADO_CAMPO_CENTRALIZADO
        #lbl, fld = self.inclui_campo(nome='', titulo='Espécie da moeda', conteudo='especie', top=3.4 * cm, left=4.1875 * cm, width=2.1875 * cm)
        #fld.style = DADO_CAMPO_CENTRALIZADO
        #lbl, txt = self.inclui_texto(nome='', titulo='Quantidade', texto='', top=3.4 * cm, left=6.375 * cm, width=3.1875 * cm)
        #lbl, txt = self.inclui_texto(nome='', titulo='Valor', texto='', top=3.4 * cm, left=9.5625 * cm, width=3.1875 * cm)

        #lbl, fld = self.inclui_campo_numerico(nome='', titulo='(=) Valor do documento', conteudo='documento.valor_formatado', top=3.4 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ##
        ## 6ª a 10ª linha
        ##
        #lbl, fld = self.inclui_campo(nome='instrucao', titulo='Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)', conteudo='instrucoes_impressao', top=4.2 * cm, left=0 * cm, width=12.75 * cm, height=4 * cm)
        #lbl, txt = self.inclui_texto(nome='', titulo='(-) Desconto/abatimento', texto='', top=4.2 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        #lbl, txt = self.inclui_texto(nome='', titulo='(-) Outras deduções', texto='', top=5 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        #lbl, txt = self.inclui_texto(nome='', titulo='(+) Mora/multa', texto='', top=5.8 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        #lbl, txt = self.inclui_texto(nome='', titulo='(+) Outros acréscimos', texto='', top=6.6 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        #lbl, txt = self.inclui_texto(nome='', titulo='(=) Valor cobrado', texto='', top=7.4 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ##
        ## 11ª linha
        ##
        #lbl, fld = self.inclui_campo(nome='', titulo='Pagador', conteudo='pagador.impressao', top=8.2 * cm, left=0 * cm, width=12.75 * cm, height=1.8 * cm)
        #lbl.borders['right'] = False
        #lbl.borders['left'] = False
        #lbl, fld = self.inclui_campo(nome='', titulo='CNPJ/CPF', conteudo='pagador.cnpj_cpf', top=8.2 * cm, left=12.75 * cm, width=4.25 * cm, height=1.8 * cm)
        #lbl.borders['right'] = False
        #lbl.borders['left'] = False

        #lbl, txt = self.inclui_texto(nome='', titulo='Autenticação mecânica/ficha de compensação', texto='', top=10 * cm, left=12 * cm, width=5 * cm)
        #lbl.borders = False

        #codigo_barras = BarCode(type='I2of5', attribute_name='codigo_barras', top=10.35 * cm, left=0 * cm, height=1.3 * cm, aditional_barcode_params={'ratio': 3, 'bearers': 0, 'quiet': 0, 'checksum': 0, 'barWidth': 0.25 * mm})

        #self.elements.append(codigo_barras)

        self.height = 1.8 * cm


class Rodape(BandaRelato):
    height = 0.5 * cm
    borders = {'top': True, 'bottom': False}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
    elements = [
        SystemField(expression=u'%(now:Impresso %A, %e de %B de %Y, %H:%M:%S)s', top=0.125 * cm, left=0.125 * cm, width=25.7 * cm, style=RODAPE_DATA),
        SystemField(expression=u'%(report_title)s ― Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, width=25.7 * cm, style=RODAPE),
    ]


class ImpressoRetorno(RelatoAutomaticoPaisagem):
    def __init__(self, *args, **kwargs):
        super(ImpressoRetorno, self).__init__(*args, **kwargs)
        self.band_page_header = Cabecalho()
        self.band_page_header.child_bands = [self.band_titulos]
        self.band_page_footer = Rodape()

        colunas = [
            ['nosso_numero',           'C', 10, 'Nosso nº', False],
            ['documento.numero',       'C', 20, 'Nº documento', False],
            ['pagador.cnpj_cpf',       'C', 18, 'Pagador CNPJ/CPF', False],
            ['pagador.nome',           'C', 20, 'Pagador nome', False],
            ['comando',                'C',  2, 'Comando', False],
            ['comando_retorno_descricao', 'C',  25, 'Descrição', False],
            ['pagamento_duplicado', 'B',  4, 'Dup', False],
            ['data_ocorrencia',           'D', 10, 'Ocorrência', False],
            ['data_credito',           'D', 10, 'Crédito', False],
            ['documento.valor',        'F', 10, 'Valor doc.', True],
            ['valor_despesa_cobranca', 'F',  6, 'Tarifa', True],
            ['valor_outras_despesas',  'F', 10, 'Outras desp.', True],
            ['valor_desconto',         'F', 10, 'Desconto', True],
            ['valor_juros',            'F', 10, 'Juros', True],
            ['valor_multa',  'F', 10, 'Multa', True],
            ['valor_recebido',         'F', 10, 'Valor recebido', True],
        ]

        grupos = [
            ['comando_retorno_descricao_grupo', 'Comando', True],
        ]

        self.monta_detalhe_automatico(colunas)
        self.monta_grupos(grupos)


def gera_retorno_pdf(retorno, classe_leiaute=ImpressoRetorno):
    impresso_retorno = classe_leiaute()

    boletos = sorted(retorno.boletos, key=lambda boleto: boleto.comando + '_' + boleto.nosso_numero)

    for boleto in boletos:
        boleto.retorno = retorno

    retorno_pdf = StringIO()

    titulo = impresso_retorno.band_page_header.elements[5]
    titulo.text = 'Arquivo de retorno de cobrança nº ' + formata_valor(retorno.sequencia, casas_decimais=0) + ' - ' + retorno.data_hora.strftime('%d/%m/%Y')
    impresso_retorno.title = titulo.text

    impresso_retorno.queryset = boletos
    impresso_retorno.generate_by(PDFGenerator, filename=retorno_pdf)
    #impresso_retorno.generate_by(PDFGenerator, filename='/home/ari/retorno.pdf')

    pdf = retorno_pdf.getvalue()

    retorno_pdf.close()

    return pdf
