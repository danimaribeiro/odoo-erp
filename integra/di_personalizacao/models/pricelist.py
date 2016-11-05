# -*- coding: utf-8 -*-

from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time
from pybrasil.valor.decimal import Decimal as D

##from _common import rounding

OUTRA_LISTA_PRECO = -1
PRECO_DO_FORNECEDOR = -2


##class price_type(osv.osv):
    ##"""
        ##The price type is used to points which field in the product form
        ##is a price and in which currency is this price expressed.
        ##When a field is a price, you can use it in pricelists to base
        ##sale and purchase prices based on some fields of the product.
    ##"""
    ##def _price_field_get(self, cr, uid, context=None):
        ##mf = self.pool.get('ir.model.fields')
        ##ids = mf.search(cr, uid, [('model','in', (('product.product'),('product.template'))), ('ttype','=','float')], context=context)
        ##res = []
        ##for field in mf.browse(cr, uid, ids, context=context):
            ##res.append((field.name, field.field_description))
        ##return res

    ##def _get_currency(self, cr, uid, ctx):
        ##comp = self.pool.get('res.users').browse(cr,uid,uid).company_id
        ##if not comp:
            ##comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
            ##comp = self.pool.get('res.company').browse(cr, uid, comp_id)
        ##return comp.currency_id.id

    ##_name = "product.price.type"
    ##_description = "Price Type"
    ##_columns = {
        ##"name" : fields.char("Price Name", size=32, required=True, translate=True, help="Name of this kind of price."),
        ##"active" : fields.boolean("Active"),
        ##"field" : fields.selection(_price_field_get, "Product Field", size=32, required=True, help="Associated field in the product form."),
        ##"currency_id" : fields.many2one('res.currency', "Currency", required=True, help="The currency the field is expressed in."),
    ##}
    ##_defaults = {
        ##"active": lambda *args: True,
        ##"currency_id": _get_currency
    ##}

##price_type()

###----------------------------------------------------------
### Price lists
###----------------------------------------------------------

##class product_pricelist_type(osv.osv):
    ##_name = "product.pricelist.type"
    ##_description = "Pricelist Type"
    ##_columns = {
        ##'name': fields.char('Name',size=64, required=True, translate=True),
        ##'key': fields.char('Key', size=64, required=True, help="Used in the code to select specific prices based on the context. Keep unchanged."),
    ##}
##product_pricelist_type()


