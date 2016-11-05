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


REAIS_ID = 6

TIPO_TAXA = [
    ('0', u'Juros simples'),
    ('1', u'Juros compostos'),
    ('2', u'Tabela price'),

    #
    # Essa SACOC é só pra Exata, pelamordedeus, não habilita isso aqui no padrão
    #
    #('3', u'Tabela SACOC'),
]

JUROS_SIMPLES = '0'
JUROS_COMPOSTOS = '1'
TABELA_PRICE = '2'
TABELA_SACOC = '3'

TIPO_MES = [
    ('001', u'A cada mês (mensal)'),
    ('002', u'A cada 2 (dois) meses'),
    ('003', u'A cada 3 (três) meses'),
    ('004', u'A cada 4 (quatro) meses'),
    ('005', u'A cada 5 (cinco) meses'),
    ('006', u'A cada 6 (seis) meses'),
    ('007', u'A cada 7 (sete) meses'),
    ('008', u'A cada 8 (oito) meses'),
    ('009', u'A cada 9 (nove) meses'),
    ('010', u'A cada 10 (dez) meses'),
    ('011', u'A cada 11 (onze) meses'),
    ('012', u'A cada ano (anual)'),
    ('024', u'A cada 2 (dois) anos'),
    ('036', u'A cada 3 (três) anos'),
    ('048', u'A cada 4 (quatro) anos'),
    ('060', u'A cada 5 (cinco) anos'),
]

TIPO_MES_DESCRICAO = dict(TIPO_MES)


class Parcela(object):
    def __init__(self, *args, **kwargs):
        self.data = kwargs.get('data', None)
        self.valor = D(kwargs.get('valor', 0))
        self.valor_seguro = D(kwargs.get('valor_seguro', 0))
        self.valor_administracao = D(kwargs.get('valor_administracao', 0))
        self.valor_original = D(kwargs.get('valor_original', 0))
        self.juros = D(kwargs.get('juros', 0))
        self.amortizacao = D(kwargs.get('amortizacao', 0))
        self.divida_amortizada = D(kwargs.get('divida_amortizada', 0))
        self.saldo_devedor = D(kwargs.get('saldo_devedor', 0))
        self.valor_capital = D(kwargs.get('valor_capital', 0))
        self.valor_capital_juros = D(kwargs.get('valor_capital_juros', 0))
        self.valor_capital_juros_correcao = D(kwargs.get('valor_capital_juros_correcao', 0))
        self.valor_original = D(kwargs.get('valor_original', 0))
        self.indice = D(kwargs.get('indice', 0))
        self.correcao = D(kwargs.get('correcao', 0))

    def __repr__(self):
        return str(self.data) + '; ' + str(self.valor)


##class finan_tabela_venda(osv.Model):
    ##_name = 'finan.tabela.venda'
    ##_recname = 'nome'

    ##_columns = {
        ##'nome': fields.char(u'Descrição', size=60, select=True),
        ##'condicao_ids': fields.one2many('finan.contrato.condicao', 'contrato_id', u'Condições de pagamento'),
    ##}


##finan_tabela_venda()


