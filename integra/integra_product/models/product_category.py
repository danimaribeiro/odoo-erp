# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from openerp import SUPERUSER_ID
#from product import product
import re


class product_category(orm.Model):
    _name = 'product.category'
    _inherit = 'product.category'
    _parent_order = 'nome_completo'
    _order = 'nome_completo'

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

############# MONTA NOME DA CATEGORIA ##################

    def monta_nome(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        nome = ''
        if conta_obj.name:
            nome = conta_obj.name

        if conta_obj.parent_id:
            nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for obj in self.browse(cr, uid, ids):
            if obj.parent_id.name:
                nome_pai = obj.parent_id.name or ''
                res.append((obj.id, nome_pai + ' - ' + self.monta_nome(cr, uid, obj.id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        #res = self.nome_get(cr, uid, ids, context=context)
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Nome Completo Categoria', store=True, select=True),
        #'product_type': product.product_template._columns['type'],
        #'supply_method': product.product_template._columns['supply_method'],
        #'procure_method': product.product_template._columns['procure_method'],
        'product_type': fields.selection(
            [
                ('product', 'Stockable Product'),
                ('consu', 'Consumable'),
                ('service', 'Service')
            ], 'Product Type', required=True,
            help="Will change the way procurements are processed. Consumable are product where you don't manage stock."),
        'procure_method': fields.selection(
            [
                ('make_to_stock', 'Make to Stock'),
                ('make_to_order', 'Make to Order')
            ], 'Procurement Method', required=True,
            help="'Make to Stock': When needed, take from the stock or wait until re-supplying. 'Make to Order': When needed, purchase or produce for the procurement request."),
        'supply_method': fields.selection(
            [
                ('produce', 'Produce'),
                ('buy', 'Buy')
            ], 'Supply method', required=True,
            help="Produce will generate production order or tasks, according to the product type. Buy will trigger purchase orders when requested."),
        'state': fields.selection(
            [
                ('', ''),
                ('draft', 'In Development'),
                ('sellable', 'Normal'),
                ('end', 'End of Lifecycle'),
                ('obsolete', 'Obsolete')
            ], 'Status',
            help="Tells the user if he can use the product or not."),
    }

    _defaults = {
        #'product_type': product.product_template._defaults['product_type'],
        #'supply_method': product.product_template._defaults['supply_method'],
        #'procure_method': product.product_template._defaults['procure_method'],
        'product_type': lambda *a: 'consu',
        'supply_method': lambda *a: 'buy',
        'procure_method': lambda *a: 'make_to_stock',
        'state': lambda *a: 'sellable',
    }

product_category()