class product_pricelist(osv.Model):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'
    _description = 'Pricelist'

    #def _pricelist_type_get(self, cr, uid, context=None):
        #pricelist_type_pool = self.pool.get('product.pricelist.type')
        #pricelist_type_ids = pricelist_type_pool.search(cr, uid, [], order='name')
        #pricelist_types = pricelist_type_pool.read(cr, uid, pricelist_type_ids, ['key','name'], context=context)

        #res = []

        #for type in pricelist_types:
            #res.append((type['key'],type['name']))

        #return res

    #_columns = {
        #'name': fields.char('Pricelist Name',size=64, required=True, translate=True),
        #'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the pricelist without removing it."),
        #'type': fields.selection(_pricelist_type_get, 'Pricelist Type', required=True),
        #'version_id': fields.one2many('product.pricelist.version', 'pricelist_id', 'Pricelist Versions'),
        #'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        #'company_id': fields.many2one('res.company', 'Company'),
    #}

    #def name_get(self, cr, uid, ids, context=None):
        #result= []
        #if not all(ids):
            #return result
        #for pl in self.browse(cr, uid, ids, context=context):
            #name = pl.name + ' ('+ pl.currency_id.name + ')'
            #result.append((pl.id,name))
        #return result


    #def _get_currency(self, cr, uid, ctx):
        #comp = self.pool.get('res.users').browse(cr, uid, uid).company_id
        #if not comp:
            #comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
            #comp = self.pool.get('res.company').browse(cr, uid, comp_id)
        #return comp.currency_id.id

    #_defaults = {
        #'active': lambda *a: 1,
        #"currency_id": _get_currency
    #}

    def price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):
        """multi products 'price_get'.
           @param pricelist_ids:
           @param products_by_qty:
           @param partner:
           @param context: {
             'date': Date of the pricelist (%Y-%m-%d),}
           @return: a dict of dict with product_id as key and a dict 'price by pricelist' as value
        """

        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_parent_category_list

        if context is None:
            context = {}

        date = time.strftime('%Y-%m-%d')
        if 'date' in context:
            date = context['date']

        currency_pool = self.pool.get('res.currency')
        product_pool = self.pool.get('product.product')
        product_template_pool = self.pool.get('product.template')
        product_category_pool = self.pool.get('product.category')
        product_uom_pool = self.pool.get('product.uom')
        supplierinfo_pool = self.pool.get('product.supplierinfo')
        price_type_pool = self.pool.get('product.price.type')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [], context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', 'in', pricelist_ids),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise osv.except_osv(_('Warning !'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_pool.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_pool.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_pool.search(cr, uid, [])
        product_categories = product_category_pool.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

                categ_id = products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                if partner:
                    partner_where = 'base <> -2 OR {partner_id} IN (SELECT name FROM product_supplierinfo WHERE product_id = {product_id}) '
                    #partner_where = 'base <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, product_id)
                else:
                    partner_where = 'base <> -2 '
                    partner_args = ()

                filtro = {
                    'categ_where': categ_where,
                    'partner_where': partner_where.format(partner_id=partner, product_id=product_id),
                    'product_tmpl_id': tmpl_id,
                    'product_id': product_id,
                    'price_version_id': pricelist_version_ids[0],
                    'qty': qty,
                }

                sql = """
                    select
                        i.id,
                        pl.currency_id

                    from
                        product_pricelist_item AS i,
                        product_pricelist_version AS v,
                        product_pricelist AS pl

                    where
                        (product_tmpl_id IS NULL OR product_tmpl_id = {product_tmpl_id})
                        AND (product_id IS NULL OR product_id = {product_id})
                        AND ({categ_where} OR (categ_id IS NULL))
                        AND ({partner_where})
                        AND price_version_id = {price_version_id}
                        AND (min_quantity IS NULL OR min_quantity <= {qty})
                        AND i.price_version_id = v.id
                        AND v.pricelist_id = pl.id
                """

                if getattr(products_dict[product_id], 'currency_id', False):
                    filtro['currency_id'] = products_dict[product_id].currency_id.id

                    sql += """
                        AND (i.currency_id IS NULL OR i.currency_id = {currency_id})
                    """
                else:
                    sql += """
                        AND (i.currency_id IS NULL OR i.currency_id = 6)
                    """

                sql += """
                    ORDER BY
                        sequence;
                """

                #print(filtro)
                sql = sql.format(**filtro)
                cr.execute(sql)
                #cr.execute(
                    #'SELECT i.id, pl.currency_id '
                    #'FROM product_pricelist_item AS i, '
                        #'product_pricelist_version AS v, product_pricelist AS pl '
                    #'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                        #'AND (product_id IS NULL OR product_id = %s) '
                        #'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                        #'AND (' + partner_where + ') '
                        #'AND price_version_id = %s '
                        #'AND (min_quantity IS NULL OR min_quantity <= %s) '
                        #'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                    #'ORDER BY sequence',
                    #(tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                #res1 = cr.dictfetchall()
                dados = cr.fetchall()

                item_ids = []
                currency_ids = []
                for iid, currency_id in dados:
                    item_ids.append(iid)
                    currency_ids.append(currency_id)

                uom_price_already_computed = False

                #print(dados, item_ids)

                for item_obj in self.pool.get('product.pricelist.item').browse(cr, 1, item_ids):
                    if item_obj.base == OUTRA_LISTA_PRECO:
                        if not item_obj.base_pricelist_id:
                            price = D(0)
                        else:
                            price_tmp = self.price_get(cr, uid,
                                    [item_obj.base_pricelist_id.id], product_id,
                                    qty, context=context)

                            price_tmp = price_tmp[item_obj.base_pricelist_id.id]
                            #ptype_src = item_obj.base_pricelist_id.currency_id.id
                            #price = currency_pool.compute(cr, uid, ptype_src, res['currency_id'], price_tmp, round=False)
                            uom_price_already_computed = True
                            price = currency_pool.compute(cr, uid, currency_ids[0], item_obj.base_pricelist_id.currency_id.id, price_tmp, round=False)
                            price = D(price)

                    elif item_obj.base == PRECO_DO_FORNECEDOR:
                        # this section could be improved by moving the queries outside the loop:
                        where = []
                        if partner:
                            where = [('name', '=', partner)]
                        sinfo = supplierinfo_pool.search(cr, uid,
                                [('product_id', '=', tmpl_id)] + where)
                        price = D(0)
                        if sinfo:
                            qty_in_product_uom = qty
                            product_default_uom = product_template_pool.read(cr, uid, [tmpl_id], ['uom_id'])[0]['uom_id'][0]
                            supplier = supplierinfo_pool.browse(cr, uid, sinfo, context=context)[0]
                            seller_uom = supplier.product_uom and supplier.product_uom.id or False
                            if seller_uom and product_default_uom and product_default_uom != seller_uom:
                                uom_price_already_computed = True
                                qty_in_product_uom = product_uom_pool._compute_qty(cr, uid, product_default_uom, qty, to_uom_id=seller_uom)
                            cr.execute('SELECT * ' \
                                    'FROM pricelist_partnerinfo ' \
                                    'WHERE suppinfo_id IN %s' \
                                        'AND min_quantity <= %s ' \
                                    'ORDER BY min_quantity DESC LIMIT 1', (tuple(sinfo),qty_in_product_uom,))
                            res2 = cr.dictfetchone()
                            if res2:
                                price = res2['price']
                    else:
                        price_type = price_type_pool.browse(cr, uid, int(item_obj.base))
                        uom_price_already_computed = True

                        price = product_pool.price_get(cr, uid, [product_id], price_type.field, context=context)[product_id]
                        produto_obj = product_pool.browse(cr, uid, product_id)
                        #
                        # Primeiro, verifica se o produto possui os preços em outra moeda
                        # e, se tiver, se é diferente da moeda da lista; se não for, não
                        # precisa converter
                        #
                        #print('moeda do produto', produto_obj.currency_id)
                        #print('moeda 1', price_type.currency_id)
                        #print('moeda 2', item_obj.price_version_id.pricelist_id.currency_id)
                        #print('preco', price, price_type.field, produto_obj.standard_price)
                        if produto_obj.currency_id and produto_obj.currency_id.id != item_obj.price_version_id.pricelist_id.currency_id:
                            price = currency_pool.compute(cr, uid, item_obj.price_version_id.pricelist_id.currency_id.id, produto_obj.currency_id.id,
                                        price, round=False, context=context)

                        #print('preco convertido', price)
                        if price_type.currency_id.id != item_obj.price_version_id.pricelist_id.currency_id.id:
                            price = currency_pool.compute(cr, uid,
                                    price_type.currency_id.id, item_obj.price_version_id.pricelist_id.currency_id.id,
                                    price, round=False, context=context)

                    if price is not False:
                        price = D(price)
                        price_limit = price

                        price_discount = D(item_obj.price_discount or 0)
                        if len(item_obj.subitem_ids) > 0:
                            price_discount = D(1)

                            #
                            # Trata os subitens
                            #
                            for subitem_obj in item_obj.subitem_ids:
                                multiplica = D(subitem_obj.multiplica or 0)
                                divide = D(subitem_obj.divide or 100)
                                price_discount *= D(1) + (multiplica / divide)

                            price_discount -= 1
                            if item_obj.price_discount != price_discount:
                                item_obj.write({'price_discount': price_discount})

                        price = price * (D(1) + price_discount)
                        #price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                        #print(D(item_obj.price_round))
                        #print(price)
                        if item_obj.price_round:
                            price = price.quantize(D(item_obj.price_round))
                        #print(price)
                        price_surcharge = D(item_obj.price_surcharge or 0)
                        price += price_surcharge

                        if item_obj.price_min_margin:
                            price = max(price, price_limit + D(item_obj.price_min_margin or 0))

                        if item_obj.price_max_margin:
                            price = min(price, price_limit + D(price_max_margin or 0))

                        #print(price)

                        break

                if price:
                    results['item_id'] = item_obj.id

                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_pool._compute_price(cr, uid, uom.id, price, context['uom'])
                        price = D(price)

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results

    #def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        #res_multi = self.price_get_multi(cr, uid, pricelist_ids=ids, products_by_qty_by_partner=[(prod_id, qty, partner)], context=context)
        #res = res_multi[prod_id]
        #res.update({'item_id': {ids[-1]: res_multi.get('item_id', ids[-1])}})
        #return res


