# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from tools.translate import _
import netsvc
import tools
from tools import float_compare
import decimal_precision as dp
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from pybrasil.valor.decimal import Decimal as D


class stock_move(osv.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'
    _rec_name = 'descricao'

    def _get_custo_medio(self, cr, uid, ids, context={}):
        res = {}

        for move_obj in self.browse(cr, uid, ids):
            sql_saldo_anterior = """
            select
                ss.data,
                coalesce(ss.quantidade, 0) as quantidade,
                coalesce(ss.vr_total, 0) as vr_total

            from
                stock_saldo ss

            where
                ss.data < {data}
                and ss.company_id = {company_id}
                and ss.location_id = {location_id}
                and ss.product_id = {product_id}

            order by
                ss.data desc

            limit 1;
            """

            sql_movimento = """
                select
                    ees.tipo,
                    cast(ees.quantidade as varchar) as quantidade,
                    cast(ees.preco_unitario as varchar) as vr_unitario

                from
                    estoque_entrada_saida ees

                where
                        ees.location_id = {location_id}
                    and ees.company_id = {company_id}
                    and ees.product_id = {product_id}
                    and es.move_id <= {move_id}
                    {filtro_data}

                order by
                    ees.company_id,
                    ees.location_id,
                    ees.product_id,
                    ees.data,
                    ees.tipo,
                    ees.move_id;
            """

            filtro = {
                'data': move_obj.date[:10],
                'company_id': move_obj.company_id.id,
                'product_id': move_obj.product_id.id,
                'location_id': move_obj.location_id.id,
                'move_id': move_obj.id,
                'filtro_data': ''
            }

            res[move_obj.id] = D(0)

            if nome_campo == 'vr_unitario_custo_saida' or nome_campo == 'vr_total_custo_saida':
                sql_saldo_saida = sql_saldo_anterior.format(**filtro)
                cr.execute(sql_saldo_saida)
                dados = cr.fetchall()

                quantidade_estoque = D(0)
                vr_unitario = D(0)
                vr_unitario_custo = D(0)
                vr_total = D(0)

                if len(dados):
                    filtro['filtro_data'] = "and es.data > '{data}'".format(data=dados[0][0])

                    quantidade_estoque = D(dados[0][1] or 0)
                    vr_total = D(dados[0][2] or 0)

                    if quantidade_estoque > 0:
                        vr_unitario_custo = vr_total / quantidade_estoque

                sql_movimento_saida = sql_movimento.format(**filtro)
                cr.execute(sql_movimento_saida)
                dados = cr.fetchall()

                for tipo, quantidade, vr_unitario in dados:
                    quantidade = D(quantidade or 0)
                    vr_unitario = D(vr_unitario or 0)

                    #
                    # Entrada
                    #
                    if tipo == u'E':
                        quantidade_estoque += quantidade
                        #
                        # O valor do custo só é ajustado quando houver entrada
                        # com valor de custo
                        #
                        if vr_unitario_custo != 0:
                            custo_atual = vr_total

                            if quantidade_estoque > 0:
                                if vr_total > 0:
                                    custo_atual += entrada * vr_unitario_custo
                                    vr_unitario =  custo_atual / quantidade_estoque
                                else:
                                    custo_atual = entrada * vr_unitario_custo
                                    vr_unitario = vr_unitario_custo

                                vr_total = vr_unitario * quantidade_estoque

                    #
                    # Saída
                    #
                    else:
                        quantidade_estoque -= quantidade
                        vr_total = vr_unitario * quantidade_estoque
                        vr_unitario_custo = vr_unitario

                if nome_campo == 'vr_unitario_custo_saida':
                    res[move_obj.id] = vr_unitario_custo
                else:
                    res[move_obj.id] = vr_unitario_custo * D(move_obj.product_qty)

            elif nome_campo == 'vr_unitario_custo_entrada' or nome_campo == 'vr_total_custo_entrada':
                filtro['location_id'] = move_obj.location_dest_id.id

                sql_saldo_entrada = sql_saldo_anterior.format(**filtro)
                cr.execute(sql_saldo_entrada)
                dados = cr.fetchall()

                quantidade_estoque = D(0)
                vr_unitario = D(0)
                vr_unitario_custo = D(0)
                vr_total = D(0)

                if len(dados):
                    filtro['filtro_data'] = "and es.data > '{data}'".format(data=dados[0][0])

                    quantidade_estoque = D(dados[0][1] or 0)
                    vr_total = D(dados[0][2] or 0)

                    if quantidade_estoque > 0:
                        vr_unitario_custo = vr_total / quantidade_estoque

                sql_movimento_entrada = sql_movimento.format(**filtro)
                cr.execute(sql_movimento_entrada)
                dados = cr.fetchall()

                for tipo, quantidade, vr_unitario in dados:
                    quantidade = D(quantidade or 0)
                    vr_unitario = D(vr_unitario or 0)

                    #
                    # Entrada
                    #
                    if tipo == u'E':
                        quantidade_estoque += quantidade
                        #
                        # O valor do custo só é ajustado quando houver entrada
                        # com valor de custo
                        #
                        if vr_unitario_custo != 0:
                            custo_atual = vr_total

                            if quantidade_estoque > 0:
                                if vr_total > 0:
                                    custo_atual += entrada * vr_unitario_custo
                                    vr_unitario =  custo_atual / quantidade_estoque
                                else:
                                    custo_atual = entrada * vr_unitario_custo
                                    vr_unitario = vr_unitario_custo

                                vr_total = vr_unitario * quantidade_estoque

                    #
                    # Saída
                    #
                    else:
                        quantidade_estoque -= quantidade
                        vr_total = vr_unitario * quantidade_estoque
                        vr_unitario_custo = vr_unitario

                if nome_campo == 'vr_unitario_custo_saida':
                    res[move_obj.id] = vr_unitario_custo
                else:
                    res[move_obj.id] = vr_unitario_custo * D(move_obj.product_qty)

        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []

        for obj in self.browse(cr, uid, ids, context=context):
            texto = u'Qtd. ' + formata_valor(obj.product_qty or 0)

            if getattr(obj, 'purchase_line_id', False):
                texto += ' [' + obj.purchase_line_id.order_id.name +']'

            texto += ': ' + obj.location_id.name
            texto += ' > ' + obj.location_dest_id.name

            res.append((obj.id, texto))

        return res

    def _get_quantidade(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.state != 'done':
                qtd_pedida = obj.quantidade_original
                qtd_recebida = 0
                qtd_saldo = obj.product_qty

            elif obj.state == 'done':
                qtd_pedida = 0
                qtd_recebida = obj.product_qty
                qtd_saldo = 0

            if nome_campo == 'quantidade_pedida':
                res[obj.id] = qtd_pedida
            elif nome_campo == 'quantidade_recebida':
                res[obj.id] = qtd_recebida
            elif nome_campo == 'quantidade_saldo':
                res[obj.id] = qtd_saldo

        return res

    def _get_total(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            valor = D(obj.product_qty or 0)
            valor *= D(obj.price_unit or 0)

            res[obj.id] = valor

        return res

    _columns = {
        'sped_documentoitem_id': fields.many2one('sped.documentoitem', u'Item da NF', ondelete='cascade'),
        'stock_inventory_line_id': fields.many2one('stock.inventory.line', u'Item do inventário'),

        'quantidade_original': fields.float(u'Quantidade original'),
        'quantidade_pedida': fields.function(_get_quantidade, type='float', string=u'Pedida'),
        'quantidade_recebida': fields.function(_get_quantidade, type='float', string=u'Recebida'),
        'quantidade_saldo': fields.function(_get_quantidade, type='float', string=u'Saldo'),
        'valor_total': fields.function(_get_total, type='float', string=u'Total'),
        'partner_id': fields.many2one('res.partner', u'Parceiro'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato do cliente'),
        #'descricao': fields.function(_get_nome_funcao, type='char', size=256, string=u'Descrição', store=True, fnct_search=_procura_nome),

        #'name': fields.char('Name', size=250, required=True, select=True),
        #'priority': fields.selection([('0', 'Not urgent'), ('1', 'Urgent')], 'Priority'),
        #'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        #'date': fields.datetime('Date', required=True, select=True, help="Move date: scheduled date until move is done, then date of actual move processing", states={'done': [('readonly', True)]}),
        #'date_expected': fields.datetime('Scheduled Date', states={'done': [('readonly', True)]},required=True, select=True, help="Scheduled date for the processing of this move"),
        #'product_id': fields.many2one('product.product', 'Product', required=True, select=True, domain=[('type','<>','service')],states={'done': [('readonly', True)]}),

        #'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM'), required=True,states={'done': [('readonly', True)]}),
        #'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True,states={'done': [('readonly', True)]}),
        #'product_uos_qty': fields.float('Quantity (UOS)', digits_compute=dp.get_precision('Product UoM'), states={'done': [('readonly', True)]}),
        #'product_uos': fields.many2one('product.uom', 'Product UOS', states={'done': [('readonly', True)]}),
        #'product_packaging': fields.many2one('product.packaging', 'Packaging', help="It specifies attributes of packaging like type, quantity of packaging,etc."),

        #'location_id': fields.many2one('stock.location', 'Source Location', required=True, select=True,states={'done': [('readonly', True)]}, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        #'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True,states={'done': [('readonly', True)]}, select=True, help="Location where the system will stock the finished products."),
        #'address_id': fields.many2one('res.partner.address', 'Destination Address ', states={'done': [('readonly', True)]}, help="Optional address where goods are to be delivered, specifically used for allotment"),

        #'prodlot_id': fields.many2one('stock.production.lot', 'Production Lot', states={'done': [('readonly', True)]}, help="Production lot is used to put a serial number on the production", select=True),
        #'tracking_id': fields.many2one('stock.tracking', 'Pack', select=True, states={'done': [('readonly', True)]}, help="Logistical shipping unit: pallet, box, pack ..."),

        #'auto_validate': fields.boolean('Auto Validate'),

        #'move_dest_id': fields.many2one('stock.move', 'Destination Move', help="Optional: next stock move when chaining them", select=True),
        #'move_history_ids': fields.many2many('stock.move', 'stock_move_history_ids', 'parent_id', 'child_id', 'Move History (child moves)'),
        #'move_history_ids2': fields.many2many('stock.move', 'stock_move_history_ids', 'child_id', 'parent_id', 'Move History (parent moves)'),
        #'picking_id': fields.many2one('stock.picking', 'Reference', select=True,states={'done': [('readonly', True)]}),
        #'note': fields.text('Notes'),
        #'state': fields.selection([('draft', 'New'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'State', readonly=True, select=True,
              #help='When the stock move is created it is in the \'Draft\' state.\n After that, it is set to \'Not Available\' state if the scheduler did not find the products.\n When products are reserved it is set to \'Available\'.\n When the picking is done the state is \'Done\'.\
              #\nThe state is \'Waiting\' if the move is waiting for another one.'),
        #'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Account'), help="Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)"),
        #'price_currency_id': fields.many2one('res.currency', 'Currency for average price', help="Technical field used to record the currency chosen by the user during a picking confirmation (when average price costing method is used)"),
        #'company_id': fields.many2one('res.company', 'Company', required=True, select=True),
        #'partner_id': fields.related('picking_id','address_id','partner_id',type='many2one', relation="res.partner", string="Partner", store=True, select=True),
        #'backorder_id': fields.related('picking_id','backorder_id',type='many2one', relation="stock.picking", string="Back Order", select=True),
        #'origin': fields.related('picking_id','origin',type='char', size=64, relation="stock.picking", string="Origin", store=True),

        # used for colors in tree views:
        #'scrapped': fields.related('location_dest_id','scrap_location',type='boolean',relation='stock.location',string='Scrapped', readonly=True),
    }

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        if uid != 1:
            frozen_fields = set(['product_qty', 'product_uom', 'product_uos_qty', 'product_uos', 'location_id', 'location_dest_id', 'product_id'])
            for move in self.browse(cr, uid, ids, context=context):
                if move.state == 'done':
                    if frozen_fields.intersection(vals):
                        #
                        # Caso esteja sendo feita uma alteração proibida, forçamos o uso
                        # do usuário admin
                        #
                        uid = 1
                        #raise osv.except_osv(_('Operation forbidden'),
                        #                     _('Quantities, UoMs, Products and Locations cannot be modified on stock moves that have already been processed (except by the Administrator)'))

        return super(stock_move, self).write(cr, uid, ids, vals, context=context)

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial pickings and moves done.
        @param partial_datas: Dictionary containing details of partial picking
                          like partner_id, address_id, delivery_date, delivery
                          moves with product_id, product_qty, uom
        """
        res = {}
        picking_obj = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")

        if context is None:
            context = {}

        complete, too_many, too_few = [], [], []
        move_product_qty = {}
        prodlot_ids = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.state in ('done', 'cancel'):
                continue
            partial_data = partial_datas.get('move%s'%(move.id), False)
            assert partial_data, _('Missing partial picking data for move #%s') % (move.id)
            product_qty = partial_data.get('product_qty',0.0)
            move_product_qty[move.id] = product_qty
            product_uom = partial_data.get('product_uom',False)
            product_price = partial_data.get('product_price',0.0)
            product_currency = partial_data.get('product_currency',False)
            prodlot_ids[move.id] = partial_data.get('prodlot_id')
            if move.product_qty == product_qty:
                complete.append(move)
            elif move.product_qty > product_qty:
                too_few.append(move)
            else:
                move.product_qty = product_qty
                too_many.append(move)

            # Average price computation
            if (move.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
                product = product_obj.browse(cr, uid, move.product_id.id)
                move_currency_id = move.company_id.currency_id.id
                context['currency_id'] = move_currency_id
                qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
                if qty > 0:
                    new_price = currency_obj.compute(cr, uid, product_currency,
                            move_currency_id, product_price)
                    new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                            product.uom_id.id)
                    if product.qty_available <= 0:
                        new_std_price = new_price
                    else:
                        # Get the standard price
                        amount_unit = product.price_get('standard_price', context=context)[product.id]
                        new_std_price = ((amount_unit * product.qty_available)\
                            + (new_price * qty))/(product.qty_available + qty)

                    product_obj.write(cr, uid, [product.id],{'standard_price': new_std_price})

                    # Record the values that were chosen in the wizard, so they can be
                    # used for inventory valuation if real-time valuation is enabled.
                    self.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency,
                                })

        for move in too_few:
            product_qty = move_product_qty[move.id]
            if product_qty != 0:
                defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty,
                            'picking_id' : move.picking_id.id,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                            }
                prodlot_id = prodlot_ids[move.id]
                if prodlot_id:
                    defaults.update(prodlot_id=prodlot_id)
                new_move = self.copy(cr, uid, move.id, defaults)
                complete.append(self.browse(cr, uid, new_move))
            self.write(cr, uid, [move.id],
                    {
                        'product_qty' : move.product_qty - product_qty,
                        'product_uos_qty':move.product_qty - product_qty,
                    })

        print('too_many', too_many)
        for move in too_many:
            print('quantidade', move.product_qty)
            self.write(cr, uid, [move.id],
                    {
                        'product_qty': move.product_qty,
                        'product_uos_qty': move.product_qty,
                    })
            complete.append(move)

        for move in complete:
            if prodlot_ids.get(move.id):
                self.write(cr, uid, [move.id],{'prodlot_id': prodlot_ids.get(move.id)})
            self.action_done(cr, uid, [move.id], context=context)
            if move.picking_id.id:
                # TOCHECK : Done picking if all moves are done
                cr.execute("""
                    SELECT move.id FROM stock_picking pick
                    RIGHT JOIN stock_move move ON move.picking_id = pick.id AND move.state = %s
                    WHERE pick.id = %s""",
                            ('done', move.picking_id.id))
                res = cr.fetchall()
                if len(res) == len(move.picking_id.move_lines):
                    picking_obj.action_move(cr, uid, [move.picking_id.id])
                    wf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)

        #
        # Mandamos atualizar todas as linhas do picking
        #
        res = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', move.picking_id.id)])
        #res = [move.id for move in complete]
        print('retornando ', res)

        #return
        return res



stock_move()
