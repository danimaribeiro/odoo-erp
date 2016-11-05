# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from openerp import SUPERUSER_ID
#from product import product
import re


class product_template(orm.Model):
    _inherit = 'product.template'
    _description = 'Product Template'

    def _check_uom_category(self, cursor, user, ids, context=None):
        #
        # id da categoria de medidas de serviços
        #
        cursor.execute("select id from product_uom_categ where name = 'Working Time';")
        categ_servico_ids = [x[0] for x in cursor.fetchall()]

        if categ_servico_ids:
            categ_servico_id = categ_servico_ids[0]
        else:
            categ_servico_id = False

        #
        # Se o tipo do produto for serviço, e a unidade de medida não for tempo de trabalho
        #
        for produto in self.browse(cursor, user, ids, context=context):
            if produto.type == 'service' and produto.uom_id.category_id.id != categ_servico_id:
                return False

        return True

    _constraints = [
        #(_check_uom_category, u'Erro: serviços devem ter unidade de medida da categoria Tempo de trabalho.', ['uom_id']),
    ]


product_template()