product_pricelist()


##class product_pricelist_version(osv.osv):
    ##_name = "product.pricelist.version"
    ##_description = "Pricelist Version"
    ##_columns = {
        ##'pricelist_id': fields.many2one('product.pricelist', 'Price List',
            ##required=True, select=True, ondelete='cascade'),
        ##'name': fields.char('Name', size=64, required=True, translate=True),
        ##'active': fields.boolean('Active',
            ##help="When a version is duplicated it is set to non active, so that the " \
            ##"dates do not overlaps with original version. You should change the dates " \
            ##"and reactivate the pricelist"),
        ##'items_id': fields.one2many('product.pricelist.item',
            ##'price_version_id', 'Price List Items', required=True),
        ##'date_start': fields.date('Start Date', help="Starting date for this pricelist version to be valid."),
        ##'date_end': fields.date('End Date', help="Ending date for this pricelist version to be valid."),
        ##'company_id': fields.related('pricelist_id','company_id',type='many2one',
            ##readonly=True, relation='res.company', string='Company', store=True)
    ##}
    ##_defaults = {
        ##'active': lambda *a: 1,
    ##}

    ### We desactivate duplicated pricelists, so that dates do not overlap
    ##def copy(self, cr, uid, id, default=None, context=None):
        ##if not default: default= {}
        ##default['active'] = False
        ##return super(product_pricelist_version, self).copy(cr, uid, id, default, context)

    ##def _check_date(self, cursor, user, ids, context=None):
        ##for pricelist_version in self.browse(cursor, user, ids, context=context):
            ##if not pricelist_version.active:
                ##continue
            ##where = []
            ##if pricelist_version.date_start:
                ##where.append("((date_end>='%s') or (date_end is null))" % (pricelist_version.date_start,))
            ##if pricelist_version.date_end:
                ##where.append("((date_start<='%s') or (date_start is null))" % (pricelist_version.date_end,))

            ##cursor.execute('SELECT id ' \
                    ##'FROM product_pricelist_version ' \
                    ##'WHERE '+' and '.join(where) + (where and ' and ' or '')+
                        ##'pricelist_id = %s ' \
                        ##'AND active ' \
                        ##'AND id <> %s', (
                            ##pricelist_version.pricelist_id.id,
                            ##pricelist_version.id))
            ##if cursor.fetchall():
                ##return False
        ##return True

    ##_constraints = [
        ##(_check_date, 'You cannot have 2 pricelist versions that overlap!',
            ##['date_start', 'date_end'])
    ##]

