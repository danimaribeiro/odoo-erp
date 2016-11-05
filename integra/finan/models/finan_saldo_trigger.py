# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv


class finan_saldo_trigger_banco(osv.Model):
    _description = u'Saldo trigger banco'
    _name = 'finan.saldo_trigger_banco'
    _rec_name = 'res_partner_bank_id'

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True),
        'data': fields.date(u'Data', select=True),
        'saldo_anterior': fields.float(u'Saldo anterior'),
        'credito': fields.float(u'Créditos'),
        'debito': fields.float(u'Débitos'),
        'saldo': fields.float(u'Saldo'),
    }

    _sql_constraints = [
        ('res_partner_bank_id_data_unique', 'unique(res_partner_bank_id, data)',
            u'O banco e a data não podem se repetir!'),
    ]


finan_saldo_trigger_banco()
