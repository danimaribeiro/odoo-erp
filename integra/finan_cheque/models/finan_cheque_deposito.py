# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_cheque_deposito(osv.Model):
    _description = u'Depósito de Cheques'
    _name = 'finan.cheque.deposito'

    _columns = {
        'tipo': fields.selection((('D', u'Depósito'), ('E', u'Estorno')), u'Tipo', select=True),
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária atual', ondelete='restrict'),
        'res_partner_bank_creditar_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict'),
        'data': fields.date(u'Data do depósito'),
        'valor': fields.float(u'Valor total'),

        'lancamento_ids': fields.one2many('finan.lancamento', 'cheque_deposito_id', u'Lançamentos de transferência'),
        'cheque_ids': fields.many2many('finan.cheque', 'finan_cheque_deposito_cheque', 'deposito_id', 'cheque_id', string=u'Cheques'),

        'confirmado': fields.boolean(u'Confirmado?'),
        'confirmado_user_id': fields.many2one('res.users', u'Usuário', ondelete='restrict'),
        'confirmado_data': fields.datetime(u'Data'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'finan.cheque', context=context),
        'data':  fields.date.today,
    }

    def confirmar(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('finan.lancamento')

        for deposito_obj in self.browse(cr, uid, ids, context=context):
            dados_base = {
                'company_id': deposito_obj.company_id.id,
                'tipo': 'T',
                'res_partner_bank_id': deposito_obj.res_partner_bank_id.id,
                'res_partner_bank_creditar_id': deposito_obj.res_partner_bank_creditar_id.id,
                'data_quitacao': deposito_obj.data,
                'data': deposito_obj.data,
                'data_documento': deposito_obj.data,
                'cheque_deposito_id': deposito_obj.id,
            }

            valor = D(0)
            for cheque_obj in deposito_obj.cheque_ids:
                dados = {}
                dados.update(dados_base)
                dados['cheque_id'] = cheque_obj.id

                if deposito_obj.tipo == 'D':
                    dados['numero_documento'] = u'CHQD-' + cheque_obj.numero_cheque
                else:
                    dados['numero_documento'] = u'CHQE-' + cheque_obj.numero_cheque

                dados['valor_documento'] = cheque_obj.valor
                dados['valor'] = cheque_obj.valor
                valor += D(cheque_obj.valor or 0)

                lancamento_pool.create(cr, uid, dados)

                if deposito_obj.tipo == 'D':
                    dados = {
                        'situacao': 'DP',
                        'res_partner_bank_id': deposito_obj.res_partner_bank_creditar_id.id,
                    }
                else:
                    dados = {
                        'situacao': 'DF',
                        'res_partner_bank_id': deposito_obj.res_partner_bank_creditar_id.id,
                    }

                cheque_obj.write(dados)

            dados = {
                'confirmado': True,
                'confirmado_user_id': uid,
                'confirmado_data': fields.datetime.now(),
                'valor': valor,
            }

            deposito_obj.write(dados)


finan_cheque_deposito()
