# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.data import hoje


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
    }


product_product()

