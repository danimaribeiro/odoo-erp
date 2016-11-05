# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class purchase_order(osv.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def _invoiced_rate(self, cr, uid, ids, nome_campo, arg, context={}):
        res = {}

        for ordem_obj in self.browse(cr, uid, ids, context=context):
            qtd_total = D(0)
            qtd_atendida = D(0)

            for item_obj in ordem_obj.order_line:
                qtd_total += D(item_obj.product_qty or 0)
                qtd_atendida += D(item_obj.quantidade_atendida or 0)

            res[ordem_obj.id] = D(100)

            if qtd_total > 0 and (not ordem_obj.fechamento_forcado):
                if  qtd_total == 0 or (qtd_atendida >= qtd_total and ordem_obj.state == 'approved'):
                    ordem_obj.write({'state': 'done'})
                elif qtd_atendida < qtd_total and ordem_obj.state == 'done':
                    ordem_obj.write({'state': 'approved'})

                res[ordem_obj.id] = qtd_atendida / qtd_total * D(100)
            elif ordem_obj.fechamento_forcado:
                res[ordem_obj.id] = 100
                ordem_obj.write({'state': 'done'})

        return res

    def _shipped_rate(self, cr, uid, ids, nome_campo, arg, context={}):
        return self._invoiced_rate(cr, uid, ids, nome_campo, arg, context)

    _columns = {
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
        'shipped_rate': fields.function(_shipped_rate, string='Received', type='float'),
        'sped_documentoitem_compra_ids': fields.one2many('sped.documentoitem.compra', 'purchase_order_id', string=u'Itens recebidos'),
        'fechamento_forcado': fields.boolean(u'Fechamento forçado?'),
    }

    def encerrar_parcial(self, cr, uid, ids, context={}):
        #
        # Encerra um pedido de compra mesmo que entregue parcial, e elimina
        # os saldos que houver
        #

        for ordem_obj in self.browse(cr, uid, ids):
            movimentos_apagar_ids = []
            for picking_obj in ordem_obj.picking_ids:
                for move_obj in picking_obj.move_lines:
                    if move_obj.state not in ('done', 'cancel'):
                        if not move_obj.sped_documentoitem_id:
                            movimentos_apagar_ids.append(move_obj.id)

            self.pool.get('stock.move').unlink(cr, uid, movimentos_apagar_ids)

        for ordem_obj in self.browse(cr, uid, ids):
            movimentos_apagar_ids = []
            for picking_obj in ordem_obj.picking_ids:
                if len(picking_obj.move_lines) == 0:
                    movimentos_apagar_ids.append(picking_obj.id)

            self.pool.get('stock.picking').unlink(cr, uid, movimentos_apagar_ids)

        for ordem_obj in self.browse(cr, uid, ids):
            ordem_obj.write({'fechamento_forcado': True})
            
            for item_obj in ordem_obj.order_line:
                if item_obj.product_qty and item_obj.quantidade_atendida:
                    if item_obj.product_qty != item_obj.quantidade_atendida:
                        item_obj.write({'product_qty': item_obj.quantidade_atendida})
                else:
                    item_obj.write({'product_qty': 1, 'quantidade_atendida': 1})

        return True


purchase_order()
