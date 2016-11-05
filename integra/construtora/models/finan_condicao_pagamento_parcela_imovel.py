# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia, data_por_extenso, mes_passado
from copy import copy
from collections import OrderedDict
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import formata_data, idade_meses
from pybrasil.valor import formata_valor, numero_por_extenso_unidade, numero_por_extenso
import numpy
import regex
from finan_condicao_pagamento_imovel import *


class finan_contrato_condicao_parcela(osv.Model):
    _description = u'Parcela das condições do contrato'
    _name = 'finan.contrato.condicao.parcela'
    _order =  'contrato_id, condicao_id, data_vencimento, parcela'

    _columns = {
        'condicao_id': fields.many2one('finan.contrato.condicao', u'Condição', required=True, ondelete="cascade"),
        'condicao_taxa_juros': fields.related('condicao_id', 'taxa_juros', type='float', string=u'Taxa de juros'),
        'condicao_tipo_taxa': fields.related('condicao_id', 'tipo_taxa', type='selection', string=u'Tipo de juros', selection=TIPO_TAXA),
        'condicao_taxa_seguro': fields.related('condicao_id', 'taxa_seguro', type='float', string=u'Taxa de seguro'),

        'contrato_id': fields.related('condicao_id', 'contrato_id', type='many2one', relation='finan.contrato', string=u'Contrato', store=True),
        'parcela': fields.integer(u'Parcela'),
        'data_vencimento': fields.date(u'Vencimento'),
        'valor': fields.float(u'Valor'),
        'valor_seguro': fields.float(u'Seguro'),
        'valor_administracao': fields.float(u'Adm.'),
        'valor_original': fields.float(u'Valor original'),
        'valor_capital': fields.float(u'Capital'),
        'valor_capital_juros': fields.float(u'Capital + Juros'),
        'valor_capital_juros_correcao': fields.float(u'Capital + Juros + Correção'),
        'juros': fields.float(u'Juros'),
        'correcao': fields.float(u'Correção'),
        'indice': fields.float(u'Índice'),
        'amortizacao': fields.float(u'Amortização'),
        'divida_amortizada': fields.float(u'Dívida amortizada'),
        'saldo_devedor': fields.float(u'Saldo devedor'),
        'obs': fields.char(u'Obs.', size=60, select=True),
        'entrada': fields.boolean(u'Entrada?'),

        #
        # Correção monetária
        #
        'currency_id': fields.many2one('res.currency', u'Ìndice', ondelete='restrict'),
        'data_base': fields.date(u'Data base'),
        'tipo_mes_correcao': fields.selection(TIPO_MES, u'Período de correção'),

        #
        # Demonstração da atualização da parcela
        #
        'atualizacao_ids': fields.one2many('finan.contrato.condicao.parcela.atualizacao', 'parcela_id', u'Atualização'),


        #
        # Cobrança
        #
        'res_partner_address_id': fields.many2one('res.partner.address', u'Endereço de cobrança', ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', ondelete='restrict'),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio', ondelete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),

        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro'),
    }

    def atualiza_valor(self, cr, uid, ids, context={}):
        currency_pool = self.pool.get('res.currency')
        atualizacao_pool = self.pool.get('finan.contrato.condicao.parcela.atualizacao')

        print('entrou aqui')

        for parcela_obj in self.browse(cr, uid, ids):
            #
            # Parcelas cuja condição de pagamento não tenha taxa de juros, ou que o índice de correção seja REAIS, não serão atualizadas
            #
            if (not parcela_obj.condicao_id.currency_id) or (parcela_obj.condicao_id.currency_id.id == 6) or (not parcela_obj.condicao_id.tipo_taxa):
                continue

            meses = idade_meses_sem_dia(parcela_obj.data_vencimento, hoje())

            if meses == len(parcela_obj.atualizacao_ids):
                continue

            meses -= len(parcela_obj.atualizacao_ids)

            #
            # Se é a primeira atualização
            #
            if len(parcela_obj.atualizacao_ids) == 0:
                parcela_atual_obj = parcela_obj

            else:
                parcela_atual_obj = parcela_obj.atualizacao_ids[0]

            for mes in range(meses):
                data_atualizacao = parse_datetime(parcela_atual_obj.data_vencimento) + relativedelta(months=1)
                dias_atraso = data_atualizacao - parse_datetime(parcela_atual_obj.data_vencimento)
                dias_atraso = dias_atraso.days

                dados = {
                    'contrato_id': parcela_atual_obj.contrato_id.id,
                    'condicao_id': parcela_atual_obj.condicao_id.id,
                    'parcela': parcela_atual_obj.parcela,
                    'currency_id': parcela_atual_obj.currency_id.id,
                    'tipo_mes_correcao': parcela_atual_obj.tipo_mes_correcao,
                    'carteira_id': parcela_atual_obj.carteira_id.id,

                    'parcela_id': parcela_obj.id,
                    'atraso': dias_atraso,
                    'data_vencimento': str(data_atualizacao)[:10],
                    'porcentagem_juros': parcela_atual_obj.condicao_id.carteira_id.porcentagem_juros,
                    'porcentagem_multa': parcela_atual_obj.condicao_id.carteira_id.porcentagem_multa,
                    'valor_capital': parcela_atual_obj.valor_capital,
                    'valor_original': parcela_atual_obj.valor,
                    'valor_seguro_original': parcela_atual_obj.valor_seguro,
                }

                valor = D(parcela_atual_obj.valor or 0)

                #
                # Removemos o seguro e a multa da parcela anterior
                #
                if hasattr(parcela_atual_obj, 'valor_multa_carteira'):
                    valor -= D(getattr(parcela_atual_obj, 'valor_multa_carteira', 0) or 0)
                    valor -= D(parcela_atual_obj.valor_seguro or 0)

                dados['valor_original'] = valor

                #
                # Multa da carteira
                #
                valor_multa_carteira = D(parcela_atual_obj.valor or 0)
                valor_multa_carteira *= D(parcela_atual_obj.condicao_id.carteira_id.porcentagem_multa or 0) / D(100)
                valor_multa_carteira = valor_multa_carteira.quantize(D('0.01'))
                dados['valor_multa_carteira'] = valor_multa_carteira

                valor += valor_multa_carteira

                #
                # Juros da carteira
                #
                valor_juros_carteira = D(parcela_atual_obj.valor or 0)
                valor_juros_carteira *= D(parcela_atual_obj.condicao_id.carteira_id.porcentagem_juros or 0) / D(100)
                valor_juros_carteira = valor_juros_carteira.quantize(D('0.01'))
                valor_juros_carteira *= dias_atraso
                valor_juros_carteira = valor_juros_carteira.quantize(D('0.01'))
                dados['valor_juros_carteira'] = valor_juros_carteira

                valor += valor_juros_carteira

                #
                # Juros SACOC
                #
                if parcela_atual_obj.condicao_id.tipo_taxa == '3':
                    valor_juros_sacoc = D(parcela_atual_obj.valor_capital or 0)
                    valor_juros_sacoc *= D(parcela_atual_obj.condicao_id.taxa_juros_sacoc or 0) / D(100)
                    valor_juros_sacoc /= D(30)
                    #valor_juros_sacoc = valor_juros_sacoc.quantize(D('0.01'))
                    valor_juros_sacoc *= dias_atraso
                    valor_juros_sacoc = valor_juros_sacoc.quantize(D('0.01'))
                    dados['valor_juros_sacoc'] = valor_juros_sacoc
                    valor += valor_juros_sacoc

                #
                # Correção pelo índice
                #
                indice_obj = currency_pool.browse(cr, uid, parcela_atual_obj.currency_id.id, context={'date': str(ultimo_dia_mes(mes_passado(data_atualizacao)))})
                indice = D(indice_obj.rate or 0)
                dados['indice'] = indice

                valor_parcela = D(parcela_atual_obj.valor_capital or 0)
                valor_parcela = currency_pool.converte(cr, uid, REAIS_ID, parcela_atual_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(data_atualizacao)))})
                #valor_parcela = currency_pool.compute(cr, uid, REAIS_ID, parcela_atual_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(data_atualizacao)))})

                correcao = valor_parcela - D(parcela_atual_obj.valor_capital or 0)
                dados['correcao'] = correcao
                valor += correcao

                #
                # Seguro atualizado
                #
                valor_seguro = D(parcela_atual_obj.valor_seguro or 0)
                valor_seguro += valor * D(parcela_atual_obj.condicao_id.taxa_seguro or 0) / D(100)
                valor_seguro = valor_seguro.quantize(D('0.01'))
                dados['valor_seguro'] = valor_seguro
                valor += valor_seguro

                dados['valor'] = valor

                atualizacao_id = atualizacao_pool.create(cr, uid, dados)
                parcela_atual_obj = atualizacao_pool.browse(cr, uid, atualizacao_id)

        return False


finan_contrato_condicao_parcela()



class finan_contrato_condicao_parcela_atualizacao(osv.Model):
    _description = u'Parcela das condições do contrato'
    _name = 'finan.contrato.condicao.parcela.atualizacao'
    _inherit = 'finan.contrato.condicao.parcela'
    _order =  'parcela_id, data_vencimento'

    _columns = {
        'parcela_id': fields.many2one('finan.contrato.condicao.parcela', u'Parcela original', ondelete='cascade'),
        'porcentagem_juros': fields.float(u'% de Juros por dia', digits=(18,8)),
        'porcentagem_multa': fields.float(u'% de Multa por atraso', digits=(5,2)),
        'valor_multa_carteira': fields.float(u'Multa da carteira', digits=(18, 2)),
        'valor_juros_carteira': fields.float(u'Juros da carteira', digits=(18, 2)),
        'atraso': fields.integer(u'Atraso em dias'),
        'valor_juros_sacoc': fields.float(u'Juros SACOC', digits=(18, 2)),
        'valor_seguro_original': fields.float(u'Seguro anterior', digits=(18, 2)),
    }


finan_contrato_condicao_parcela_atualizacao()
