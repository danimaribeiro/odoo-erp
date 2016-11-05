# -*- encoding: utf-8 -*-


from StringIO import StringIO
from reportlab.graphics.barcode.common import I2of5
from geraldo.generators import PDFGenerator
from geraldo import Image, Label, ObjectValue, SystemField
from geraldo.utils import get_attr_value
from pybrasil.base import RelatoAutomatico, BandaRelato, cm, mm, PAISAGEM
from pybrasil.base.relato.estilo import *
from pybrasil.base.relato.relato import LabelMargemEsquerda, LabelMargemDireita, Titulo, Campo, Texto, Descritivo, CPC
from pybrasil.base.relato.registra_fontes import *
from pybrasil.valor import formata_valor
import base64


CODIGO_BANCO = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_14, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_16}
LINHA_DIGITAVEL = {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': FONTE_TAMANHO_9, 'alignment': TA_CENTER, 'leading': FONTE_TAMANHO_11}
RODAPE = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_RIGHT}
RODAPE_DATA = {'fontName': FONTE_DEJAVU_SANS, 'fontSize': 8, 'alignment': TA_LEFT}

ESTILO = {
    'CABECALHO_TITULO': {'fontName': FONTE_DEJAVU_SANS_NEGRITO, 'fontSize': 14, 'alignment': TA_CENTER},
    #'CABECALHO_NORMAL': {'fontName': 'Gentium', 'fontSize': 12, 'alignment': TA_RIGHT},
    #'CABECALHO_DATA':   {'fontName': 'Gentium Italic', 'fontSize': 8, 'alignment': TA_RIGHT},

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
    def __init__(self, *args, **kwargs):
        super(Cabecalho, self).__init__(*args, **kwargs)
        self.elements = []

        #
        # 1ª linha
        #
        img = LogoBanco()
        img.top = 0.1 * cm
        img.left = 0.1 * cm
        self.elements.append(img)

        fld = Campo(attribute_name='company_id.partner_id.razao_social', top=0 * cm, left=4.5 * cm, width=1.4 * cm, height=1 * cm)
        self.elements.append(fld)
        fld = Campo(attribute_name='company_id.partner_id.cnpj_cpf', top=0.5 * cm, left=4.5 * cm, width=1.4 * cm, height=1 * cm)
        self.elements.append(fld)
        fld = SystemField(top=1 * cm, left=0, width=19 * cm, height=1 * cm, expression=u'%(report_title)s')
        fld.style = ESTILO['CABECALHO_TITULO']
        self.elements.append(fld)



        #elements = [
            #SystemField(expression=u'%(report_title)s', left=0 * cm, top=1.0 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_TITULO']),
            #SystemField(expression=u'Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_NORMAL']),
            #SystemField(expression=u'%(now:%A, %d/%m/%Y, %H:%M:%S)s', top=0.65 * cm, right=0.125 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_DATA']),
            #Label(text=u'', name='usuario', left=0 * cm, top=1.5 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_NORMAL']),
            #Label(text=u'', name='filial', left=0 * cm, top=1.95 * cm, width=BAND_WIDTH, style=ESTILO['CABECALHO_NORMAL']),
        #]

        #fld.style = CODIGO_BANCO
        #fld.padding_top = 0.2 * cm
        #lbl, fld = self.inclui_texto(nome='', titulo='', texto='Arquivo de retorno de cobrança', top=0 * cm, left=5.2 * cm, width=20.5 * cm, margem_direita=True, height=1 * cm)
        #fld.style = LINHA_DIGITAVEL
        #fld.padding_top = 0.3 * cm
        #fld.padding_left = 0 * cm
        #fld.padding_right = 0 * cm

        ##
        ## 2ª linha
        ##
        #lbl, fld = self.inclui_campo(nome='', titulo='Beneficiário', conteudo='beneficiario.nome', top=1 * cm, left=0 * cm, width=12.95 * cm)

        #lbl, fld = self.inclui_campo(nome='', titulo='CNPJ', conteudo='beneficiario.cnpj_cpf', top=1 * cm, left=12.95 * cm, width=4.25 * cm, margem_direita=True)

        #lbl, fld = self.inclui_campo_numerico(nome='', titulo='Agência/código do beneficiário', conteudo='beneficiario.agencia_codigo_beneficiario', top=1 * cm, left=17.2 * cm, width=4.25 * cm, margem_direita=True)
        #lbl, fld = self.inclui_campo_numerico(nome='', titulo='Agência/conta', conteudo='beneficiario.agencia_conta', top=1 * cm, left=21.45 * cm, width=4.25 * cm, margem_direita=True)

        ###
        ### 3ª linha
        ###
        ##lbl, fld = self.inclui_campo(nome='', titulo='Beneficiário', conteudo='beneficiario.nome', top=1.8 * cm, left=0 * cm, width=12.75 * cm)


        ###
        ### 4ª linha
        ###
        ##lbl, fld = self.inclui_campo(nome='', titulo='Data do documento', conteudo='documento.data_formatada', top=2.6 * cm, left=0 * cm, width=3.1875 * cm)
        ##lbl, fld = self.inclui_campo(nome='', titulo='Nº do documento', conteudo='documento.numero', top=2.6 * cm, left=3.1875 * cm, width=3.1875 * cm)
        ##lbl, fld = self.inclui_campo(nome='', titulo='Espécie do documento', conteudo='documento.especie', top=2.6 * cm, left=6.375 * cm, width=2.1875 * cm)
        ##fld.style = DADO_CAMPO_CENTRALIZADO
        ##lbl, fld = self.inclui_campo(nome='', titulo='Aceite', conteudo='aceite', top=2.6 * cm, left=8.5625 * cm, width=1 * cm)
        ##fld.style = DADO_CAMPO_CENTRALIZADO
        ##lbl, fld = self.inclui_campo(nome='', titulo='Data do processamento', conteudo='data_processamento_formatada', top=2.6 * cm, left=9.5625 * cm, width=3.1875 * cm)

        ##lbl, fld = self.inclui_campo_numerico(nome='', titulo='Carteira/nosso número', conteudo='carteira_nosso_numero', top=2.6 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ###
        ### 5ª linha
        ###
        ##lbl, txt = self.inclui_texto(nome='', titulo='Uso do banco', texto='', top=3.4 * cm, left=0 * cm, width=3.1875 * cm)
        ##lbl, fld = self.inclui_campo(nome='', titulo='Carteira', conteudo='banco.carteira', top=3.4 * cm, left=3.1875 * cm, width=1 * cm)
        ##fld.style = DADO_CAMPO_CENTRALIZADO
        ##lbl, fld = self.inclui_campo(nome='', titulo='Espécie da moeda', conteudo='especie', top=3.4 * cm, left=4.1875 * cm, width=2.1875 * cm)
        ##fld.style = DADO_CAMPO_CENTRALIZADO
        ##lbl, txt = self.inclui_texto(nome='', titulo='Quantidade', texto='', top=3.4 * cm, left=6.375 * cm, width=3.1875 * cm)
        ##lbl, txt = self.inclui_texto(nome='', titulo='Valor', texto='', top=3.4 * cm, left=9.5625 * cm, width=3.1875 * cm)

        ##lbl, fld = self.inclui_campo_numerico(nome='', titulo='(=) Valor do documento', conteudo='documento.valor_formatado', top=3.4 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ###
        ### 6ª a 10ª linha
        ###
        ##lbl, fld = self.inclui_campo(nome='instrucao', titulo='Instruções (todas as informações deste boleto são de exclusiva responsabilidade do beneficiário)', conteudo='instrucoes_impressao', top=4.2 * cm, left=0 * cm, width=12.75 * cm, height=4 * cm)
        ##lbl, txt = self.inclui_texto(nome='', titulo='(-) Desconto/abatimento', texto='', top=4.2 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        ##lbl, txt = self.inclui_texto(nome='', titulo='(-) Outras deduções', texto='', top=5 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        ##lbl, txt = self.inclui_texto(nome='', titulo='(+) Mora/multa', texto='', top=5.8 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        ##lbl, txt = self.inclui_texto(nome='', titulo='(+) Outros acréscimos', texto='', top=6.6 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)
        ##lbl, txt = self.inclui_texto(nome='', titulo='(=) Valor cobrado', texto='', top=7.4 * cm, left=12.75 * cm, width=4.25 * cm, margem_direita=True)

        ###
        ### 11ª linha
        ###
        ##lbl, fld = self.inclui_campo(nome='', titulo='Pagador', conteudo='pagador.impressao', top=8.2 * cm, left=0 * cm, width=12.75 * cm, height=1.8 * cm)
        ##lbl.borders['right'] = False
        ##lbl.borders['left'] = False
        ##lbl, fld = self.inclui_campo(nome='', titulo='CNPJ/CPF', conteudo='pagador.cnpj_cpf', top=8.2 * cm, left=12.75 * cm, width=4.25 * cm, height=1.8 * cm)
        ##lbl.borders['right'] = False
        ##lbl.borders['left'] = False

        ##lbl, txt = self.inclui_texto(nome='', titulo='Autenticação mecânica/ficha de compensação', texto='', top=10 * cm, left=12 * cm, width=5 * cm)
        ##lbl.borders = False

        ##codigo_barras = BarCode(type='I2of5', attribute_name='codigo_barras', top=10.35 * cm, left=0 * cm, height=1.3 * cm, aditional_barcode_params={'ratio': 3, 'bearers': 0, 'quiet': 0, 'checksum': 0, 'barWidth': 0.25 * mm})

        ##self.elements.append(codigo_barras)

        self.height = 1.8 * cm


class Rodape(BandaRelato):
    height = 0.5 * cm
    borders = {'top': True, 'bottom': False}
    borders_stroke_width = {'top': 0.1, 'right': 0.1, 'bottom': 0.1, 'left': 0.1}
    elements = [
        SystemField(expression=u'%(now:Impresso por ERP Integra em %A, %e de %B de %Y, %H:%M:%S)s', top=0.125 * cm, left=0.125 * cm, width=19 * cm, style=RODAPE_DATA),
        SystemField(expression=u'%(report_title)s ― Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, width=19 * cm, style=RODAPE),
    ]


class ImpressoOS(RelatoAutomatico):
    def __init__(self, *args, **kwargs):
        super(ImpressoOS, self).__init__(*args, **kwargs)
        largura, altura = self.page_size
        self.page_size = largura, int(altura / 2.0)
        self.margin_top = 1 * cm
        self.margin_bottom = 1 * cm
        self.margin_left = 1 * cm
        self.margin_right = 1 * cm
        self.largura_maxima = (largura - (2 * cm)) /  cm

        self.title = 'Ordem de Servico'
        self.author = 'ERP Integra'

        self.band_page_header = Cabecalho()
        #self.band_page_header.child_bands = [self.band_titulos]
        self.band_page_footer = Rodape()

        colunas = [
            ['product_id.default_code',   'C', 10, u'Código', False],
            ['product_id.name' ,       'C', 40, u'Descrição', False],
            ['product_uom_qty',        'F',  5, u'Quant', True],
            ['price_unit',             'F', 10, u'Unitário', True],
            ['vr_total_margem_desconto', 'F',  10, u'Total', True],
        ]

        self.monta_detalhe_automatico(colunas)
        #self.monta_grupos(grupos)




def gera_impresso_os(self, cr, uid, ped_id):
    if not ped_id:
        return

    ped_pool = self.pool.get('sale.order')
    ped_obj = self.browse(cr, uid, ped_id)

    impresso = ImpressoOS()

    for item_obj in ped_obj.order_line:
        item_obj.ped_obj = ped_obj

    retorno_pdf = StringIO()

    #titulo = impresso.band_page_header.elements[5]
    #titulo.text = 'Arquivo de retorno de cobrança nº ' + formata_valor(retorno.sequencia, casas_decimais=0) + ' - ' + retorno.data_hora.strftime('%d/%m/%Y')
    #impresso_retorno.title = titulo.text

    impresso.queryset = ped_obj.order_line
    impresso.generate_by(PDFGenerator, filename=retorno_pdf)

    pdf = retorno_pdf.getvalue()

    nome_os = 'os_' + ped_obj.name + '_' + ped_obj.date_order + '.pdf'

    attachment_pool = self.pool.get('ir.attachment')
    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', ped_obj.id), ('name', '=', nome_os)])
    #
    # Apaga os boletos anteriores com o mesmo nome
    #
    attachment_pool.unlink(cr, uid, attachment_ids)

    dados = {
        'datas': base64.encodestring(pdf),
        'name': nome_os,
        'datas_fname': nome_os,
        'res_model': 'sale.order',
        'res_id': ped_obj.id,
        'file_type': 'application/pdf',
    }
    attachment_pool.create(cr, uid, dados)

    retorno_pdf.close()

    return pdf

