# -*- coding: utf-8 -*-

from osv import fields, osv


class account_payment_term(osv.osv):
    _inherit = 'account.payment.term'

    _columns = {
        'bloqueia_pagamento': fields.boolean(u'Bloqueia pagamento no financeiro?'),
    }


account_payment_term()
