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
        #SystemField(expression=u'%(report_title)s ― Pág. %(page_number)d de %(page_count)d', top=0.125 * cm, right=0.125 * cm, width=19 * cm, style=RODAPE),
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
        'inventory_line_id': fields.one2many('stock.inventory.line', 'inventory_id', 'Inventories', states={'done': [('readonly', False)]}),
    }

    def gera_inventario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for inv_obj in self.browse(cr, uid, ids):
            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Inventário - ' + inv_obj.name + ' - ' + formata_data(parse_datetime(inv_obj.date))
            rel.colunas = [
                ['product_id.default_code', 'C', 15, u'Código', False],
                ['product_id.name' , 'C', 60, u'Produto', False],
                ['product_uom.name' , 'C', 5, u'UN', False],
                ['product_qty' , 'F', 5, u'Qtd.', True],
                ['vr_unitario' , 'F', 10, u'Valor.Unit.', False],
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
            p.name_template;
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

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirm the inventory and writes its finished date
        @return: True
        """
        if context is None:
            context = {}
        # to perform the correct inventory corrections we need analyze stock location by
        # location, never recursively, so we use a special context
        product_context = dict(context, compute_child=False)

        location_obj = self.pool.get('stock.location')
        for inv in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for line in inv.inventory_line_id:
                pid = line.product_id.id
                product_context.update(uom=line.product_uom.id, to_date=inv.date, date=inv.date, prodlot_id=line.prod_lot_id.id)
                amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]

                change = line.product_qty - amount
                lot_id = line.prod_lot_id.id
                if change:
                    location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                    value = {
                        'name': 'INV:' + str(line.inventory_id.id) + ':' + line.inventory_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,
                        'date': inv.date,
                        'stock_inventory_line_id': line.id,
                    }
                    if change > 0:
                        value.update( {
                            'product_qty': change,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                        })
                    else:
                        value.update( {
                            'product_qty': -change,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
                        })
                    move_ids.append(self._inventory_line_hook(cr, uid, line, value))

                    #
                    # Atualiza o custo do estoque
                    #
                    custo_pool = self.pool.get('product.custo')

                    dados = {
                        'company_id': inv.company_id.id,
                        'product_id': line.product_id.id,
                        'location_id': line.location_id.id,
                        'quantidade': line.product_qty,
                        'vr_unitario': line.vr_unitario,
                        'vr_total': line.vr_total,
                    }

                    print('dados', dados)

                    custo_ids = custo_pool.search(cr, uid, [('company_id', '=', inv.company_id.id), ('product_id', '=', line.product_id.id), ('location_id', '=', line.location_id.id)])
                    if custo_ids:
                        custo_pool.write(cr, uid, custo_ids, dados)

                    else:
                        print('criou custo')
                        custo_pool.create(cr, uid, dados)


            message = u"Inventário '%s' está concluído." % inv.name
            self.log(cr, uid, inv.id, message)
            self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)

        return True


stock_inventory()


#class stock_inventory(osv.osv):
    #_name = "stock.inventory"
    #_description = "Inventory"
    #_columns = {
        #'name': fields.char('Inventory Reference', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        #'date': fields.datetime('Creation Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        #'date_done': fields.datetime('Date done'),
        #'inventory_line_id': fields.one2many('stock.inventory.line', 'inventory_id', 'Inventories', states={'done': [('readonly', True)]}),
        #'move_ids': fields.many2many('stock.move', 'stock_inventory_move_rel', 'inventory_id', 'move_id', 'Created Moves'),
        #'state': fields.selection( (('draft', 'Draft'), ('done', 'Done'), ('confirm','Confirmed'),('cancel','Cancelled')), 'State', readonly=True, select=True),
        #'company_id': fields.many2one('res.company', 'Company', required=True, select=True, readonly=True, states={'draft':[('readonly',False)]}),

    #}
    #_defaults = {
        #'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        #'state': 'draft',
        #'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.inventory', context=c)
    #}

    #def copy_data(self, cr, uid, id, default=None, context=None):
        #if default is None:
            #default = {}
        ## force new date, date_done and move_ids on copied datas
        #default.update(date=False, date_done=False, move_ids=[])
        #copied_data = super(stock_inventory, self).copy_data(cr, uid, id, default=default, context=context)
        #copied_data.pop('date',None)
        #return copied_data

    #def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):
        #""" Creates a stock move from an inventory line
        #@param inventory_line:
        #@param move_vals:
        #@return:
        #"""
        #return self.pool.get('stock.move').create(cr, uid, move_vals)

    #def action_done(self, cr, uid, ids, context=None):
        #""" Finish the inventory
        #@return: True
        #"""
        #if context is None:
            #context = {}
        #move_obj = self.pool.get('stock.move')
        #for inv in self.browse(cr, uid, ids, context=context):
            #inventory_move_ids = [x.id for x in inv.move_ids]
            #move_obj.action_done(cr, uid, inventory_move_ids, context=context)
            ## ask 'stock.move' action done are going to change to 'date' of the move,
            ## we overwrite the date as moves must appear at the inventory date.
            #move_obj.write(cr, uid, inventory_move_ids, {'date': inv.date}, context=context)
            #self.write(cr, uid, [inv.id], {'state':'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        #return True

    #def action_confirm(self, cr, uid, ids, context=None):
        #""" Confirm the inventory and writes its finished date
        #@return: True
        #"""
        #if context is None:
            #context = {}
        ## to perform the correct inventory corrections we need analyze stock location by
        ## location, never recursively, so we use a special context
        #product_context = dict(context, compute_child=False)

        #location_obj = self.pool.get('stock.location')
        #for inv in self.browse(cr, uid, ids, context=context):
            #move_ids = []
            #for line in inv.inventory_line_id:
                #pid = line.product_id.id
                #product_context.update(uom=line.product_uom.id, to_date=inv.date, date=inv.date, prodlot_id=line.prod_lot_id.id)
                #amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]

                #change = line.product_qty - amount
                #lot_id = line.prod_lot_id.id
                #if change:
                    #location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                    #value = {
                        #'name': 'INV:' + str(line.inventory_id.id) + ':' + line.inventory_id.name,
                        #'product_id': line.product_id.id,
                        #'product_uom': line.product_uom.id,
                        #'prodlot_id': lot_id,
                        #'date': inv.date,
                    #}
                    #if change > 0:
                        #value.update( {
                            #'product_qty': change,
                            #'location_id': location_id,
                            #'location_dest_id': line.location_id.id,
                        #})
                    #else:
                        #value.update( {
                            #'product_qty': -change,
                            #'location_id': line.location_id.id,
                            #'location_dest_id': location_id,
                        #})
                    #move_ids.append(self._inventory_line_hook(cr, uid, line, value))
            #message = _("Inventory '%s' is done.") %(inv.name)
            #self.log(cr, uid, inv.id, message)
            #self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            #self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)
        #return True

    #def action_cancel_draft(self, cr, uid, ids, context=None):
        #""" Cancels the stock move and change inventory state to draft.
        #@return: True
        #"""
        #for inv in self.browse(cr, uid, ids, context=context):
            #self.pool.get('stock.move').action_cancel(cr, uid, [x.id for x in inv.move_ids], context=context)
            #self.write(cr, uid, [inv.id], {'state':'draft'}, context=context)
        #return True

    #def action_cancel_inventory(self, cr, uid, ids, context=None):
        #""" Cancels both stock move and inventory
        #@return: True
        #"""
        #move_obj = self.pool.get('stock.move')
        #account_move_obj = self.pool.get('account.move')
        #for inv in self.browse(cr, uid, ids, context=context):
            #move_obj.action_cancel(cr, uid, [x.id for x in inv.move_ids], context=context)
            #for move in inv.move_ids:
                 #account_move_ids = account_move_obj.search(cr, uid, [('name', '=', move.name)])
                 #if account_move_ids:
                     #account_move_data_l = account_move_obj.read(cr, uid, account_move_ids, ['state'], context=context)
                     #for account_move in account_move_data_l:
                         #if account_move['state'] == 'posted':
                             #raise osv.except_osv(_('UserError'),
                                                  #_('In order to cancel this inventory, you must first unpost related journal entries.'))
                         #account_move_obj.unlink(cr, uid, [account_move['id']], context=context)
            #self.write(cr, uid, [inv.id], {'state': 'cancel'}, context=context)
        #return True

#stock_inventory()

#class stock_inventory_line(osv.osv):
    #_name = "stock.inventory.line"
    #_description = "Inventory Line"
    #_rec_name = "inventory_id"
    #_columns = {
        #'inventory_id': fields.many2one('stock.inventory', 'Inventory', ondelete='cascade', select=True),
        #'location_id': fields.many2one('stock.location', 'Location', required=True),
        #'product_id': fields.many2one('product.product', 'Product', required=True, select=True),
        #'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
        #'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM')),
        #'company_id': fields.related('inventory_id','company_id',type='many2one',relation='res.company',string='Company',store=True, select=True, readonly=True),
        #'prod_lot_id': fields.many2one('stock.production.lot', 'Production Lot', domain="[('product_id','=',product_id)]"),
        #'state': fields.related('inventory_id','state',type='char',string='State',readonly=True),
    #}

    #def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        #""" Changes UoM and name if product_id changes.
        #@param location_id: Location id
        #@param product: Changed product_id
        #@param uom: UoM product
        #@return:  Dictionary of changed values
        #"""
        #if not product:
            #return {'value': {'product_qty': 0.0, 'product_uom': False}}
        #obj_product = self.pool.get('product.product').browse(cr, uid, product)
        #uom = uom or obj_product.uom_id.id
        #amount = self.pool.get('stock.location')._product_get(cr, uid, location_id, [product], {'uom': uom, 'to_date': to_date, 'compute_child': False})[product]
        #result = {'product_qty': amount, 'product_uom': uom}
        #return {'value': result}

#stock_inventory_line()
