# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.data import parse_datetime, formata_data


class caixa_caixa(orm.Model):
    _name = 'caixa.caixa'
    _description = 'Caixas'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome', size=30, select=True, required=True),
        'company_id': fields.many2one('res.company', u'Empresa', required=True),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária', required=True, select=True),
    }


caixa_caixa()
