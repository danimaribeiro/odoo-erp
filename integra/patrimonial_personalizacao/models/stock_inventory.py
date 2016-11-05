# -*- coding: utf-8 -*-

from osv import fields, osv
from pybrasil.data import parse_datetime, formata_data
from pybrasil.base import RelatoAutomatico, gera_relatorio_pdf
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
from pybrasil.valor.decimal import Decimal as D
import base64




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



class stock_inventory(osv.osv):
    _name = "stock.inventory"
    _inherit = "stock.inventory"

    _columns = {
        'location_id': fields.many2one('stock.location', u'Local destino', select=True),
    }

    def gera_inventario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for inv_obj in self.browse(cr, uid, ids):
            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Inventário - ' + inv_obj.name + ' - ' + formata_data(parse_datetime(inv_obj.date))
            rel.colunas = [
                ['product_id.default_code', 'C', 20, u'Código', False],
                ['product_id.name' , 'C', 50, u'Produto', False],
                ['product_qty' , 'F', 5, u'Qtd.', True],
                ['vr_unitario' , 'F', 10, u'Unit.', False],
                ['vr_total' , 'F', 10, u'Valor', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(date_inicial) + u' a ' + formata_data(date_final)

            sql = u'''
            select
                sil.id
            from stock_inventory_line sil
            join product_product p on p.id = sil.product_id
            where sil.inventory_id = {inventory_id}
            order by
            cast(p.default_code as numeric);
            '''.format(inventory_id=inv_obj.id)

            cr.execute(sql)
            inv_ids = cr.fetchall()

            lista_itens = []
            for id, in inv_ids:
                lista_itens.append(id)

            itens = self.pool.get('stock.inventory.line').browse(cr, uid, lista_itens)

            pdf = gera_relatorio_pdf(rel, itens)

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.inventory'), ('res_id', '=', inv_obj.id), ('name', '=', 'inventario.pdf')])
            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': 'inventario.pdf',
                'datas_fname': 'inventario.pdf',
                'res_model': 'stock.inventory',
                'res_id': inv_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        return True


stock_inventory()
