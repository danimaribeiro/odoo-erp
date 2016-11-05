# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import fields, osv


class account_payment_term(osv.osv):
    _name = 'account.payment.term'
    _inherit = 'account.payment.term'
    #_description = u'Condições de pagamento'

    _columns = {
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
    }


account_payment_term()
