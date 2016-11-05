# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_documentoitem_compra(osv.Model):
    _description = 'Itens de compras documentos SPED'
    _name = 'sped.documentoitem.compra'

    _columns = {
        'order_line_id': fields.many2one('purchase.order.line', u'Item do Pedido', ondelete='restrict'),
        'purchase_order_id': fields.related('order_line_id', 'order_id', type='many2one', relation='purchase.order', string=u'Pedido de compra', store=True, index=True, ondelete='restrict'),
        'documentoiten_id': fields.many2one('sped.documentoitem', u'item da nota', ondelete='cascade'),
        'product_id': fields.many2one('product.product', u'produto'),
        'quantidade_item': fields.float('Qtd. atendida'),
        'partner_id': fields.many2one('res.partner', u'Pagador', ondelete='restrict'),

        #
        # Campos do pedido de compra
        #
        'preco_pedido': fields.related('order_line_id', 'price_unit', type='float', relation='purchase.order.line', string=u'Preço pedido'),
        'quantidade_pedido': fields.related('order_line_id', 'product_qty', type='float', relation='purchase.order.line', string=u'Qtd. pedido'),
        'saldo_a_atender': fields.related('order_line_id', 'saldo_a_atender', type='float', relation='purchase.order.line', string=u'Saldo a atender'),
        'data_emissao': fields.datetime(u'Data de emissão'),
        'mensagem': fields.char(u'Alerta', size=60),

        #
        # Campos da nota fiscal
        #
        'documento_id': fields.related('documentoiten_id', 'documento_id', type='many2one', relation='sped.documento', string=u'Nota Fiscal')
    }

    def onchange_itempredido(self, cr, uid, ids, order_line_id, data_emissao, vr_unitario, quantidade, context=None):
        valores = {}
        retorno = {'value': valores}
        if order_line_id:
            obj_pedido = self.pool.get('purchase.order.line').browse(cr, uid, order_line_id)
            valores['quantidade_item'] = quantidade
            valores['quantidade_pedido'] = obj_pedido.product_qty
            valores['saldo_a_atender'] = obj_pedido.saldo_a_atender
            valores['preco_pedido'] = obj_pedido.price_unit
            valores['alerta'] = ''

            if vr_unitario and obj_pedido.price_unit and obj_pedido.price_unit > vr_unitario:
                valores['alerta'] += 'Preço diferente!'

            if quantidade and obj_pedido.saldo_a_atender:
                if obj_pedido.saldo_a_atender > quantidade:
                    valores['alerta'] += 'Quantidade diferente!'
                else:
                    valores['quantidade_item'] = obj_pedido.saldo_a_atender

        return retorno

sped_documentoitem_compra()
