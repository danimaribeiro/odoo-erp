# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
from geraldo.generators import PDFGenerator
from geraldo import Image, Line, BarCode, ObjectValue
from geraldo.utils import get_attr_value
from ...base.relato import *
from ...base.relato.estilo import *
from ...base.relato.registra_fontes import *
from PyPDF2 import PdfFileWriter, PdfFileReader
from copy import copy

try:
    import Image as PILImage
except ImportError:
    from PIL import Image as PILImage

CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}
CACHE_LOGO = {}


class LogoBanco(Image):
    def __init__(self, *args, **kwargs):
        super(LogoBanco, self).__init__(*args, **kwargs)
        self.cache_logo = {}

    def _get_image(self):
        if get_attr_value(self.instance, 'nfse.boleto.banco.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'nfse.boleto.banco.arquivo_logo')

            #if nome_arq_logo not in self.cache_logo or not self.cache_logo[nome_arq_logo]:
                #self.cache_logo[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            #arq = StringIO(self.cache_logo[nome_arq_logo])

            if nome_arq_logo not in CACHE_LOGO or not CACHE_LOGO[nome_arq_logo]:
                CACHE_LOGO[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            arq = StringIO(CACHE_LOGO[nome_arq_logo])

            self._image = PILImage.open(arq)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


class LogoPrefeitura(Image):
    def __init__(self, *args, **kwargs):
        super(LogoPrefeitura, self).__init__(*args, **kwargs)
        self.cache_logo = {}

    def _get_image(self):
        if get_attr_value(self.instance, 'nfse.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'nfse.arquivo_logo')

            #if nome_arq_logo not in self.cache_logo or not self.cache_logo[nome_arq_logo]:
                #self.cache_logo[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            #arq = StringIO(self.cache_logo[nome_arq_logo])

            if nome_arq_logo not in CACHE_LOGO or not CACHE_LOGO[nome_arq_logo]:
                CACHE_LOGO[nome_arq_logo] = open(nome_arq_logo, 'rb').read()
                print('guardou cache')

            arq = StringIO(CACHE_LOGO[nome_arq_logo])

            self._image = PILImage.open(arq)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


MARGEM_SUPERIOR = 0.8 * cm
MARGEM_INFERIOR = 0.8 * cm
MARGEM_ESQUERDA = 0.8 * cm
MARGEM_DIREITA = 0.8 * cm


class FichaCompensacao(BandaRelato):
    def __init__(self, *args, **kwargs):
        super(FichaCompensacao, self).__init__(*args, **kwargs)
        self.elements = []

        #
        # 1ª linha
        #
        lbl, txt = self.inclui_texto(nome='', titulo='', texto=u'', top=0 * cm, left=0 * cm, width=3.2 * cm, height=1 * cm)

        img = LogoBanco()
        img.top = 0.1 * cm
        img.left = 0.1 * cm
        self.elements.append(img)

        lbl, fld = self.inclui_campo(nome='', titulo='', conteudo='nfse.boleto.banco.codigo_digito', top=0 * cm, left=3.2 * cm, width=2 * cm, height=1 * cm)
        fld.style = CODIGO_BANCO
        fld.padding_top = 0.2 * cm
        lbl, fld = self.inclui_campo(nome='', titulo='', conteudo='nfse.boleto.linha_digitavel', top=0 * cm, left=5.2 * cm, width=13.8 * cm, margem_direita=True, height=1 * cm)
        fld.style = LINHA_DIGITAVEL
        fld.padding_top = 0.3 * cm
        fld.padding_left = 0 * cm
        fld.padding_right = 0 * cm

        #
        # 2ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='Local de pagamento', conteudo='nfse.boleto.local_pagamento', top=1 * cm, left=0 * cm, width=12.75 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='', titulo='Data de vencimento', conteudo='nfse.boleto.data_vencimento_formatada', top=1 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)
        fld.style = DADO_CAMPO_NUMERICO_NEGRITO

        #
        # 3ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='Beneficiário', conteudo='nfse.boleto.beneficiario.nome', top=1.8 * cm, left=0 * cm, width=12.75 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='', titulo='Agência/código do beneficiário', conteudo='nfse.boleto.imprime_agencia_conta', top=1.8 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)

        #
        # 4ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='Data do documento', conteudo='nfse.boleto.documento.data_formatada', top=2.6 * cm, left=0 * cm, width=3.1875 * cm)
        lbl, fld = self.inclui_campo(nome='', titulo='Nº do documento', conteudo='nfse.boleto.documento.numero', top=2.6 * cm, left=3.1875 * cm, width=3.1875 * cm)
        lbl, fld = self.inclui_campo(nome='', titulo='Espécie do documento', conteudo='nfse.boleto.documento.especie', top=2.6 * cm, left=6.375 * cm, width=2.1875 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='', titulo='Aceite', conteudo='nfse.boleto.aceite', top=2.6 * cm, left=8.5625 * cm, width=1 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='', titulo='Data do processamento', conteudo='nfse.boleto.data_processamento_formatada', top=2.6 * cm, left=9.5625 * cm, width=3.1875 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='', titulo='Carteira/nosso número', conteudo='nfse.boleto.imprime_carteira_nosso_numero', top=2.6 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)

        #
        # 5ª linha
        #
        lbl, txt = self.inclui_texto(nome='', titulo='Uso do banco', texto='', top=3.4 * cm, left=0 * cm, width=3.1875 * cm)
        lbl, fld = self.inclui_campo(nome='', titulo='Carteira', conteudo='nfse.boleto.banco.carteira', top=3.4 * cm, left=3.1875 * cm, width=1 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='', titulo='Espécie da moeda', conteudo='nfse.boleto.especie', top=3.4 * cm, left=4.1875 * cm, width=2.1875 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, txt = self.inclui_texto(nome='', titulo='Quantidade', texto='', top=3.4 * cm, left=6.375 * cm, width=3.1875 * cm)
        lbl, txt = self.inclui_texto(nome='', titulo='Valor', texto='', top=3.4 * cm, left=9.5625 * cm, width=3.1875 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='', titulo='(=) Valor do documento', conteudo='nfse.boleto.documento.valor_formatado', top=3.4 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)

        #
        # 6ª a 10ª linha
        #
        lbl, fld = self.inclui_campo(nome='instrucao', titulo='Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)', conteudo='nfse.boleto.instrucoes_impressao', top=4.2 * cm, left=0 * cm, width=12.75 * cm, height=4 * cm)
        lbl, txt = self.inclui_texto(nome='', titulo='(-) Desconto/abatimento', texto='', top=4.2 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)
        lbl, txt = self.inclui_texto(nome='', titulo='(-) Outras deduções', texto='', top=5 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)
        lbl, txt = self.inclui_texto(nome='', titulo='(+) Mora/multa', texto='', top=5.8 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)
        lbl, txt = self.inclui_texto(nome='', titulo='(+) Outros acréscimos', texto='', top=6.6 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)
        lbl, txt = self.inclui_texto(nome='', titulo='(=) Valor cobrado', texto='', top=7.4 * cm, left=12.75 * cm, width=6.25 * cm, margem_direita=True)

        #
        # 11ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='Pagador', conteudo='nfse.boleto.pagador.impressao', top=8.2 * cm, left=0 * cm, width=12.75 * cm, height=1.8 * cm)
        lbl.borders['right'] = False
        lbl.borders['left'] = False
        lbl, fld = self.inclui_campo(nome='', titulo='CNPJ/CPF', conteudo='nfse.boleto.pagador.cnpj_cpf', top=8.2 * cm, left=12.75 * cm, width=6.25 * cm, height=1.8 * cm)
        lbl.borders['right'] = False
        lbl.borders['left'] = False

        lbl, txt = self.inclui_texto(nome='', titulo='Autenticação mecânica/ficha de compensação', texto='', top=10 * cm, left=12 * cm, width=7 * cm)
        lbl.borders = False

        codigo_barras = BarCode(type='I2of5', attribute_name='nfse.boleto.codigo_barras', top=10.35 * cm, left=0 * cm, height=1.3 * cm, aditional_barcode_params={'ratio': 3, 'bearers': 0, 'quiet': 0, 'checksum': 0, 'barWidth': 0.25 * mm})

        self.elements.append(codigo_barras)

        self.height = 12 * cm


class FichaCompensacaoTerco(FichaCompensacao):
    ''' Encolhe a fonte e a altura dos elementos da ficha de compensação
    para caberem 3 numa folha A4
    '''
    def __init__(self, *args, **kwargs):
        super(FichaCompensacaoTerco, self).__init__(*args, **kwargs)

        sobe_topo = 0
        alturas = {}
        topos = {}
        self.height -= 2.6 * cm
        self.elements[-1].top -= 2.6 * cm
        self.elements[-2].top -= 2.6 * cm

        for elemento in self.elements[:-2]:
            if isinstance(elemento, LogoBanco):
                elemento.top -= 0.075 * cm

            elif isinstance(elemento, (LabelMargemEsquerda, LabelMargemDireita)):
                if elemento.height not in alturas:
                    if elemento.text in ['pagador.cnpj_cpf', 'CNPJ/CPF', 'pagador.impressao', 'Pagador']:
                        alturas[elemento.height] = elemento.height - 0.45 * cm
                    elif elemento.text in ['instrucoes_impressao', 'Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)']:
                        alturas[elemento.height] = elemento.height - 1.15 * cm
                    else:
                        alturas[elemento.height] = elemento.height - 0.23 * cm

                if elemento.top not in topos:
                    topos[elemento.top] = elemento.top - sobe_topo
                    sobe_topo += 0.23 * cm

                elemento.height = alturas[elemento.height]
                elemento.top = topos[elemento.top]

                estilo = copy(elemento.style)
                estilo['fontSize'] = estilo['fontSize'] - 1.5
                if 'leading' in estilo:
                    estilo['leading'] = estilo['leading'] - 1.5
                elemento.style = estilo

            elif isinstance(elemento, Campo):
                if elemento.attribute_name in ['pagador.cnpj_cpf', 'CNPJ/CPF', 'pagador.impressao', 'Pagador']:
                    alturas[elemento.height] = elemento.height - 0.45 * cm
                elif elemento.attribute_name in ['instrucoes_impressao', 'Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)']:
                    alturas[elemento.height] = elemento.height - 1.15 * cm
                elif elemento.height not in alturas:
                    alturas[elemento.height] = elemento.height - 0.23 * cm

                if elemento.top not in topos:
                    topos[elemento.top] = elemento.top - sobe_topo
                    sobe_topo += 0.23 * cm

                elemento.height = alturas[elemento.height]
                elemento.top = topos[elemento.top]

                if elemento.attribute_name not in ['linha_digitavel', 'banco.codigo_digito']:
                    elemento.padding_top = elemento.padding_top - 0.13 * cm
                    estilo = copy(elemento.style)
                    estilo['fontSize'] = estilo['fontSize'] - 1.5
                    if 'leading' in estilo:
                        estilo['leading'] = estilo['leading'] - 1.5
                    elemento.style = estilo
                elif elemento.attribute_name == 'linha_digitavel':
                    elemento.padding_top = elemento.padding_top - 0.07 * cm
                elif elemento.attribute_name == 'banco.codigo_digito':
                    elemento.padding_top = elemento.padding_top - 0.07 * cm


class ImpressoNFSe(Relato):
    def __init__(self, *args, **kargs):
        super(ImpressoNFSe, self).__init__(*args, **kargs)
        self.title = 'NFS-e - Nota Fiscal de Serviços Eletrônica'
        self.print_if_empty = True
        self.margin_top = MARGEM_SUPERIOR
        self.margin_bottom = MARGEM_INFERIOR
        self.margin_left = MARGEM_ESQUERDA
        self.margin_right = MARGEM_DIREITA

        # Bandas e observações
        self.band_page_header = Cabecalho()
        self.band_page_header.child_bands = [CabecalhoRPS(), Prestador(), Tomador(), Discriminacao(), TituloServicos()]
        self.band_detail = DetItem()

        #self.band_page_footer = RodapeTotais()
        #self.band_page_footer.child_bands = [RodapeObservacoes()]


class Cabecalho(BandaRelato):
    def __init__(self):
        super(Cabecalho, self).__init__()
        self.elements = []

        # Quadro do emitente
        self.inclui_texto(nome='quadro_emitente', titulo='', texto='', top=0*cm, left=0*cm, width=15.4*cm, height=2.4*cm)

        #
        # Área central - Dados do DANFE
        #
        fld = self.inclui_campo_sem_borda(nome='prefeitura', conteudo='nfse.prefeitura', top=0.5*cm, left=3*cm, width=12.4*cm, height=0.5*cm)
        fld.style = DESCRITIVO_DANFE

        #txt = self.inclui_texto_sem_borda(nome='secretaria', texto='Secretaria Municipal de Finanças', top=0.75*cm, left=3*cm, width=12.4*cm, height=0.5*cm)
        #txt.style = DESCRITIVO_DANFE

        txt = self.inclui_texto_sem_borda(nome='nfse', texto='NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e', top=1.5*cm, left=3*cm, width=12.4*cm, height=0.5*cm)
        txt.style = DESCRITIVO_DANFE

        lbl, fld = self.inclui_campo_numerico(nome='numero', titulo='Número da NFS-e', conteudo='nfse.numero_formatado', top=0*cm, left=15.4*cm, width=4*cm, margem_direita=True)
        fld.style = DADO_CAMPO_NUMERICO_MENOR

        lbl, fld = self.inclui_campo_numerico(nome='data', titulo='Data de Emissão', conteudo='nfse.data_hora_emissao_formatada', top=0.8*cm, left=15.4*cm, width=4*cm, margem_direita=True)
        fld.style = DADO_CAMPO_NUMERICO_MENOR

        lbl, fld = self.inclui_campo_numerico(nome='codigo_verificacao', titulo='Código de verificação', conteudo='nfse.codigo_verificacao', top=1.6*cm, left=15.4*cm, width=4*cm, margem_direita=True)
        fld.style = DADO_CAMPO_NUMERICO_MENOR

        img = LogoPrefeitura()
        img.top = 7
        img.left = 9
        #
        # Tamanhos equilaventes, em centímetros, a 3,0 x 2,2, em 128 dpi
        # estranhamente, colocar os tamanhos em centímetros encolhe a imagem
        #
        img.width = 133
        img.height = 98
        self.elements.append(img)

        self.height = 2.4*cm


class CabecalhoRPS(BandaRelato):
    def __init__(self):
        super(CabecalhoRPS, self).__init__()
        self.elements = []

        lbl, fld = self.inclui_campo_numerico(nome='data_fato_gerador', titulo='Competência/Fato gerador', conteudo='nfse.data_hora_fato_gerador_formatada', top=0*cm, left=0*cm, width=64.66*mm)

        lbl, fld = self.inclui_campo_numerico(nome='rps_numero', titulo='Número do RPS', conteudo='nfse.rps.numero_formatado', top=0*cm, left=64.66*mm, width=64.66*mm)

        lbl, fld = self.inclui_campo_numerico(nome='nfse_substituida_numero', titulo='Número da NFS-e substituída', conteudo='nfse.nfse_substituida.numero_formatado', top=0*cm, left=(64.66*2)*mm, width=64.66*mm, margem_direita=True)

        self.height = 0.7*cm


class Prestador(BandaRelato):
    def __init__(self):
        super(Prestador, self).__init__()
        self.elements = []
        self.inclui_descritivo(nome='titulo_prestador', titulo='PRESTADOR DE SERVIÇOS', top=0.1*cm, left=0*cm, width=19.4*cm)

        # 1ª linha
        lbl, fld = self.inclui_campo(nome='prestador_nome', titulo='Razão Social/Nome', conteudo='nfse.prestador.nome', top=0.52*cm, left=0*mm, width=15.4*cm)

        lbl, fld = self.inclui_campo(nome='prestador_cnpj', titulo='CNPJ/CPF', conteudo='nfse.prestador.cnpj_cpf', top=0.52*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='prestador_endereco', titulo='Endereço', conteudo='nfse.prestador.endereco_completo', top=1.32*cm, left=0*cm, width=15.4*cm)
        lbl, fld = self.inclui_campo(nome='prestador_im', titulo='Inscrição municipal', conteudo='nfse.prestador.im', top=1.32*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='prestador_bairro', titulo='Bairro', conteudo='nfse.prestador.bairro', top=2.12*cm, left=0*cm, width=4*cm)
        lbl, fld = self.inclui_campo(nome='prestador_municipio', titulo='Município', conteudo='nfse.prestador.municipio', top=2.12*cm, left=4*cm, width=9.1*cm)
        lbl, fld = self.inclui_campo(nome='prestador_cep', titulo='CEP', conteudo='nfse.prestador.cep', top=2.12*cm, left=13.1*cm, width=2.3*cm, margem_direita=True)
        lbl, fld = self.inclui_campo(nome='prestador_ie', titulo='Inscrição estadual', conteudo='nfse.prestador.ie', top=2.12*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='prestador_fone', titulo='Telefone', conteudo='nfse.prestador.fone', top=2.92*cm, left=0*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo_numerico(nome='prestador_celular', titulo='Celular', conteudo='nfse.prestador.celular', top=2.92*cm, left=3.5*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo(nome='prestador_email', titulo='E-mail', conteudo='nfse.prestador.email', top=2.92*cm, left=7*cm, width=12.4*cm, margem_direita=True)

        self.height = 3.72*cm


class Tomador(BandaRelato):
    def __init__(self):
        super(Tomador, self).__init__()
        self.elements = []
        self.inclui_descritivo(nome='titulo_tomador', titulo='TOMADOR DE SERVIÇOS', top=0*cm, left=0*cm, width=19.4*cm)

        # 1ª linha
        lbl, fld = self.inclui_campo(nome='tomador_nome', titulo='Razão Social/Nome', conteudo='nfse.tomador.nome', top=0.42*cm, left=0*mm, width=15.4*cm)

        lbl, fld = self.inclui_campo(nome='tomador_cnpj', titulo='CNPJ/CPF', conteudo='nfse.tomador.cnpj_cpf', top=0.42*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='tomador_endereco', titulo='Endereço', conteudo='nfse.tomador.endereco_completo', top=1.22*cm, left=0*cm, width=15.4*cm)
        lbl, fld = self.inclui_campo(nome='tomador_im', titulo='Inscrição municipal', conteudo='nfse.tomador.im', top=1.22*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='tomador_bairro', titulo='Bairro', conteudo='nfse.tomador.bairro', top=2.02*cm, left=0*cm, width=4*cm)
        lbl, fld = self.inclui_campo(nome='tomador_municipio', titulo='Município', conteudo='nfse.tomador.municipio', top=2.02*cm, left=4*cm, width=9.1*cm)
        lbl, fld = self.inclui_campo(nome='tomador_cep', titulo='CEP', conteudo='nfse.tomador.cep', top=2.02*cm, left=13.1*cm, width=2.3*cm, margem_direita=True)
        lbl, fld = self.inclui_campo(nome='tomador_ie', titulo='Inscrição estadual', conteudo='nfse.tomador.ie', top=2.02*cm, left=15.4*cm, width=4*cm, margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='tomador_fone', titulo='Telefone', conteudo='nfse.tomador.fone', top=2.82*cm, left=0*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo_numerico(nome='tomador_celular', titulo='Celular', conteudo='nfse.tomador.celular', top=2.82*cm, left=3.5*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo(nome='tomador_email', titulo='E-mail', conteudo='nfse.tomador.email', top=2.82*cm, left=7*cm, width=12.4*cm, margem_direita=True)

        self.height = 3.62*cm


class Discriminacao(BandaRelato):
    def __init__(self):
        super(Discriminacao, self).__init__()
        self.elements = []
        self.inclui_descritivo(nome='titulo_discriminacao', titulo='DISCRIMINAÇÃO DOS SERVIÇOS', top=0*cm, left=0*cm, width=19.4*cm)

        fld = Campo(attribute_name='nfse.descricao_impressao', top=0.42*cm, left=0*cm, width=19.4*cm)
        fld.style = DADO_CAMPO_NORMAL
        fld.height = 3.98*cm
        self.elements.append(fld)

        #self.elements.append(Line(top=4.4*cm, bottom=4.4*cm, left=0*cm, right=19.4*cm, stroke_width=0.1))
        self.height = 4.4*cm


class TituloServicos(BandaRelato):
    def __init__(self):
        super(TituloServicos, self).__init__()
        self.elements = []
        lbl = self.inclui_descritivo_item(nome='', titulo='TRIBUTÁVEL', top=0*cm, left=0*cm, width=1.2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='ISS RETIDO', top=0*cm, left=1.2*cm, width=1.2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='ITEM', top=0*cm, left=2.4*cm, width=11.8*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='QUANT.', top=0*cm, left=14.2*cm, width=1.2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='VALOR UNITÁRIO', top=0*cm, left=15.4*cm, width=2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='VALOR TOTAL', top=0*cm, left=17.4*cm, width=2*cm, margem_direita=True)
        lbl.padding_top = 0.15*cm

        self.height = 0.42*cm


class DetItem(BandaRelato):
    def __init__(self):
        super(DetItem, self).__init__()
        self.elements = []
        txt = self.inclui_campo_item(nome='item', conteudo='tributavel_formatado', top=0*cm, left=0*cm, width=1.2*cm)
        txt.style = DADO_PRODUTO_CENTRALIZADO
        txt = self.inclui_campo_item(nome='item', conteudo='iss_retido_formatado', top=0*cm, left=1.2*cm, width=1.2*cm)
        txt.style = DADO_PRODUTO_CENTRALIZADO
        txt = self.inclui_campo_item(nome='item', conteudo='descricao', top=0*cm, left=2.4*cm, width=11.8*cm)
        txt = self.inclui_campo_numerico_item(nome='quantidade', conteudo='quantidade_formatado', top=0*cm, left=14.2*cm, width=1.2*cm)
        txt = self.inclui_campo_numerico_item(nome='vr_unitario', conteudo='vr_unitario_formatado', top=0*cm, left=15.4*cm, width=2*cm)
        txt = self.inclui_campo_numerico_item(nome='vr_total', conteudo='vr_servico_formatado', top=0*cm, left=17.4*cm, width=2*cm, margem_direita=True)

        #self.height = 0.28*cm
        self.auto_expand_height = True


class RodapeTotais(BandaRelato):
    def __init__(self):
        super(RodapeTotais, self).__init__()
        self.elements = []

        # 1ª linha
        lbl, fld = self.inclui_campo(nome='cod_servico', titulo='Código de classificação do serviço', conteudo='nfse.servico', top=0*cm, left=0*cm, width=19.4*cm)
        fld.style = {'fontName': FONTE_NORMAL, 'fontSize': FONTE_TAMANHO_7, 'leading': FONTE_TAMANHO_9}
        lbl.borders['right'] = False

        lbl, fld = self.inclui_campo_numerico(nome='vr_servico', titulo='Valor dos serviços', conteudo='nfse.valor.servico_formatado', top=0.8*cm, left=0*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_deducao', titulo='Valor da dedução', conteudo='nfse.valor.deducao_formatado', top=0.8*cm, left=4.85*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Desconto incondicionado', conteudo='nfse.valor.desconto_incondicionado_formatado', top=0.8*cm, left=9.7*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='bc_iss', titulo='Base de cálculo do ISS', conteudo='nfse.valor.bc_iss_formatado', top=0.8*cm, left=14.55*cm, width=4.85*cm, margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='al_iss', titulo='Alíquota do ISS', conteudo='nfse.valor.al_iss_formatado', top=1.6*cm, left=0*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_iss_retido', titulo='Valor do ISS', conteudo='nfse.valor.vr_iss_formatado', top=1.6*cm, left=4.85*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Valor do ISS retido', conteudo='nfse.valor.retido.iss_formatado', top=1.6*cm, left=9.7*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Desconto condicionado', conteudo='nfse.valor.desconto_condicionado_formatado', top=1.6*cm, left=14.55*cm, width=4.85*cm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_retencoes', titulo='RETENÇÕES FEDERAIS', top=2.4*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        lbl, fld = self.inclui_campo_imposto(nome='pis', titulo='nfse.valor.retido.al_pis_formatado', conteudo='nfse.valor.retido.pis_formatado', top=2.82*cm, left=0*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='cofins', titulo='nfse.valor.retido.al_cofins_formatado', conteudo='nfse.valor.retido.cofins_formatado', top=2.82*cm, left=3.23*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='inss', titulo='nfse.valor.retido.al_inss_formatado', conteudo='nfse.valor.retido.inss_formatado', top=2.82*cm, left=6.46*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='ir', titulo='nfse.valor.retido.al_ir_formatado', conteudo='nfse.valor.retido.ir_formatado', top=2.82*cm, left=9.69*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='csll', titulo='nfse.valor.retido.al_csll_formatado', conteudo='nfse.valor.retido.csll_formatado', top=2.82*cm, left=12.92*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_numerico(nome='outras_retencoes', titulo='Outras retenções', conteudo='nfse.valor.retido.outras_formatado', top=2.82*cm, left=16.15*cm, width=3.25*cm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_totais', titulo='TOTAIS', top=3.62*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        lbl, fld = self.inclui_campo_numerico(nome='vr_servico', titulo='Valor dos serviços', conteudo='nfse.valor.servico_formatado', top=4.04*cm, left=0*cm, width=64.66*mm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_liquido', titulo='Total líquido', conteudo='nfse.valor.liquido_formatado', top=4.04*cm, left=64.66*mm, width=64.66*mm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_nfse', titulo='Valor da nota', conteudo='nfse.valor.servico_formatado', top=4.04*cm, left=(64.66*2)*mm, width=64.66*mm, margem_direita=True)

        self.height = 4.82*cm


class RodapeObservacoes(BandaRelato):
    def __init__(self):
        super(RodapeObservacoes, self).__init__()
        self.elements = []

        self.inclui_descritivo(nome='titulo_outras', titulo='OUTRAS INFORMAÇÕES', top=0*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        fld = Campo(attribute_name='nfse.obs_impressao', top=0.42*cm, left=0*cm, width=19.4*cm)
        fld.style = DADO_PRODUTO
        fld.height = 4.54*cm
        self.elements.append(fld)

        #self.elements.append(Line(top=9.8*cm, bottom=9.8*cm, left=0*cm, right=19.4*cm, stroke_width=0.1))

        #fld = Relato.ObsImpressao()
        #fld.top = 9.8*cm
        #self.elements.append(fld)

        self.elements.append(BarCode(type='QR', attribute_name='nfse.link_verificacao', top=0*cm, left=16.9*cm, width=2.5*cm, height=2.5*cm))

        self.height = 4.96*cm


class Rodape(BandaRelato):
    def __init__(self):
        super(Rodape, self).__init__()
        self.elements = []

        # 1ª linha
        lbl, fld = self.inclui_campo(nome='cod_servico', titulo='Código de classificação do serviço', conteudo='nfse.servico', top=0*cm, left=0*cm, width=19.4*cm)
        fld.style = {'fontName': FONTE_NORMAL, 'fontSize': FONTE_TAMANHO_7, 'leading': FONTE_TAMANHO_9}
        lbl.borders['right'] = False

        lbl, fld = self.inclui_campo_numerico(nome='vr_servico', titulo='Valor dos serviços', conteudo='nfse.valor.servico_formatado', top=0.8*cm, left=0*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_deducao', titulo='Valor da dedução', conteudo='nfse.valor.deducao_formatado', top=0.8*cm, left=4.85*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Desconto incondicionado', conteudo='nfse.valor.desconto_incondicionado_formatado', top=0.8*cm, left=9.7*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='bc_iss', titulo='Base de cálculo do ISS', conteudo='nfse.valor.bc_iss_formatado', top=0.8*cm, left=14.55*cm, width=4.85*cm, margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='al_iss', titulo='Alíquota do ISS', conteudo='nfse.valor.al_iss_formatado', top=1.6*cm, left=0*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_iss_retido', titulo='Valor do ISS', conteudo='nfse.valor.vr_iss_formatado', top=1.6*cm, left=4.85*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Valor do ISS retido', conteudo='nfse.valor.retido.iss_formatado', top=1.6*cm, left=9.7*cm, width=4.85*cm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_desconto', titulo='Desconto condicionado', conteudo='nfse.valor.desconto_condicionado_formatado', top=1.6*cm, left=14.55*cm, width=4.85*cm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_retencoes', titulo='RETENÇÕES FEDERAIS', top=2.4*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        lbl, fld = self.inclui_campo_imposto(nome='pis', titulo='nfse.valor.retido.al_pis_formatado', conteudo='nfse.valor.retido.pis_formatado', top=2.82*cm, left=0*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='cofins', titulo='nfse.valor.retido.al_cofins_formatado', conteudo='nfse.valor.retido.cofins_formatado', top=2.82*cm, left=3.23*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='inss', titulo='nfse.valor.retido.al_inss_formatado', conteudo='nfse.valor.retido.inss_formatado', top=2.82*cm, left=6.46*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='ir', titulo='nfse.valor.retido.al_ir_formatado', conteudo='nfse.valor.retido.ir_formatado', top=2.82*cm, left=9.69*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_imposto(nome='csll', titulo='nfse.valor.retido.al_csll_formatado', conteudo='nfse.valor.retido.csll_formatado', top=2.82*cm, left=12.92*cm, width=3.23*cm)
        lbl, fld = self.inclui_campo_numerico(nome='outras_retencoes', titulo='Outras retenções', conteudo='nfse.valor.retido.outras_formatado', top=2.82*cm, left=16.15*cm, width=3.25*cm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_totais', titulo='TOTAIS', top=3.62*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        lbl, fld = self.inclui_campo_numerico(nome='vr_servico', titulo='Valor dos serviços', conteudo='nfse.valor.servico_formatado', top=4.04*cm, left=0*cm, width=64.66*mm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_liquido', titulo='Total líquido', conteudo='nfse.valor.liquido_formatado', top=4.04*cm, left=64.66*mm, width=64.66*mm)
        lbl, fld = self.inclui_campo_numerico(nome='vr_nfse', titulo='Valor da nota', conteudo='nfse.valor.servico_formatado', top=4.04*cm, left=(64.66*2)*mm, width=64.66*mm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_outras', titulo='OUTRAS INFORMAÇÕES', top=4.82*cm, left=0*cm, width=19.4*cm, height=1.32*cm)

        fld = Campo(attribute_name='nfse.obs_impressao', top=5.26*cm, left=0*cm, width=19.4*cm)
        fld.style = DADO_PRODUTO
        fld.height = 4.54*cm
        self.elements.append(fld)

        self.elements.append(Line(top=9.8*cm, bottom=9.8*cm, left=0*cm, right=19.4*cm, stroke_width=0.1))

        fld = Relato.ObsImpressao()
        fld.top = 9.8*cm
        self.elements.append(fld)

        self.elements.append(BarCode(type='QR', attribute_name='nfse.link_verificacao', top=5.26*cm, left=16.9*cm, width=2.5*cm, height=2.5*cm))

        self.height = 10*cm


def ajusta_terco(elementos):
    sobe_topo = 0
    alturas = {}
    topos = {}

    for i in range(len(elementos)):
        elemento = elementos[i]

        if elemento.top not in topos:
            if elemento.top == 0:
                topos[elemento.top] = 0*cm
            elif elemento.height == 0.52 * cm:
                topos[elemento.top] = elemento.top - sobe_topo + 0.23 * cm
            elif elemento.height == 0.42 * cm:
                topos[elemento.top] = elemento.top - sobe_topo
                sobe_topo -= 0.23 * cm
            else:
                topos[elemento.top] = elemento.top - sobe_topo
                sobe_topo += 0.23 * cm

        elemento.top = topos[elemento.top]

        if elemento.height == 0.52 * cm:
            alturas[elemento.height] = elemento.height - 0.01 * cm
        elif elemento.height == 0.28 * cm:
            alturas[elemento.height] = elemento.height
        elif elemento.height not in alturas:
            alturas[elemento.height] = elemento.height - 0.23 * cm

        elemento.height = alturas[elemento.height]

        estilo = copy(elemento.style)

        if not isinstance(elemento, (LabelMargemEsquerda, LabelMargemDireita)):
            if estilo['fontSize'] == FONTE_TAMANHO_5:
                pass
            elif estilo['fontSize'] == FONTE_TAMANHO_7:
                elemento.padding_top = elemento.padding_top - 0.07 * cm
            elif estilo['fontSize'] == FONTE_TAMANHO_10:
                elemento.padding_top = elemento.padding_top - 0.13 * cm

        estilo['fontSize'] = estilo['fontSize'] - 1.5
        if 'leading' in estilo:
            estilo['leading'] = estilo['leading'] - 1.5
        elemento.style = estilo

    return elementos, sobe_topo


def gera_nfse_pdf(lista_nfses, arquivo_unico=False):
    impresso_nfse = ImpressoNFSe()

    #
    # Prepara as notas
    #
    if arquivo_unico:
        pdf_unico = PdfFileWriter()

    for nfse in lista_nfses:
        for item in nfse.itens:
            item.nfse = nfse

        #nfse.obs_impressao = nfse.obs_impressao.replace('<br/>', ' | ')

        if hasattr(nfse, 'boleto'):
            impresso_nfse.band_page_footer = FichaCompensacaoTerco()
            impresso_nfse.band_page_footer.child_bands = [RodapeTotais(), RodapeObservacoes()]
            for banda in impresso_nfse.band_page_header.child_bands:
                banda.elements, altura_menos = ajusta_terco(banda.elements)
                banda.height -= altura_menos
            impresso_nfse.band_page_footer.child_bands[1].elements[1].attribute_name = 'nfse.obs_impressao_curta'
            impresso_nfse.band_page_footer.child_bands[1].elements[1].width = 17 * cm
            impresso_nfse.band_page_footer.child_bands[1].height = 2 * cm

            impresso_nfse.band_page_header = Cabecalho()
            impresso_nfse.band_page_header.child_bands = [CabecalhoRPS(), Prestador(), Tomador(), Discriminacao(), TituloServicos()]
            for banda in impresso_nfse.band_page_header.child_bands[:-1]:
                banda.elements, altura_menos = ajusta_terco(banda.elements)
                banda.height -= altura_menos
            impresso_nfse.band_page_header.child_bands[3].auto_expand_height = True

        else:
            impresso_nfse.band_page_footer = Rodape()

        nfse_pdf = StringIO()
        impresso_nfse.queryset = nfse.itens
        impresso_nfse.generate_by(PDFGenerator, filename=nfse_pdf)

        pdf = nfse_pdf.getvalue()
        nfse_pdf.close()
        nfse.pdf = pdf

        if arquivo_unico:
            arq_pdf = StringIO()
            arq_pdf.write(pdf)
            separa_paginas = PdfFileReader(arq_pdf)
            for i in range(separa_paginas.numPages):
                pdf_unico.addPage(separa_paginas.getPage(i))

    if arquivo_unico:
        arq_pdf = StringIO()
        pdf_unico.write(arq_pdf)
        arq_pdf.seek(0)
        pdf = arq_pdf.read()
        return pdf

    return lista_nfses
