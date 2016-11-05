# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia
from copy import copy
from collections import OrderedDict



class finan_tabela_venda(osv.Model):
    _name = 'finan.tabela.venda'
    _recname = 'nome'

    _columns = {
        'nome': fields.char(u'Descrição', size=60, select=True),
        'condicao_ids': fields.one2many('finan.contrato.condicao', 'tabela_venda_id', u'Condições de pagamento'),
    }


finan_tabela_venda()


class finan_contrato_condicao(osv.Model):
    _description = u'Condições do contrato'
    _name = 'finan.contrato.condicao'
    _order = 'ordem'

    _columns = {
        'tabela_venda_id': fields.many2one('finan.tabela.venda', u'Tabela de venda', ondelete='cascade'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'ordem': fields.integer(u'Ordem'),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição', ondelete='restrict'),
        'vezes': fields.integer(u'Vezes/parcelas'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict'),
        'currency_id': fields.many2one('res.currency', u'Correção', ondelete='restrict'),
        'valor_principal': fields.float(u'Valor principal'),
        'valor_entrada': fields.float(u'Valor entrada'),
        'data_inicio': fields.date(u'Data de início da cobrança'),
        'parcela_ids': fields.one2many('finan.contrato.condicao.parcela', 'condicao_id', u'Parcelas'),
    }

    _defaults = {
        'ordem': 1,
        'currency_id': 6,
    }

    def create(self, cr, uid, dados, context={}):
        res = super(finan_contrato_condicao, self).create(cr, uid, dados, context)

        self.pool.get('finan.contrato.condicao').gera_parcelas(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if 'ordem' in dados:
            del dados['ordem']

        res = super(finan_contrato_condicao, self).write(cr, uid, ids, dados, context)

        self.pool.get('finan.contrato.condicao').gera_parcelas(cr, uid, ids, context=context)

        return res

    #_sql_constraints = [
        #('contrato_ordem_unique', 'unique(contrato_id, ordem)',
            #u'O número do contrato/parcelamento não pode se repetir!'),
    #]

    def gera_parcelas(self, cr, uid, ids, context={}):
        parcela_pool = self.pool.get('finan.contrato.condicao.parcela')

        for condpag_obj in self.browse(cr, uid, ids, context=context):
            if condpag_obj.tabela_venda_id:
                continue
            
            lista_vencimentos = condpag_obj.payment_term_id.calcula(D(condpag_obj.valor_principal), data_base=condpag_obj.data_inicio, entrada=D(condpag_obj.valor_entrada or 0))

            print(lista_vencimentos)

            for parcela_obj in condpag_obj.parcela_ids:
                parcela_obj.unlink()

            i = 1
            for parcela in lista_vencimentos:
                dados = {
                    'condicao_id': condpag_obj.id,
                    'parcela': i,
                    'data_vencimento': parcela.data,
                    'valor': parcela.valor,
                    'juros': parcela.juros,
                    'amortizacao': parcela.amortizacao,
                    'divida_amortizada': parcela.divida_amortizada,
                    'saldo_devedor': parcela.saldo_devedor,
                }

                parcela_pool.create(cr, uid, dados)
                i += 1

        return True


finan_contrato_condicao()


class finan_contrato_condicao_parcela(osv.Model):
    _description = u'Parcela das condições do contrato'
    _name = 'finan.contrato.condicao.parcela'
    _order =  'condicao_id, data_vencimento, parcela'

    _columns = {
        'condicao_id': fields.many2one('finan.contrato.condicao', u'Condição', required=True, ondelete="cascade"),
        'parcela': fields.integer(u'Parcela'),
        'data_vencimento': fields.date(u'Vencimento'),
        'valor': fields.float(u'Valor'),
        'juros': fields.float(u'Juros'),
        'amortizacao': fields.float(u'Amortização'),
        'divida_amortizada': fields.float(u'Dívida amortizada'),
        'saldo_devedor': fields.float(u'Saldo devedor'),
    }


finan_contrato_condicao_parcela()