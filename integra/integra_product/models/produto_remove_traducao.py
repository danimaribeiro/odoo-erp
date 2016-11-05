# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class product_uom_categ(orm.Model):
    _name = 'product.uom.categ'
    _inherit = 'product.uom.categ'

    _columns = {
        'name': fields.char(u'Nome', size=64, required=True, translate=False, select=True),
    }


product_uom_categ()


class product_uom(orm.Model):
    _name = 'product.uom'
    _inherit = 'product.uom'

    _columns = {
        'name': fields.char(u'Nome', size=64, required=True, translate=False, select=True),
    }


product_uom()


class product_ul(orm.Model):
    _name = "product.ul"
    _inherit = "product.ul"

    _columns = {
        'name' : fields.char(u'Nome', size=64, select=True, required=True, translate=False),
    }


product_ul()


class product_category(orm.Model):
    _name = "product.category"
    _inherit = "product.category"

    _columns = {
        'name': fields.char(u'Nome', size=64, required=True, translate=False, select=True),
    }


product_category()


class product_template(orm.Model):
    _name = "product.template"
    _inherit = "product.template"

    _columns = {
        'name': fields.char(u'Nome', size=120, required=True, translate=False, select=True),
        'description': fields.text(u'Descrição', translate=False),
        'description_purchase': fields.text(u'Descrição na compra', translate=False),
        'description_sale': fields.text(u'Descrição na venda', translate=False),
    }


product_template()
