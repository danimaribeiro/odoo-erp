# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, osv, fields
from decimal import Decimal as D
import re


class product_category(orm.Model):
    _inherit = 'product.category'
    _description = 'Product category'

    _columns = {
        'tipo_classificacao': fields.selection([('Produto', 'Produto'), ('Metal', 'Material'), ('Cor', 'Cor')], u'Caracteristica'),
    }

product_category()


class product_product(osv.Model):
    _inherit = 'product.product'
    _rec_name = 'nome_apresentacao'


    _columns = {
        'tipo_metal_id': fields.many2one('product.category','Tipo Material', select=True),
        'tipo_cor_id': fields.many2one('product.category','Cor Material', select=True),
        'preco_venda_por_peso': fields.float(u'Preço de venda por peso'),
        'preco_custo_por_peso': fields.float(u'Preço de custo por peso'),
        'nome_apresentacao': fields.char(u'Apresentação', size=100, select=True, required=True),
        'preco_por_parcela': fields.float(u'Valor por parcela'),
        'parcelas': fields.float(u'Nº de parcelas'),
        #'preco_minimo_por_peso': fields.float(u'Preço mínimo por peso'),
    }

    _defaults = {
        'parcelas': 10,
    }


    def onchange_monta_nome(self, cr, uid, ids, name, categ_id, tipo_metal_id, tipo_cor_id, variants):
        categoria_pool = self.pool.get('product.category')
        produto_pool = self.pool.get('product.product')
        tamplate_pool = self.pool.get('product.tamplate')
        nome_apresentacao = ''
        res = []

        if categ_id:
            m_desc_1_obj = categoria_pool.browse(cr, uid, categ_id )
            res.append(m_desc_1_obj.name)

        if tipo_metal_id:
            m_desc_2_obj = categoria_pool.browse(cr, uid, tipo_metal_id)
            res.append(m_desc_2_obj.name)

        if tipo_cor_id:
            m_desc_3_obj = categoria_pool.browse(cr, uid, tipo_cor_id)
            res.append(m_desc_3_obj.name)

        if name:
            res.append(name)

        if variants:
            res.append(variants)

        nome_apresentacao = ', '.join(res)

        return {'value': {'nome_apresentacao': nome_apresentacao}}


    def onchange_weight_net(self, cr, uid, ids, weight_net, preco_venda_por_peso, preco_custo_por_peso):

        list_price = D(str(weight_net)) * D(str(preco_venda_por_peso))
        list_price = list_price.quantize(D('0.01'))

        standard_price = D(str(weight_net)) * D(str(preco_custo_por_peso))
        standard_price = standard_price.quantize(D('0.01'))

        return {'value': {'list_price': list_price, 'standard_price': standard_price}}

    def onchange_preco_venda_por_peso(self, cr, uid, ids, weight_net, preco_venda_por_peso):

        list_price = D(str(weight_net)) * D(str(preco_venda_por_peso))
        list_price = list_price.quantize(D('0.01'))

        return {'value': {'list_price': list_price}}

    def onchange_preco_custo_por_peso(self, cr, uid, ids, weight_net, preco_custo_por_peso):

        standard_price = D(str(weight_net)) * D(str(preco_custo_por_peso))
        standard_price = standard_price.quantize(D('0.01'))

        return {'value': {'standard_price': standard_price}}

    def onchange_preco_minimo_por_peso(self, cr, uid, ids, weight_net, preco_minimo_por_peso):

        preco_minimo = D(str(weight_net)) * D(str(preco_minimo_por_peso))
        preco_minimo = preco_minimo.quantize(D('0.01'))

        return {'preco_minimo': preco_minimo}

    def onchange_preco_por_parcela_parcelas(self, cr, uid, ids, preco_por_parcela, parcelas):

        list_price = D(str(preco_por_parcela)) * D(str(parcelas))
        list_price = list_price.quantize(D('0.01'))

        return {'value': {'list_price': list_price}}

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
            if code:
                name = '[%s] %s' % (code,name)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.nome_apresentacao,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.nome_apresentacao,
                          'default_code': product.default_code,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
                if len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + ['|', ('name',operator,name), ('nome_apresentacao', operator, name)], limit=(limit-len(ids)), context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

product_product()
