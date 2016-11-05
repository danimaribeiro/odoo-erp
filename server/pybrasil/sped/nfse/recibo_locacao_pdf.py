# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
from geraldo.generators import PDFGenerator
from geraldo import Image, Line, BarCode
from geraldo.utils import get_attr_value
from ...base.relato import *
from ...base.relato.estilo import *
from ...base.relato.registra_fontes import *
from PyPDF2 import PdfFileWriter, PdfFileReader


MARGEM_SUPERIOR = 0.8 * cm
MARGEM_INFERIOR = 0.8 * cm
MARGEM_ESQUERDA = 0.8 * cm
MARGEM_DIREITA = 0.8 * cm


CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}


class LogoBanco(Image):
    def __init__(self, *args, **kwargs):
        super(LogoBanco, self).__init__(*args, **kwargs)
        self.cache_logo = {}

    def _get_image(self):
        try:
            import Image as PILImage
        except ImportError:
            from PIL import Image as PILImage

        if get_attr_value(self.instance, 'nfse.boleto.banco.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'nfse.boleto.banco.arquivo_logo')

            if nome_arq_logo not in self.cache_logo or not self.cache_logo[nome_arq_logo]:
                self.cache_logo[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            arq = StringIO(self.cache_logo[nome_arq_logo])
            self._image = PILImage.open(arq)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


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
        lbl, fld = self.inclui_campo(nome='', titulo='Carteira', conteudo='imprime_carteira', top=3.4 * cm, left=3.1875 * cm, width=1 * cm)
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


class ImpressoReciboLocacao(Relato):
    def __init__(self, *args, **kargs):
        super(ImpressoReciboLocacao, self).__init__(*args, **kargs)
        self.title = 'Recibo de Locação'
        self.print_if_empty = True
        self.margin_top = MARGEM_SUPERIOR
        self.margin_bottom = MARGEM_INFERIOR
        self.margin_left = MARGEM_ESQUERDA
        self.margin_right = MARGEM_DIREITA

        # Bandas e observações
        self.band_page_header = Cabecalho()
        self.band_page_header.child_bands = [Prestador(), Tomador(), Discriminacao()]
        self.band_detail = DetItem()

        self.band_page_footer = Rodape()


class LogoEmpresa(Image):
    def __init__(self, *args, **kwargs):
        super(LogoEmpresa, self).__init__(*args, **kwargs)
        self.cache_logo = {}

    def _get_image(self):
        try:
            import Image as PILImage
        except ImportError:
            from PIL import Image as PILImage

        if get_attr_value(self.instance, 'nfse.prestador.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'nfse.prestador.arquivo_logo')

            if nome_arq_logo not in self.cache_logo or not self.cache_logo[nome_arq_logo]:
                self.cache_logo[nome_arq_logo] = open(nome_arq_logo, 'rb').read()

            arq = StringIO(self.cache_logo[nome_arq_logo])
            self._image = PILImage.open(arq)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)


class Cabecalho(BandaRelato):
    def __init__(self):
        super(Cabecalho, self).__init__()
        self.elements = []

        # Quadro do emitente
        self.inclui_texto(nome='quadro_emitente', titulo='', texto='', top=0*cm, left=0*cm, width=15.4*cm, height=1.6*cm)

        txt = self.inclui_texto_sem_borda(nome='nfse', texto='Recibo de Locação', top=0.45*cm, left=0*cm, width=15.4*cm, height=0.5*cm)
        txt.style = DESCRITIVO_DANFE

        lbl, fld = self.inclui_campo_numerico(nome='numero', titulo='Número', conteudo='nfse.numero_formatado', top=0*cm, left=15.4*cm, width=4*cm, margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='data', titulo='Data', conteudo='nfse.data_emissao_formatada', top=0.8*cm, left=15.4*cm, width=4*cm, margem_direita=True)

        self.height = 1.6*cm

        img = LogoEmpresa()
        img.top = 0.1 * cm
        img.left = 0.1 * cm
        self.elements.append(img)


class Prestador(BandaRelato):
    def __init__(self):
        super(Prestador, self).__init__()
        self.elements = []
        self.inclui_descritivo(nome='titulo_prestador', titulo='LOCADOR', top=0*cm, left=0*cm, width=19.4*cm)

        # 1ª linha
        lbl, fld = self.inclui_campo(nome='prestador_nome', titulo='Razão Social/Nome', conteudo='nfse.prestador.nome', top=0.42*cm, left=0*mm, width=15.4*cm)

        lbl, fld = self.inclui_campo(nome='prestador_cnpj', titulo='CNPJ/CPF', conteudo='nfse.prestador.cnpj_cpf', top=0.42*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='prestador_endereco', titulo='Endereço', conteudo='nfse.prestador.endereco_completo', top=1.22*cm, left=0*cm, width=15.4*cm)
        lbl, fld = self.inclui_campo(nome='prestador_im', titulo='Inscrição municipal', conteudo='nfse.prestador.im', top=1.22*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo(nome='prestador_bairro', titulo='Bairro', conteudo='nfse.prestador.bairro', top=2.02*cm, left=0*cm, width=4*cm)
        lbl, fld = self.inclui_campo(nome='prestador_municipio', titulo='Município', conteudo='nfse.prestador.municipio', top=2.02*cm, left=4*cm, width=9.1*cm)
        lbl, fld = self.inclui_campo(nome='prestador_cep', titulo='CEP', conteudo='nfse.prestador.cep', top=2.02*cm, left=13.1*cm, width=2.3*cm, margem_direita=True)
        lbl, fld = self.inclui_campo(nome='prestador_ie', titulo='Inscrição estadual', conteudo='nfse.prestador.ie', top=2.02*cm, left=15.4*cm, width=4*cm,margem_direita=True)

        lbl, fld = self.inclui_campo_numerico(nome='prestador_fone', titulo='Telefone', conteudo='nfse.prestador.fone', top=2.82*cm, left=0*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo_numerico(nome='prestador_celular', titulo='Celular', conteudo='nfse.prestador.celular', top=2.82*cm, left=3.5*cm, width=3.5*cm)
        lbl, fld = self.inclui_campo(nome='prestador_email', titulo='E-mail', conteudo='nfse.prestador.email', top=2.82*cm, left=7*cm, width=12.4*cm, margem_direita=True)

        self.height = 3.62*cm


class Tomador(BandaRelato):
    def __init__(self):
        super(Tomador, self).__init__()
        self.elements = []
        self.inclui_descritivo(nome='titulo_tomador', titulo='LOCATÁRIO', top=0*cm, left=0*cm, width=19.4*cm)

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
        self.inclui_descritivo(nome='titulo_discriminacao', titulo='DISCRIMINAÇÃO DOS ITENS LOCADOS', top=0*cm, left=0*cm, width=19.4*cm)

        fld = Campo(attribute_name='nfse.descricao_impressao', top=0.42*cm, left=0*cm, width=19.4*cm)
        fld.style = DADO_CAMPO_NORMAL
        fld.height = 3.98*cm
        self.elements.append(fld)

        lbl = self.inclui_descritivo_item(nome='', titulo='ITEM', top=2.4*cm, left=0*cm, width=14.2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='QUANT.', top=2.4*cm, left=14.2*cm, width=1.2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='VALOR UNITÁRIO', top=2.4*cm, left=15.4*cm, width=2*cm)
        lbl.padding_top = 0.15*cm
        lbl = self.inclui_descritivo_item(nome='', titulo='VALOR TOTAL', top=2.4*cm, left=17.4*cm, width=2*cm, margem_direita=True)
        lbl.padding_top = 0.15*cm

        self.height = 2.82*cm


class DetItem(BandaRelato):
    def __init__(self):
        super(DetItem, self).__init__()
        self.elements = []
        txt = self.inclui_campo_item(nome='item', conteudo='descricao', top=0*cm, left=0*cm, width=14.2*cm)
        txt = self.inclui_campo_numerico_item(nome='quantidade', conteudo='quantidade_formatado', top=0*cm, left=14.2*cm, width=1.2*cm)
        txt = self.inclui_campo_numerico_item(nome='vr_unitario', conteudo='vr_unitario_formatado', top=0*cm, left=15.4*cm, width=2*cm)
        txt = self.inclui_campo_numerico_item(nome='vr_total', conteudo='vr_servico_formatado', top=0*cm, left=17.4*cm, width=2*cm, margem_direita=True)

        #self.height = 0.28*cm
        self.auto_expand_height = True


class Rodape(BandaRelato):
    def __init__(self):
        super(Rodape, self).__init__()
        self.elements = []

        self.inclui_descritivo(nome='titulo_totais', titulo='TOTAL', top=0*cm, left=0*cm, width=19.4*cm, height=0.42*cm)

        lbl, fld = self.inclui_campo(nome='vr_servico', titulo='Valor por extenso', conteudo='nfse.valor.liquido_extenso', top=0.42*cm, left=0*cm, width=16.15*cm)
        #fld.style = DADO_CAMPO_NORMAL
        lbl, fld = self.inclui_campo_numerico(nome='vr_nfse', titulo='Valor', conteudo='nfse.valor.liquido_formatado', top=0.42*cm, left=16.15*cm, width=3.25*cm, margem_direita=True)

        self.inclui_descritivo(nome='titulo_outras', titulo='OUTRAS INFORMAÇÕES', top=1.22*cm, left=0*cm, width=19.4*cm, height=0.42*cm)

        fld = Campo(attribute_name='nfse.obs_impressao', top=1.64*cm, left=0*cm, width=19.4*cm)
        fld.style = DADO_PRODUTO
        #fld.height = 3.36*cm
        fld.height = 1.36*cm
        self.elements.append(fld)

        self.height = 3*cm


def gera_recibo_locacao_pdf(lista_nfses, arquivo_unico=False, titulo_fatura=False):
    impresso_nfse = ImpressoReciboLocacao()

    if titulo_fatura:
        impresso_nfse.title = u'Fatura de Locação'
        impresso_nfse.band_page_header.elements[1].text = u'Fatura de Locação'

    #
    # Prepara as notas
    #
    if arquivo_unico:
        pdf_unico = PdfFileWriter()

    for nfse in lista_nfses:
        for item in nfse.itens:
            item.nfse = nfse

        if hasattr(nfse, 'boleto'):
            impresso_nfse.band_page_footer = FichaCompensacao()
            impresso_nfse.band_page_footer.child_bands = [Rodape()]
            #impresso_nfse.band_page_footer.height = 3*cm

        elif len(impresso_nfse.band_page_footer.child_bands) != 0:
            impresso_nfse.band_page_footer.child_bands = []
            impresso_nfse.band_page_footer.height = 125*cm

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
