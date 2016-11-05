# -*- coding: utf-8 -*-


from osv import fields, osv
from integra_sesmt.constante_sesmt import *


class product_product(osv.Model):
    _inherit = 'product.product'

    _columns = {
        'ca': fields.char(u'Certificado de aprovação', size=6, select=True),
        'data_validade_ca': fields.date(u'Validade do CA'),
    }


product_product()
