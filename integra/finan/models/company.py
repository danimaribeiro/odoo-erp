# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária padrão', select=True, ondelete='restrict'),
        'porcentagem_juros': fields.float(u'% de Juros por dia'),
        'porcentagem_multa': fields.float(u'% de Multa por atraso'),
    }

    _defaults = {
        'porcentagem_juros': 0,
        'porcentagem_multa': 0,
    }


res_company()
