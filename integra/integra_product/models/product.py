# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from openerp import SUPERUSER_ID
#from product import product
import re


def is_pair(x):
    return not x%2


def check_ean(eancode):
    if not eancode:
        return True
    if len(eancode) <> 13:
        return False
    try:
        int(eancode)
    except:
        return False
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    reversevalue = eanvalue[::-1]
    finalean=reversevalue[1:]

    for i in range(len(finalean)):
        if is_pair(i):
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10

    if check != int(eancode[-1]):
        return False
    return True


class product_product(orm.Model):
    _inherit = "product.product"
    _description = "Product"

    _columns = {
        'currency_id': fields.many2one('res.currency', u'Moeda'),
        'variants': fields.char(u'Marca', size=60, select=True),
    }

    def onchange_categ_id(self, cr, uid, ids, categ_id):
        res = {}

        if not categ_id:
            return {'type': False, 'procure_method': False, 'supply_method': False}

        categ_obj = self.pool.get('product.category').browse(cr, uid, categ_id)

        res = {
            'type': categ_obj.product_type,
            'procure_method': categ_obj.procure_method,
            'supply_method': categ_obj.supply_method,
            'state': categ_obj.state,
        }

        return {'value': res}

    def create(self, cr, uid, dados, context=None):
        #
        # Substitui os espaços inseparáveis por espaços normais
        #
        if 'default_code' in dados and dados['default_code']:
            dados['default_code'] = dados['default_code'].replace(u' ', u' ')

        if 'name' in dados and dados['name']:
            dados['name'] = dados['name'].replace(u' ', u' ')

        res = super(product_product, self).create(cr, uid, dados, context)

        #
        # Corrige os nomes dos produtos com (copy) (copy)
        #
        cr.execute('''
            begin;
            UPDATE product_template pt
            SET name=pp.name_template
            FROM product_product pp
            WHERE pt.id = pp.product_tmpl_id and pt.name != pp.name_template;
            commit work;
        ''')

        #
        # Ajustando o default_code com o próprio ID do produto
        #
        for prod_obj in self.browse(cr, uid, [res]):
            if not prod_obj.default_code:
                cr.execute(u"update product_product set default_code='{produto_id}' where id = {produto_id};".format(produto_id=str(prod_obj.id).zfill(5)))


        return res

    def write(self, cr, uid, ids, dados, context=None):
        #
        # Substitui os espaços inseparáveis por espaços normais
        #
        if 'default_code' in dados and dados['default_code']:
            dados['default_code'] = dados['default_code'].replace(u' ', u' ')

        if 'name' in dados and dados['name']:
            dados['name'] = dados['name'].replace(u' ', u' ')

        res = super(product_product, self).write(cr, uid, ids, dados, context)

        #
        # Corrige os nomes dos produtos com (copy) (copy)
        #
        cr.execute('''
            begin;
            UPDATE product_template pt
            SET name=pp.name_template
            FROM product_product pp
            WHERE pt.id = pp.product_tmpl_id and pt.name != pp.name_template;
            commit work;
        ''')

        #
        # Ajustando o default_code com o próprio ID do produto
        #
        for prod_obj in self.browse(cr, uid, ids):
            if not prod_obj.default_code:
                cr.execute(u"update product_product set default_code='{produto_id}' where id = {produto_id};".format(produto_id=str(prod_obj.id).zfill(5)))

        return res

    def on_change_type(self, cr, uid, ids, tipo):
        res = {}

        if not tipo or tipo != 'service':
            return {}

        res = {
            'procure_method': 'make_to_order',
            'supply_method': 'produce',
        }

        return {'value': res}

    def copy(self, cr, uid, id, default, context={}):
        default['default_code'] = False
        default['groups_id'] = False

        res = super(product_product, self).copy(cr, uid, id, default, context=context)

        print(res)

        return res

    def name_search(self, cr, uid, name='', args=[], operator='ilike', context={}, limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            ids = self.search(cr, uid, [
                '|', '|', '|',
                ('default_code', 'ilike', name),
                ('ean13', '=', name),
                ('name', 'ilike', name),
                ('variants', 'ilike', name),
                ] + args, limit=limit, context=context)


            #ids = self.search(cr, user, [('default_code', '=', name)] + args, limit=limit, context=context)

            #if not ids:
                #ids = self.search(cr, user, [('ean13', '=', name)] + args, limit=limit, context=context)

            #if not ids:
                ## Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                ## on a database with thousands of matching products, due to the huge merge+unique needed for the
                ## OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                ## Performing a quick memory merge of ids in Python will give much better performance
                #ids = set()
                #ids.update(self.search(cr, user, args + [('default_code', operator, name)], limit=limit, context=context))

                #if len(ids) < limit:
                    ## we may underrun the limit because of dupes in the results, that's fine
                    #ids.update(self.search(cr, user, args + ['|', ('name', operator, name), ('variants', operator, name)], limit=(limit-len(ids)), context=context))

                #ids = list(ids)

            #if not ids:
                #ptrn = re.compile('(\[(.*?)\])')
                #res = ptrn.search(name)

                #if res:
                    #ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)

        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)

        result = self.name_get(cr, uid, ids, context=context)

        return result

    def _check_ean_key(self, cr, uid, ids, context=None):
        for product in self.browse(cr, uid, ids, context=context):
            res = check_ean(product.ean13)

            if not res:
                raise osv.except_osv(u'Erro!', u'Código de barras incorreto para o produto código {codigo}!'.format(codigo=product.default_code))

        return res


product_product()
