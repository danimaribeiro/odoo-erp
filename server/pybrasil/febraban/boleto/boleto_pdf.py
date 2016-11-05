# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
from reportlab.graphics.barcode.common import I2of5
from geraldo.generators import PDFGenerator
from geraldo.barcodes import BarCode
from geraldo import Image, Label, ObjectValue
from geraldo.utils import get_attr_value
from ...base import Relato, BandaRelato, cm, mm
from ...base.relato.estilo import *
from ...base.relato.relato import LabelMargemEsquerda, LabelMargemDireita, Titulo, Campo, Texto, Descritivo
from ...base.relato.registra_fontes import *
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
        if hasattr(self, 'instance') and get_attr_value(self.instance, 'banco.arquivo_logo'):
            nome_arq_logo = get_attr_value(self.instance, 'banco.arquivo_logo')

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


class FichaCompensacao(BandaRelato):
    def __init__(self, *args, **kwargs):
        super(FichaCompensacao, self).__init__(*args, **kwargs)
        self.elements = []

        #
        # 1ª linha
        #
        img = LogoBanco()
        img.top = 0.1 * cm
        img.left = 0.1 * cm
        self.elements.append(img)

        lbl, txt = self.inclui_texto(nome='logo', titulo='', texto=u'', top=0 * cm, left=0 * cm, width=3.2 * cm, height=1 * cm)

        lbl, fld = self.inclui_campo(nome='codigo_banco', titulo='', conteudo='banco.codigo_digito', top=0 * cm, left=3.2 * cm, width=2 * cm, height=1 * cm)
        fld.style = CODIGO_BANCO
        fld.padding_top = 0.2 * cm
        lbl, fld = self.inclui_campo(nome='linha_digitavel', titulo='', conteudo='linha_digitavel', top=0 * cm, left=5.2 * cm, width=11.8 * cm, margem_direita=True, height=1 * cm)
        fld.style = LINHA_DIGITAVEL
        fld.padding_top = 0.3 * cm
        fld.padding_left = 0 * cm
        fld.padding_right = 0 * cm

        #
        # 2ª linha
        #
        topo = 1
        lbl, fld = self.inclui_campo(nome='local_pagamento', titulo='Local de pagamento', conteudo='local_pagamento', top=topo * cm, left=0 * cm, width=12.75 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='data_vencimento', titulo='Data de vencimento', conteudo='data_vencimento_formatada', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        fld.style = DADO_CAMPO_NUMERICO_NEGRITO

        #
        # 3ª linha
        #
        topo = 1.8
        lbl, fld = self.inclui_campo(nome='beneficiario_nome', titulo='Beneficiário', conteudo='beneficiario.nome', top=topo * cm, left=0 * cm, width=8.75 * cm)
        lbl, fld = self.inclui_campo_numerico(nome='beneficiario_cnpj', titulo='CNPJ/CPF', conteudo='beneficiario.cnpj_cpf', top=topo * cm, left=8.75 * cm, width=3.5 * cm, margem_direita=True)
        lbl, fld = self.inclui_campo_numerico(nome='agencia_codigo', titulo='Agência/código do beneficiário', conteudo='imprime_agencia_conta', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        #
        # 4ª linha
        #
        topo = 2.6
        lbl, fld = self.inclui_campo(nome='beneficiario_endereco', titulo='Endereço do beneficiário', conteudo='beneficiario.endereco_completo_uma_linha', top=topo * cm, left=0 * cm, width=17 * cm, margem_direita=True)
        lbl.borders = {'top': False, 'right': False, 'bottom': 0.1, 'left': False}
        fld.borders = {'top': 0.1, 'right': False, 'bottom': False, 'left': False}

        #
        # 5ª linha
        #
        topo = 3.4
        lbl, fld = self.inclui_campo(nome='data_documento', titulo='Data do documento', conteudo='documento.data_formatada', top=topo * cm, left=0 * cm, width=2.1875 * cm)
        lbl, fld = self.inclui_campo(nome='numero_documento', titulo='Nº do documento', conteudo='documento.numero', top=topo * cm, left=2.1875 * cm, width=6.4375 * cm)

        lbl, fld = self.inclui_campo(nome='especie_documento', titulo='Espécie do doc.', conteudo='documento.especie', top=topo * cm, left=8.675 * cm, width=1.1875 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='aceite', titulo='Aceite', conteudo='aceite', top=topo * cm, left=9.9625 * cm, width=0.6 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='data_processamento', titulo='Data do processamento', conteudo='data_processamento_formatada', top=topo * cm, left=10.5625 * cm, width=2.1875 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='nosso_numero', titulo='Nosso número', conteudo='imprime_carteira_nosso_numero', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        #
        # 6ª linha
        #
        topo = 4.2
        lbl, txt = self.inclui_texto(nome='uso_banco', titulo='Uso do banco', texto='', top=topo * cm, left=0 * cm, width=3.1875 * cm)
        lbl, fld = self.inclui_campo(nome='carteira', titulo='Carteira', conteudo='imprime_carteira', top=topo * cm, left=3.1875 * cm, width=1 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, fld = self.inclui_campo(nome='especie', titulo='Espécie moeda', conteudo='especie', top=topo * cm, left=4.1875 * cm, width=2.1875 * cm)
        fld.style = DADO_CAMPO_CENTRALIZADO
        lbl, txt = self.inclui_texto(nome='quantidade', titulo='Quantidade moeda', texto='', top=topo * cm, left=6.375 * cm, width=3.1875 * cm)
        lbl, txt = self.inclui_texto(nome='valor', titulo='Valor', texto='', top=topo * cm, left=9.5625 * cm, width=3.1875 * cm)

        lbl, fld = self.inclui_campo_numerico(nome='valor_documento', titulo='(=) Valor do documento', conteudo='documento.valor_formatado', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        #
        # 7ª a 10ª linha
        #
        topo = 5
        lbl, fld = self.inclui_campo(nome='instrucao', titulo='Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)', conteudo='instrucoes_impressao', top=topo * cm, left=0 * cm, width=12.75 * cm, height=3.43 * cm)
        lbl, txt = self.inclui_campo_numerico(nome='desconto', conteudo='imprime_desconto_formatado', titulo='(-) Desconto/abatimento', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        topo = 5.8
        #lbl, txt = self.inclui_campo_numerico(nome='outras_deducoes', conteudo='imprime_outras_deducoes_formatado', titulo='(-) Outras deduções', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        lbl, txt = self.inclui_campo_numerico(nome='juros_multa', conteudo='imprime_juros_multa_formatado', titulo='(+) Juros/multa', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        topo = 6.6
        lbl, txt = self.inclui_campo_numerico(nome='outros_ascrescimos', conteudo='imprime_outros_acrescimos_formatado', titulo='(+) Outros acréscimos', top=6.6 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        topo = 7.4
        #topo = 8.2
        lbl, txt = self.inclui_campo_numerico(nome='valor_cobrado', conteudo='imprime_valor_cobrado_formatado', titulo='(=) Valor cobrado', top=topo * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        #
        # 11ª linha
        #
        topo = 8.2
        lbl, fld = self.inclui_campo(nome='pagador_nome', titulo='Pagador', conteudo='pagador.impressao', top=topo * cm, left=0 * cm, width=12.75 * cm, height=1.8 * cm)
        lbl.borders['right'] = False
        lbl.borders['left'] = False
        lbl, fld = self.inclui_campo(nome='pagador_cnpj', titulo='CNPJ/CPF', conteudo='pagador.cnpj_cpf', top=topo * cm, left=12.75 * cm, width=4.25 * cm, height=1.8 * cm)
        lbl.borders['right'] = False
        lbl.borders['left'] = False

        topo = 10
        lbl, txt = self.inclui_texto(nome='autenticacao', titulo='Autenticação mecânica/ficha de compensação', texto='', top=topo * cm, left=12 * cm, width=5 * cm)
        lbl.borders = False

        topo = 10.35
        codigo_barras = BarCode(type='I2of5', attribute_name='codigo_barras', top=topo * cm, left=0 * cm, height=1.3 * cm, aditional_barcode_params={'ratio': 3, 'bearers': 0, 'quiet': 0, 'checksum': 0, 'barWidth': 0.25 * mm})

        self.elements.append(codigo_barras)

        self.height = 12 * cm


class ReciboPagador(BandaRelato):
    def __init__(self, *args, **kwargs):
        super(ReciboPagador, self).__init__(*args, **kwargs)
        self.elements = []

        lbl, txt = self.inclui_texto(nome='', titulo='', texto='Recibo do Pagador', top=0 * cm, left=0 * cm, width=17 * cm)
        lbl.borders = False
        txt.style = DESCRITIVO_DANFE

        self.height = 1 * cm


class FichaCaixa(ReciboPagador):
    def __init__(self, *args, **kwargs):
        super(FichaCaixa, self).__init__(*args, **kwargs)
        self.elements[1].text = 'Ficha de Caixa'


class ImpressoBoleto(Relato):
    def __init__(self, *args, **kwargs):
        super(ImpressoBoleto, self).__init__(*args, **kwargs)
        self.additional_fonts[FONTE_DEJAVU_SANS_MONO] = LISTA_FONTES_DEJAVU_SANS_MONO
        self.margin_bottom = 0.5 * cm

        titulo_recibo_pagador = ReciboPagador()

        recibo_pagador = FichaCompensacao()
        recibo_pagador.find_by_name('lbl_instrucao').text = 'Descrição'
        recibo_pagador.find_by_name('fld_instrucao').attribute_name = 'descricao_impressao'
        recibo_pagador.elements.pop(len(recibo_pagador.elements) - 1)
        recibo_pagador.height += 2.20 * cm

        ficha_compensacao = FichaCompensacao()

        self.band_detail = titulo_recibo_pagador
        self.band_detail.child_bands = [recibo_pagador, ficha_compensacao]


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


class ImpressoBoleto3Partes(ImpressoBoleto):
    def __init__(self, *args, **kwargs):
        super(ImpressoBoleto3Partes, self).__init__(*args, **kwargs)
        self.margin_top = 0.5 * cm

        titulo_recibo_pagador = ReciboPagador()
        titulo_recibo_pagador.height = 0.8 * cm

        titulo_ficha_caixa = FichaCaixa()
        titulo_ficha_caixa.height = 0.8 * cm

        recibo_pagador = FichaCompensacaoTerco()
        recibo_pagador.find_by_name('lbl_instrucao').text = 'Descrição'
        recibo_pagador.find_by_name('fld_instrucao').attribute_name = 'descricao_impressao'
        recibo_pagador.elements.pop(len(recibo_pagador.elements) - 1)
        recibo_pagador.height -= 1.00 * cm

        ficha_caixa = FichaCompensacaoTerco()
        ficha_caixa.elements.pop(len(ficha_caixa.elements) - 1)
        ficha_caixa.height -= 0.25 * cm

        ficha_compensacao = FichaCompensacaoTerco()

        self.band_detail = titulo_recibo_pagador
        self.band_detail.child_bands = [recibo_pagador, titulo_ficha_caixa, ficha_caixa, ficha_compensacao]


class FichaCompensacaoCarne(FichaCompensacaoTerco):
    def __init__(self, *args, **kwargs):
        super(FichaCompensacaoCarne, self).__init__(*args, **kwargs)

        PROPORCAO = 0.90

        esquerdas = {}
        larguras = {}

        for elemento in self.elements:
            if not isinstance(elemento, LogoBanco):
                if elemento.width not in larguras:
                    larguras[elemento.width] = elemento.width * PROPORCAO

                #
                # Salva também o novo ponto a esquerda do elemento ao lado
                #
                esquerdas[elemento.left + elemento.width] = elemento.left + larguras[elemento.width]

                elemento.width = larguras[elemento.width]

                if isinstance(elemento, Campo):
                    estilo = copy(elemento.style)

                    estilo['fontSize'] = estilo['fontSize'] * PROPORCAO

                    if 'leading' in estilo:
                        estilo['leading'] = estilo['leading'] * PROPORCAO

                    elemento.style = estilo

            #if elemento.left not in esquerdas:
                #esquerdas[elemento.left] = elemento.left + (5 * cm)

        for elemento in self.elements:
            if elemento.left in esquerdas:
                elemento.left = esquerdas[elemento.left]

        #
        # Ajuste fino de alguns elementos com valores muito quebrados
        #
        #
        # Linha 1
        #
        logo_banco = self.elements[0]
        logo_banco.width = 4.2 * cm
        logo_banco.height = 1 * cm
        logo_banco.top = 0.12 * cm
        logo_banco.left = 0.25 * cm

        elemento_esquerda = self.find_by_name('fld_codigo_banco')
        elemento_direita = self.find_by_name('lbl_linha_digitavel')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width
        elemento_direita = self.find_by_name('fld_linha_digitavel')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width

        #
        # Linha 4
        #
        elemento_direita = self.find_by_name('lbl_nosso_numero')
        elemento_esquerda = self.find_by_name('lbl_data_processamento')
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width
        elemento_esquerda = self.find_by_name('fld_data_processamento')
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width

        elemento_direita = elemento_esquerda
        elemento_esquerda = self.find_by_name('lbl_aceite')
        elemento_esquerda.width += 0.1 * cm
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width
        elemento_esquerda = self.find_by_name('fld_aceite')
        elemento_esquerda.width += 0.1 * cm
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width

        elemento_direita = elemento_esquerda
        elemento_esquerda = self.find_by_name('lbl_especie_documento')
        elemento_esquerda.width += 0.1 * cm
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width
        elemento_esquerda = self.find_by_name('fld_especie_documento')
        elemento_esquerda.width += 0.1 * cm
        elemento_esquerda.left = elemento_direita.left - elemento_esquerda.width

        #
        # Linha 5
        #
        elemento_esquerda = self.find_by_name('fld_carteira')
        elemento_direita = self.find_by_name('lbl_especie')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width
        elemento_direita = self.find_by_name('fld_especie')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width

        elemento_esquerda = elemento_direita
        elemento_direita = self.find_by_name('lbl_quantidade')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width

        elemento_esquerda = elemento_direita
        elemento_direita = self.find_by_name('lbl_valor')
        elemento_direita.left = elemento_esquerda.left + elemento_esquerda.width

        #
        # Linha 12
        #
        elemento_esquerda = self.find_by_name('fld_pagador_cnpj')
        elemento_direita = self.find_by_name('lbl_autenticacao')
        elemento_direita.left = elemento_esquerda.left - (0.75 * cm * PROPORCAO)
        estilo = copy(elemento_direita.style)

        estilo['fontSize'] = estilo['fontSize'] * 0.95

        if 'leading' in estilo:
            estilo['leading'] = estilo['leading'] * 0.95

        elemento_direita.style = estilo

        #
        # Eliminamos os outros descontos e acréscimos
        #
        #elemento_apaga = self.find_by_name('lbl_outras_deducoes')
        #altura_tirada = elemento_apaga.height
        altura_tirada = 0

        elemento_sobe = self.find_by_name('lbl_juros_multa')
        elemento_sobe.top -= altura_tirada
        elemento_sobe = self.find_by_name('fld_juros_multa')
        elemento_sobe.top -= altura_tirada

        elemento_apaga = self.find_by_name('lbl_outros_ascrescimos')
        altura_tirada += elemento_apaga.height

        elemento_sobe = self.find_by_name('lbl_valor_cobrado')
        elemento_sobe.top -= altura_tirada
        elemento_sobe = self.find_by_name('fld_valor_cobrado')
        elemento_sobe.top -= altura_tirada

        elemento_sobe = self.find_by_name('lbl_pagador_nome')
        elemento_sobe.top -= altura_tirada
        elemento_sobe = self.find_by_name('fld_pagador_nome')
        elemento_sobe.top -= altura_tirada

        elemento_sobe = self.find_by_name('lbl_pagador_cnpj')
        elemento_sobe.top -= altura_tirada
        elemento_sobe = self.find_by_name('fld_pagador_cnpj')
        elemento_sobe.top -= altura_tirada

        elemento_sobe = self.find_by_name('lbl_autenticacao')
        elemento_sobe.top -= altura_tirada
        elemento_sobe = self.find_by_type(BarCode)[0]
        elemento_sobe.top -= altura_tirada

        elemento = self.find_by_name('lbl_instrucao')
        elemento.height -= altura_tirada
        elemento = self.find_by_name('fld_instrucao')
        elemento.height -= altura_tirada

        novos_elementos = []
        for elemento in self.elements:
            if isinstance(elemento, (LabelMargemDireita, LabelMargemEsquerda, Campo)):
                if 'outros_ascrescimos' in elemento.name or 'outras_deducoes' in elemento.name:
                    continue

            novos_elementos.append(elemento)

        self.elements = novos_elementos

        #
        # Agora, empurramos todos os elementos para a direita, para abrir espaço pro canhoto
        # Guardamos os elementos que irão compor o canhoto
        #
        canhoto = []
        canhoto.append(copy(self.elements[0]))
        canhoto.append(copy(self.elements[1]))
        canhoto.append(copy(self.elements[2]))
        canhoto.append(copy(self.elements[3]))
        canhoto[2].borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': False}

        for elemento in self.elements:
            if isinstance(elemento, (LabelMargemDireita, LabelMargemEsquerda, Campo)):
                if ('data_vencimento' in elemento.name) or \
                    ('agencia_codigo' in elemento.name) or \
                    ('nosso_numero' in elemento.name) or \
                    ('valor_documento' in elemento.name) or \
                    ('desconto' in elemento.name) or \
                    ('juros_multa' in elemento.name) or \
                    ('valor_cobrado' in elemento.name) or \
                    ('numero_documento' in elemento.name) or \
                    ('pagador_cnpj' in elemento.name):

                    canhoto.append(elemento.clone())
                    canhoto[-1].left = 0

                    if canhoto[-1].borders:
                        canhoto[-1].borders = {'top': 0.1, 'right': False, 'bottom': 0.1, 'left': False}

                    if elemento.name == 'lbl_agencia_codigo':
                        altura_primeiro = elemento.height
                        topo_primeiro = elemento.top
                        largura_primeiro = elemento.width

            elemento.left += 4.5 * cm

        novos_elementos = []
        fator_topo = 2
        for elemento in canhoto:
            if isinstance(elemento, (LabelMargemDireita, LabelMargemEsquerda, Campo)):
                if 'numero_documento' in elemento.name:
                    elemento.top = topo_primeiro
                    elemento.width = largura_primeiro

                elif 'logo' not in elemento.name and 'codigo_banco' not in elemento.name:
                    elemento.top += altura_primeiro * fator_topo

                    if 'fld_agencia_codigo' in elemento.name:
                        fator_topo = 1

                if elemento.name == 'lbl_pagador_cnpj':
                    elemento.height = altura_primeiro
                    elemento.top += altura_primeiro * 2
                    elemento.text = u'CNPJ/CPF do pagador'
                elif elemento.name == 'fld_pagador_cnpj':
                    elemento.top += altura_primeiro * 2

            novos_elementos.append(elemento)

        for elemento in self.elements:
            novos_elementos.append(elemento)

        self.elements = novos_elementos

        #
        # Por fim, ajustamos o logo e o número do banco no canhoto
        #
        logo_banco = self.elements[0]
        logo_banco.width = 3.2 * cm
        logo_banco.height = 0.80 * cm
        logo_banco.top = 0.18 * cm
        logo_banco.left = 0.095 * cm

        self.elements[1].width -= 0.85 * cm
        self.elements[2].left -= 0.85 * cm
        self.elements[3].left -= 0.85 * cm

        #
        # Agora, adiciona os últimos elementos que faltam
        #
        lbl_parcela = self.elements[8].clone()
        lbl_parcela.top -= lbl_parcela.height
        lbl_parcela.text = u'Nº da parcela'
        self.elements.append(lbl_parcela)

        fld_parcela = self.elements[9].clone()
        fld_parcela.top -= lbl_parcela.height
        fld_parcela.attribute_name = 'documento.numero_original'
        self.elements.append(fld_parcela)

        lbl_pagador = self.elements[20].clone()
        lbl_pagador.top -= lbl_pagador.height * 2
        lbl_pagador.height *= 2
        lbl_pagador.text = u'Pagador'
        self.elements.append(lbl_pagador)

        fld_pagador = self.elements[21].clone()
        fld_pagador.top -= lbl_pagador.height
        fld_pagador.height *= 2
        fld_pagador.attribute_name = 'pagador.nome'
        self.elements.append(fld_pagador)


class ImpressoBoletoCarne(ImpressoBoleto):
    def __init__(self, *args, **kwargs):
        super(ImpressoBoletoCarne, self).__init__(*args, **kwargs)
        self.margin_top = 0.5 * cm
        self.margin_left = 0.5 * cm
        self.margin_right = 0.5 * cm
        self.margin_bottom = 0.5 * cm

        ficha_compensacao = FichaCompensacaoCarne()

        self.band_detail = ficha_compensacao


def gera_boletos_pdf(lista_boletos, classe_leiaute=ImpressoBoleto3Partes):
    impresso_boleto = classe_leiaute()
    impresso_boleto.title = u'Boletos'

    boleto_pdf = StringIO()

    impresso_boleto.queryset = lista_boletos
    impresso_boleto.generate_by(PDFGenerator, filename=boleto_pdf)

    pdf = boleto_pdf.getvalue()
    boleto_pdf.close()

    return pdf