##product_pricelist_version()


class product_pricelist_item(osv.Model):
    _name = "product.pricelist.item"
    _description = "Pricelist item"
    _order = "sequence, min_quantity desc"
    _inherit = 'product.pricelist.item'

    #def _price_field_get(self, cr, uid, context=None):
        #pt = self.pool.get('product.price.type')
        #ids = pt.search(cr, uid, [], context=context)
        #result = []
        #for line in pt.browse(cr, uid, ids, context=context):
            #result.append((line.id, line.name))

        #result.append((-1, _('Other Pricelist')))
        #result.append((-2, _('Partner section of the product form')))
        #return result

    #_defaults = {
        #'base': lambda *a: -1,
        #'min_quantity': lambda *a: 0,
        #'sequence': lambda *a: 5,
        #'price_discount': lambda *a: 0,
    #}

    #def _check_recursion(self, cr, uid, ids, context=None):
        #for obj_list in self.browse(cr, uid, ids, context=context):
            #if obj_list.base == -1:
                #main_pricelist = obj_list.price_version_id.pricelist_id.id
                #other_pricelist = obj_list.base_pricelist_id.id
                #if main_pricelist == other_pricelist:
                    #return False
        #return True

    _columns = {
        #'name': fields.char('Rule Name', size=64, help="Explicit rule name for this pricelist line."),
        'price_version_id': fields.many2one('product.pricelist.version', u'Versão da Lista de Preços', required=True, select=True, ondelete='cascade'),
        #'product_tmpl_id': fields.many2one('product.template', 'Product Template', ondelete='cascade', help="Set a template if this rule only apply to a template of product. Keep empty for all products"),
        'product_id': fields.many2one('product.product', u'Produto', ondelete='cascade', help="Set a product if this rule only apply to one product. Keep empty for all products"),
        'categ_id': fields.many2one('product.category', u'Produto Categoria', ondelete='cascade', help="Set a category of product if this rule only apply to products of a category and his children. Keep empty for all products"),
        'currency_id': fields.many2one('res.currency', u'Moeda', ondelete='cascade'),

        'min_quantity': fields.integer(u'Quantidade mínima', required=True, help="The rule only applies if the partner buys/sells more than this quantity."),
        'sequence': fields.integer(u'Sequência', required=True, help="Gives the order in which the pricelist items will be checked. The evaluation gives highest priority to lowest sequence and stops as soon as a matching item is found."),
        #'base': fields.selection(_price_field_get, u'Baseado em', required=True, size=-1, help="The mode for computing the price for this rule."),
        #'base_pricelist_id': fields.many2one('product.pricelist', u'If Other Pricelist'),

        #'price_surcharge': fields.float('Price Surcharge',
            #digits_compute= dp.get_precision('Sale Price')),
        #'price_discount': fields.float('Price Discount', digits=(16,4)),
        'price_round': fields.float(u'Arredondamento',
            digits_compute= dp.get_precision('Sale Price'),
            help="Sets the price so that it is a multiple of this value.\n" \
              "Rounding is applied after the discount and before the surcharge.\n" \
              "To have prices that end in 9.99, set rounding 10, surcharge -0.01" \
            ),
        'price_min_margin': fields.float(u'Preço mínimo',
            digits_compute= dp.get_precision('Sale Price')),
        'price_max_margin': fields.float(u'Preço máximo',
            digits_compute= dp.get_precision('Sale Price')),
        #'company_id': fields.related('price_version_id','company_id',type='many2one',
            #readonly=True, relation='res.company', string='Company', store=True),

        'subitem_ids': fields.one2many('product.pricelist.subitem', 'pricelist_item_id', u'Subitens'),
    }

    #_constraints = [
        #(_check_recursion, 'Error ! You cannot assign the Main Pricelist as Other Pricelist in PriceList Item!', ['base_pricelist_id'])
    #]

    #def product_id_change(self, cr, uid, ids, product_id, context=None):
        #if not product_id:
            #return {}
        #prod = self.pool.get('product.product').read(cr, uid, [product_id], ['code','name'])
        #if prod[0]['code']:
            #return {'value': {'name': prod[0]['code']}}
        #return {}


product_pricelist_item()


class product_pricelist_subitem(osv.Model):
    _name = 'product.pricelist.subitem'
    _description = u'Subitem da lista de preços'
    _recname = 'nome'

    _columns = {
        'pricelist_item_id': fields.many2one('product.pricelist.item', u'Item da lista de preços'),
        'nome': fields.char(u'Nome', size=30),
        'multiplica': fields.float(u'Multiplica por'),
        'divide': fields.float(u'Divide por'),
    }

    _defaults = {
        'multiplica': 100,
        'divide': 100,
    }


product_pricelist_subitem()
