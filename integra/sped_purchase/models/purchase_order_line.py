# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class purchase_order_line(osv.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

    def _get_quantidade_atendida(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            soma = D('0')

            for nf_obj in item_obj.documentoitem_compra_ids:
                soma += D(nf_obj.quantidade_item or 0)

            if nome_campo == 'quantidade_atendida':
                res[item_obj.id] = soma
            else:
                res[item_obj.id] = D(item_obj.product_qty or 0) - soma

            if item_obj.order_id.fechamento_forcado:
                res[item_obj.id] = 1

        return res

    _columns = {
        'documentoitem_compra_ids': fields.one2many('sped.documentoitem.compra','order_line_id',string=u'Item do Pedido'),
        'quantidade_atendida': fields.function(_get_quantidade_atendida, type='float', string=u'Atendida'),
        'saldo_a_atender': fields.function(_get_quantidade_atendida, type='float', string=u'Saldo'),
    }

    def name_get(self, cr, uid, ids, context={}):
        if context is None:
            context = {}

        if not len(ids):
            return []

        res = []
        for item_obj in self.browse(cr, uid, ids):
            if hasattr(item_obj, 'name'):
                nome = item_obj.name or u''

                if item_obj.order_id.name:
                    nome += ' - ' + item_obj.order_id.name or u''

                if item_obj.order_id.partner_ref:
                    nome += ' - ' + item_obj.order_id.partner_ref or u''

                nome += ' - ' + formata_valor(item_obj.product_qty or 0)

                if getattr(item_obj, 'orcamento_item_id', False):
                    nome += ' - ' + item_obj.orcamento_item_id.descricao
                elif getattr(item_obj, 'project_id', False):
                    nome += ' - ' + item_obj.project_id.name

                res.append((item_obj.id, nome))

        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            ids = self.search(cr, uid, [
                '|', '|',
                ('order_id.name', 'ilike', name),
                ('name', 'ilike', name),
                ('product_qty', '=', name),
                ] + args, limit=limit, context=context)

            if ids:
                return self.name_get(cr, uid, ids, context)


        # short-circuit ref match when possible
        #if name and operator in ('=', 'ilike', '=ilike', 'like'):
        #    ids = self.search(cr, uid, [
        #        '|', '|', '|', '|',
        #        ('ref', '=', name),
        #        '|',
        #        ('cnpj_cpf', 'like', mascara(name, u'  .   .   /    -  ')),
        #        ('cnpj_cpf', 'like', mascara(name, u'   .   .   -  ')),
        #        ('razao_social', 'like', name),
        #        ('fantasia', 'like', name),
        #        ('ref', 'like', name),
        #        ] + args, limit=limit, context=context)

        #    if ids:
        #        return self.name_get(cr, uid, ids, context)

        return super(purchase_order_line, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)


purchase_order_line()