class finan_contrato_condicao(osv.Model):
    _description = u'Condições do contrato'
    _name = 'finan.contrato.condicao'
    _order = 'contrato_id, ordem'
    _rec_name = 'ordem'

    def get_meses(self, cr, uid, ids, context={}):
        res = {}

        for condicao_obj in self.browse(cr, uid, ids, context=context):
            linhas = []

            periodo = int(condicao_obj.tipo_mes or '001')
            vezes = int(condicao_obj.vezes or 0)

            #print(periodo)
            #print(vezes)

            if vezes == 0 or vezes == 1:
                dados = DicionarioBrasil({
                    'name': u'1ª parcela',
                    'value': 'balance',
                    'days': 0,
                    'days2': 0,
                    'multiplica': 1,
                    'divide': 1,
                    'meses': 0,
                })
                linhas.append(dados)

            else:
                for i in range(0, vezes):
                    dados = DicionarioBrasil({
                        'name': str(i) + u'ª parcela',
                        'value': 'divisao',
                        'days': 0,
                        'days2': 0,
                        'multiplica': 1,
                        'divide': vezes,
                        'meses': i * periodo,
                    })

                    if i == vezes:
                        dados['value'] = 'balance'

                    #print(dados)

                    linhas.append(dados)

            res[condicao_obj.id] = linhas

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def _descricao_contratual(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for condicao_obj in self.browse(cr, uid, ids):
            condicao = u'• R$ '
            condicao += formata_valor(condicao_obj.valor_principal or 0)
            condicao += u' ('
            condicao += numero_por_extenso_unidade(condicao_obj.valor_principal or 0)
            condicao += u') '

            if condicao_obj.entrada:
                condicao += u'a serem pagos em moeda corrente nacional, no ato da assinatura do presente contrato, como sinal de negócios e “ARRAS” de acordo com o artigo 417 e 419 do código civil brasileiro de 2002;'

            elif condicao_obj.obs and 'FINANC' in condicao_obj.obs.upper():
                condicao += u'a serem pagos em moeda corrente nacional, com recursos próprios ou por meio de financiamento bancário a ser adquirido pelo PROMITENTE COMPRADOR junto à instituição financeira de sua preferência, no prazo de 120 (cento e vinte) dias corridos, a contar da data de comunicação da conclusão da infra-estrutura mínima necessária para o encaminhamento do processo de financiamento, a ser emitida pelo PROMITENTE VENDEDOR. Acertam ainda as Partes, que na impossibilidade do PROMITENTE COMPRADOR efetuar o financiamento bancário ou efetuar o pagamento com recursos próprios poderão ser tomadas as medidas do Parágrafo Sétimo abaixo.'

            else:
                condicao += u'a serem pagos em moeda corrente nacional, R$ '
                condicao += formata_valor(condicao_obj.valor_parcela or 0)
                condicao += u' ('
                condicao += numero_por_extenso_unidade(condicao_obj.valor_parcela or 0)
                condicao += u') '
                condicao += TIPO_MES_DESCRICAO[condicao_obj.tipo_mes].lower()
                condicao += u', num total de '
                condicao += str(condicao_obj.vezes)
                condicao += u' ('
                condicao += numero_por_extenso(condicao_obj.vezes, genero_unidade_masculino=False)
                condicao += u') parcelas'

                if condicao_obj.carteira_id:
                    condicao += u', representadas por boletos'

                if len(condicao_obj.parcela_ids):
                    parcela_obj = condicao_obj.parcela_ids[0]
                    condicao += u', sendo a primeira com vencimento no dia '
                    condicao += data_por_extenso(parcela_obj.data_vencimento)

                    if len(condicao_obj.parcela_ids) > 1:
                        parcela_obj = condicao_obj.parcela_ids[-1]
                        condicao += u' e a última com vencimento no dia '
                        condicao += data_por_extenso(parcela_obj.data_vencimento)

                condicao += u';'

            res[condicao_obj.id] = condicao

        return res

    _columns = {
        'tipo': fields.selection((('O', u'Original'), ('R', u'Renegociação')), u'Tipo', select=True),
        #'condicao_pagamento_id': fields.many2one('finan.tabela.venda', u'Tabela de venda', ondelete='cascade'),
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', ondelete='cascade'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'obs': fields.char(u'Obs.', size=60, select=True),
        'ordem': fields.integer(u'Ordem'),
        #'payment_term_id': fields.many2one('account.payment.term', u'Condição', ondelete='restrict'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict'),
        'valor_principal': fields.float(u'Valor principal'),
        'valor_parcela': fields.float(u'Valor parcela'),
        'valor_entrada': fields.float(u'Valor entrada'),
        'data_inicio': fields.date(u'Data de início da cobrança'),
        'parcela_ids': fields.one2many('finan.contrato.condicao.parcela', 'condicao_id', u'Parcelas'),
        'cheque_ids': fields.one2many('finan.cheque','condicao_contrato_id', u'Cheques'),

        'taxa_juros': fields.float(string=u'Taxa de Juros', digits=(18, 5)),
        'taxa_juros_sacoc': fields.float(string=u'Taxa de Juros SACOC', digits=(18, 5)),
        'tipo_taxa': fields.selection(TIPO_TAXA, string=u'Tipo de juros'),
        'tipo_mes': fields.selection(TIPO_MES, string=u'Período'),
        'taxa_administracao': fields.float(u'Taxa de administração'),
        'taxa_seguro': fields.float(u'Taxa de seguro', digits=(18, 5)),
        'taxa_abertura_credito': fields.float(u'Tarifa de abertura de crédito (TAC)'),
        'taxa_iof': fields.float(u'Alíquota do IOF'),
        'vezes': fields.integer(u'Parcelas'),
        'entrada': fields.boolean(u'Entrada?'),

        'valor_original': fields.float(u'Valor original'),


        #
        # Correção monetária
        #
        'currency_id': fields.many2one('res.currency', u'Ìndice', ondelete='restrict'),
        'data_base': fields.date(u'Data base'),
        'tipo_mes_correcao': fields.selection(TIPO_MES, u'Período de correção'),

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
        'ajusta_quantidade_parcelas': fields.integer(u'Ajuste na quantidade de parcelas'),

        'descricao_contratual': fields.function(_descricao_contratual, type='char', string=u'Descrição contratual'),

        'lancamento_ids': fields.one2many('finan.lancamento', 'finan_contrato_condicao_id', u'Lançamentos gerados'),
        'lancamento_renegociado_ids': fields.many2many('finan.lancamento', 'finan_contrato_codicao_renegociacao', 'finan_contrato_condicao_id', 'lancamento_id', u'Lançamentos a renegociar'),
    }

    _defaults = {
        'tipo': 'O',
        'ordem': 1,
        'currency_id': 6,
        'tipo_mes': '001',
        'tipo_mes_correcao': '001',
        'vezes': 1,
        'data_base': fields.datetime.now,
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

    def onchange_valor_parcela(self, cr, uid, ids, valor_parcela, vezes, tipo_taxa, taxa_juros, currency_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        valor_parcela = D(valor_parcela or 0)

        #if tipo_taxa == TABELA_SACOC and currency_id and taxa_juros:
            #currency_pool = self.pool.get('res.currency')
            #taxa_juros = D(taxa_juros or 0)
            #print('valor_parcela')
            #print(valor_parcela)
            #valor_parcela *= 1 + (taxa_juros / 100)
            #valor_parcela = valor_parcela.quantize(D('0.01'))
            #print(valor_parcela)
            #valor_parcela = currency_pool.compute(cr, uid, 6, currency_id, valor_parcela)
            #print(valor_parcela)

        vezes = D(vezes or 1)
        valores['valor_principal'] = valor_parcela * vezes

        return res

    #_sql_constraints = [
        #('contrato_ordem_unique', 'unique(contrato_id, ordem)',
            #u'O número do contrato/parcelamento não pode se repetir!'),
    #]

    def gera_parcelas(self, cr, uid, ids, context={}):
        parcela_pool = self.pool.get('finan.contrato.condicao.parcela')

        for condpag_obj in self.browse(cr, uid, ids, context=context):
            if condpag_obj.contrato_id and condpag_obj.contrato_id.parcelas_manual:
                continue

            lista_vencimentos = condpag_obj.calcula(D(condpag_obj.valor_principal), data_base=condpag_obj.data_inicio, entrada=D(condpag_obj.valor_entrada or 0))

            print(lista_vencimentos)

            for parcela_obj in condpag_obj.parcela_ids:
                #
                # CUIDADO!!!!!
                #
                # A linha abaixo, que exclui os lançamento financeiros vinculados ao contrato
                # PRECISA ser removida quando entrar em produção.
                #
                cr.execute('delete from finan_lancamento l where l.contrato_imovel_id = {contrato_id};'.format(contrato_id=condpag_obj.contrato_id.id))

                parcela_obj.unlink()

            print('pronto, apagou todas')

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
                    'entrada': condpag_obj.entrada,
                    'obs': condpag_obj.obs,
                    'data_base': condpag_obj.data_base,
                    'currency_id': condpag_obj.currency_id.id,
                    'tipo_mes_correcao': condpag_obj.tipo_mes_correcao,
                    'valor_seguro': parcela.valor_seguro,
                    'valor_administracao': parcela.valor_administracao,
                    'valor_capital': parcela.valor_capital or parcela.valor_original,
                    'valor_capital_juros': parcela.valor_capital_juros,
                    'valor_capital_juros_correcao': parcela.valor_capital_juros_correcao,
                    'valor_original': parcela.valor_original,
                    'indice': parcela.indice,
                    'correcao': parcela.correcao,
                }

                if condpag_obj.res_partner_address_id:
                    dados['res_partner_address_id'] = condpag_obj.res_partner_address_id.id

                if condpag_obj.documento_id:
                    dados['documento_id'] = condpag_obj.documento_id.id

                if condpag_obj.conta_id:
                    dados['conta_id'] = condpag_obj.conta_id.id

                if condpag_obj.centrocusto_id:
                    dados['centrocusto_id'] = condpag_obj.centrocusto_id.id

                if condpag_obj.res_partner_bank_id:
                    dados['res_partner_bank_id'] = condpag_obj.res_partner_bank_id.id

                if condpag_obj.carteira_id:
                    dados['carteira_id'] = condpag_obj.carteira_id.id

                if condpag_obj.formapagamento_id:
                    dados['formapagamento_id'] = condpag_obj.formapagamento_id.id

                parcela_id = parcela_pool.create(cr, uid, dados)
                parcela_pool.atualiza_valor(cr, uid, [parcela_id])
                #parcela_obj = parcela_pool.browse(cr, uid, parcela_id)
                i += 1

        return True


    def calcula(self, cr, uid, ids, valor, data_base=None, entrada=0, context={}):
        currency_pool = self.pool.get('res.currency')

        data_base = parse_datetime(data_base or hoje())
        valor_original = D(valor).quantize(D('0.01'))
        valor = D(valor).quantize(D('0.01'))
        entrada = D(entrada).quantize(D('0.01'))
        #entrada = D('10000').quantize(D('0.01'))
        res = []

        for condicao_obj in self.browse(cr, uid, ids, context=context):
            if condicao_obj.tipo_taxa == TABELA_SACOC:
                taxa_administracao = D(condicao_obj.taxa_administracao or 0)
                taxa_administracao = taxa_administracao.quantize(D('0.01'))

            else:
                taxa_administracao = valor_original * D(condicao_obj.taxa_administracao or 0) / D(100)
                taxa_administracao = taxa_administracao.quantize(D('0.01'))

            condicao_obj.saldo_devedor = D(valor or 0)
            condicao_obj.divida_amortizada = D(0)

            linhas = condicao_obj.get_meses()

            taxa_abertura_credito = D(0)
            taxa_iof = D(0)

            taxa_juros = D(condicao_obj.taxa_juros or 0) / D(100)

            if taxa_juros:
                #
                # Ultima parcela tem o máximo de dias/meses a considerar
                #
                parc_obj = linhas[-1]

                if parc_obj.meses:
                    meses = parc_obj.meses
                else:
                    dias = D(parc_obj.days or 0)
                    meses = dias / D(30)

                if condicao_obj.tipo_taxa == JUROS_COMPOSTOS:
                    valor_parcela = numpy.pmt(taxa_juros, meses, (valor_original - entrada) * -1)
                    valor_parcela = valor_parcela.quantize(D('0.01'))
                    valor_original = entrada + (valor_parcela * meses)
                    valor = entrada + (valor_parcela * meses)

                elif condicao_obj.tipo_taxa == TABELA_PRICE:
                    valor_parcela = numpy.pmt(taxa_juros, meses, (valor_original - entrada) * -1)
                    valor_parcela = valor_parcela.quantize(D('0.01'))

                elif condicao_obj.tipo_taxa == JUROS_SIMPLES:
                    valor_original = entrada + ((valor_original - entrada) * taxa_juros)
                    valor = entrada + ((valor - entrada) * taxa_juros)

                elif condicao_obj.tipo_taxa == TABELA_SACOC:
                    pass

            #
            # Calculamos as datas e juros de cada parcela
            #
            if condicao_obj.tipo_taxa == TABELA_SACOC:
                #
                # Segue planilha doida da Exata no chamado 1300
                #
                valor_parcela = D(condicao_obj.valor_parcela or 0)
                valor = D(condicao_obj.valor_principal or 0)
                saldo_devedor = valor - valor_parcela

                i = 0
                for parcela_obj in linhas:
                    #
                    # Paga a data da parcela
                    #
                    parcela_obj.value = 'fixed'
                    parcela_obj.value_amount = 1
                    parcela_data = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada)

                    valor_capital = valor_parcela

                    valor_parcela *= 1 + taxa_juros

                    valor_juros = valor_capital * taxa_juros
                    valor_juros = valor_juros.quantize(D('0.01'))

                    valor_capital_juros = valor_parcela

                    indice = 0
                    if parcela_data.data.date() < hoje():
                        indice_obj = currency_pool.browse(cr, uid, condicao_obj.currency_id.id, context={'date': str(ultimo_dia_mes(mes_passado(parcela_data.data)))})
                        indice = D(indice_obj.rate or 0)
                        valor_parcela = currency_pool.converte(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(parcela_data.data)))})
                        #valor_parcela = currency_pool.compute(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(parcela_data.data)))})
                        #valor_parcela = currency_pool.compute(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(hoje()))})

                    valor_capital_juros_correcao = valor_parcela

                    valor_correcao = valor_capital_juros_correcao - valor_capital_juros

                    saldo_devedor = valor_parcela * (len(linhas) - i - 1)

                    valor_seguro = saldo_devedor * D(condicao_obj.taxa_seguro or 0) / D(100)
                    valor_seguro = valor_seguro.quantize(D('0.01'))

                    i += 1

                    parcela_obj.value = 'fixed'
                    parcela_obj.value_amount = valor_parcela + valor_seguro + D(condicao_obj.taxa_administracao or 0)

                    parcela = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada)
                    parcela.saldo_devedor = saldo_devedor
                    parcela.valor_seguro = valor_seguro
                    parcela.valor_administracao = taxa_administracao
                    parcela.valor_capital = valor_capital
                    parcela.valor_capital_juros = valor_capital_juros
                    parcela.valor_capital_juros_correcao = valor_capital_juros_correcao
                    parcela.valor_original = D(condicao_obj.valor_original or 0)
                    parcela.juros = valor_juros
                    parcela.correcao = valor_correcao
                    parcela.indice = indice
                    res.append(parcela)

            else:
                valor_total = taxa_administracao
                for parcela_obj in linhas:
                    if condicao_obj.tipo_taxa == TABELA_PRICE:
                        parcela_obj.value = 'fixed'
                        parcela_obj.value_amount = valor_parcela

                    parcela = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada)
                    valor -= parcela.valor_original
                    #print(parcela)
                    taxa_abertura_credito += D(condicao_obj.taxa_abertura_credito or 0)

                    valor_parcela = parcela.valor
                    indice = 0
                    if parcela.data < hoje():
                        indice_obj = currency_pool.browse(cr, uid, condicao_obj.currency_id.id, context={'date': str(ultimo_dia_mes(mes_passado(parcela.data)))})
                        indice = D(indice_obj.rate or 0)
                        valor_parcela = currency_pool.converte(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(parcela.data)))})
                        #valor_parcela = currency_pool.compute(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(mes_passado(parcela.data)))})
                        #valor_parcela = currency_pool.compute(cr, uid, REAIS_ID, condicao_obj.currency_id.id, valor_parcela, context={'date': str(ultimo_dia_mes(hoje()))})

                    valor_capital_juros_correcao = valor_parcela

                    valor_correcao = valor_capital_juros_correcao - D(condicao_obj.valor_parcela or 0)
                    valor_parcela = valor_capital_juros_correcao

                    valor_total += valor_parcela

                    #parcela.saldo_devedor = saldo_devedor
                    #parcela.valor_seguro = valor_seguro
                    #parcela.valor_administracao = taxa_administracao
                    parcela.valor_capital = D(condicao_obj.valor_parcela or 0)
                    #parcela.valor_capital_juros = valor_capital_juros
                    parcela.valor_capital_juros_correcao = valor_capital_juros_correcao
                    parcela.valor_original = D(condicao_obj.valor_original or 0)
                    #parcela.juros = valor_juros
                    parcela.correcao = valor_correcao
                    parcela.indice = indice
                    parcela.valor = valor_parcela
                    res.append(parcela)

        return res

    def monta_parcela(self, condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada=0):
        parcela = Parcela()

        if parcela_obj.value == 'fixed':
            parcela.valor = D(parcela_obj.value_amount)

        elif parcela_obj.value == 'entrada':
            parcela.valor = D(entrada)

        elif parcela_obj.value == 'procent':
            parcela.valor = (valor_original - entrada) * D(parcela_obj.value_amount) / D('100')

        elif parcela_obj.value == 'balance':
            parcela.valor = valor

        elif parcela_obj.value == 'divisao':
            parcela.valor = valor
            if parcela_obj.divide and parcela_obj.multiplica:
                parcela.valor = (valor_original - entrada) * D(parcela_obj.multiplica) / D(parcela_obj.divide)
            elif parcela_obj.multiplica:
                parcela.valor = (valor_original - entrada) * D(parcela_obj.multiplica)
            elif parcela_obj.divide:
                parcela.valor = (valor_original - entrada) / D(parcela_obj.divide)

        parcela.valor = parcela.valor.quantize(D('0.01'))
        parcela.valor_original = parcela.valor.quantize(D('0.01'))

        if parcela.valor:
            if parcela_obj.meses:
                meses = parcela_obj.meses
                dia_fixo = parcela_obj.days2 or 0

                #
                # No caso da conta em meses, colocamos o dia fixo primeiro
                # Se o dia fixo for negativo, ele conta a partir do último dia do mês
                #
                data_parcela = data_base + relativedelta(months=meses)

                if dia_fixo > 0:
                    data_parcela += relativedelta(day=dia_fixo)
                elif dia_fixo < 0:
                    data_parcela = ultimo_dia_mes(data_parcela)

                    dia_fixo += 1  # -1 significa exatamente o último dia do mês

                    if dia_fixo < 0:
                        data_parcela += relativedelta(days=dia_fixo)

            else:
                #
                # Define a data da parcela como sendo a data de referência
                # + x dias
                #
                dias = parcela_obj.days or 0
                dia_fixo = parcela_obj.days2 or 0
                data_parcela = data_base + relativedelta(days=dias)

                #
                # days2 é um dia fixo do mês
                # se o valor for negativo, conta x dias a partir do final do mês
                #
                if dia_fixo < 0:
                    #
                    # Pega o dia 1º do próximo mês
                    #
                    dia_primeiro = data_parcela + relativedelta(day=1, months=1)
                    data_parcela = dia_primeiro + relativedelta(days=dia_fixo)

                #
                # e se for positivo, é o dia x do mês seguinte
                #
                elif dia_fixo > 0:
                    data_parcela += relativedelta(day=dia_fixo, months=1)

                meses = idade_meses(data_base, data_parcela)

            parcela.data = data_parcela

            if isinstance(parcela.data, datetime):
                parcela.data = parcela.data.date()

            if taxa_juros:
                if condicao_obj.tipo_taxa == JUROS_SIMPLES:
                    pass

                elif condicao_obj.tipo_taxa == JUROS_COMPOSTOS:
                    pass

                elif condicao_obj.tipo_taxa == TABELA_PRICE:
                    parcela.juros = condicao_obj.saldo_devedor * taxa_juros
                    parcela.juros = parcela.juros.quantize(D('0.01'))
                    parcela.amortizacao = parcela.valor - parcela.juros
                    condicao_obj.divida_amortizada += parcela.amortizacao
                    parcela.divida_amortizada = condicao_obj.divida_amortizada
                    condicao_obj.saldo_devedor -= parcela.amortizacao
                    parcela.saldo_devedor = condicao_obj.saldo_devedor
                    parcela.valor_original = parcela.amortizacao

                    #print('juros', parcela.juros)
                    #print('amortizacao', parcela.amortizacao)
                    #print('divida_amortizada', parcela.divida_amortizada)
                    #print('saldo devedor', parcela.saldo_devedor)

        return parcela


finan_contrato_condicao()
