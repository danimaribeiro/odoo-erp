# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
from sped.models.fields import CampoDinheiro
from finan.models.sql_finan_saldo import SQL_VIEW_GERAL


class finan_saldo_bancario_hoje(osv.Model):
    _description = u'Saldos bancários hoje'
    _name = 'finan.saldo_bancario_hoje'
    _sql = SQL_VIEW_GERAL
    _auto = False

    _columns = {
        #
        # Data e valor de caixa - movimentação do banco
        #
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária'),
        'company_id': fields.related('res_partner_bank_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=True),
        'nome': fields.related('res_partner_bank_id', 'bank_name', type='char', string=u'Banco'),
        'agencia': fields.related('res_partner_bank_id', 'agencia', type='char', string=u'Agência'),
        'conta': fields.related('res_partner_bank_id', 'acc_number', type='char', string=u'Conta'),
        'saldo_anterior': CampoDinheiro(u'Saldo anterior'),
        'credito': CampoDinheiro(u'Créditos hoje'),
        'debito': CampoDinheiro(u'Débitos hoje'),
        'saldo': CampoDinheiro(u'Saldo'),
        #'tipo': fields.char(u'Tipo', size=20),
        'tipo': fields.related('res_partner_bank_id', 'tipo', type='char', string=u'Tipo', store=True),
    }


finan_saldo_bancario_hoje()
