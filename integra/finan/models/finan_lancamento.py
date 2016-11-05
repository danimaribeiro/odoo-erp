# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime, date, timedelta
from pybrasil.valor.decimal import Decimal as D
import base64
from numpy import base_repr

# from datetime import datetime
from osv import orm, fields, osv
#from sped.models.fields import *
from pybrasil.febraban.banco import BANCO_CODIGO
from pybrasil.febraban.boleto import (Boleto, gera_boletos_pdf)
from pybrasil.valor import formata_valor, valor_por_extenso_unidade
from pybrasil.data import data_por_extenso, hoje, parse_datetime, formata_data
from sql_finan_lancamento import SQL_VIEW_PAGAMENTO_RESUMO, SQL_AJUSTA_QUITACAO, SQL_AJUSTA_QUITACAO_DEMORADO
from mako.template import Template
from copy import copy
import os



class CampoDinheiro(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (18, 2)
        super(CampoDinheiro, self).__init__(*args, **kwargs)


class CampoPorcentagem(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (21, 11)
        super(CampoPorcentagem, self).__init__(*args, **kwargs)



TIPO_LANCAMENTO = (
    ('R', u'A RECEBER'),
    ('P', u'A PAGAR'),
    ('T', u'TRANSFERÊNCIA'),
    ('E', u'ENTRADA'),
    ('S', u'SAÍDA'),
    ('PR', u'PAGAMENTO RECEBIDO'),
    ('PP', u'PAGAMENTO EFETUADO'),
    ('LR', u'LOTE RECEBIMENTO'),
    ('LP', u'LOTE PAGAMENTO'),
    ('AR', u'ADIANTAMENTO RECEBIDO'),
    ('AP', u'ADIANTAMENTO PAGO'),
    ('MR', u'MODELO RECEBER'),
    ('MP', u'MODELO PAGAR'),
)
TIPO_LANCAMENTO_DICT = dict(TIPO_LANCAMENTO)

TIPO_LANCAMENTO_A_RECEBER = 'R'
TIPO_LANCAMENTO_A_PAGAR = 'P'
TIPO_LANCAMENTO_TRANSFERENCIA = 'T'
TIPO_LANCAMENTO_TRANSACAO_ENTRADA = 'E'
TIPO_LANCAMENTO_TRANSACAO_SAIDA = 'S'
TIPO_LANCAMENTO_PAGAMENTO_RECEBIDO = 'PR'
TIPO_LANCAMENTO_PAGAMENTO_PAGO = 'PP'
TIPO_LANCAMENTO_LOTE_RECEBIMENTO = 'LR'
TIPO_LANCAMENTO_LOTE_PAGAMENTO = 'LP'
TIPO_LANCAMENTO_ADIANTAMENTO_RECEBIDO = 'AR'
TIPO_LANCAMENTO_ADIANTAMENTO_PAGO = 'AP'

TIPO_TRANSACAO = (
    ('E', u'TRANSAÇÃO DE ENTRADA'),
    ('S', u'TRANSAÇÃO DE SAÍDA'),
    ('T', u'TRANSFERÊNCIA'),
)

TIPO_LOTE = (
    ('LR', u'LOTE RECEBIMENTO'),
    ('LP', u'LOTE PAGAMENTO'),
)

TIPO_PAGAMENTO = (
    ('PR', u'PAGAMENTO RECEBIDO'),
    ('PP', u'PAGAMENTO EFETUADO'),
)

SITUACAO_VENCIDO = 'Vencido'  # após a data do vencimento
SITUACAO_A_VENCER = 'A vencer'  # até a data do vencimento
SITUACAO_VENCE_HOJE = 'Vence hoje'
SITUACAO_QUITADO = 'Quitado'  # pago
SITUACAO_BAIXADO = 'Baixado'  # ignorado pelo sistema
SITUACAO_BAIXADO_PARCIAL = 'Baixado parcial'  # ignorado pelo sistema
SITUACAO_CONCILIADO = 'Conciliado'  # Quitado e conciliado com o banco
SITUACAO_NAO_IDENTIFICADO = 'Não identificado'
SITUACAO_SEM_VENCIMENTO = 'Sem informação de vencimento'

TIPO_ADICAO = 0
TIPO_EXCLUSAO = 1


class finan_lancamento(orm.Model):
    _description = u'Lançamentos'
    _name = 'finan.lancamento'
    _inherit = 'mail.thread'
    _rec_name = 'descricao'
    _order = 'data_quitacao desc, data_vencimento, numero_documento_original, numero_documento'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):

            if registro.tipo in ['MR','MP']:
                txt = registro.descricao_modelo
                retorno[registro.id] = txt
                continue

            txt = registro.tipo

            if registro.documento_id:
                txt += ' '
                txt += registro.documento_id.nome

            txt += ' '

            if registro.tipo in ['PP', 'PR'] and registro.lancamento_id:
                txt += registro.lancamento_id.numero_documento or u's/nº'
            else:
                txt += registro.numero_documento or u's/nº'

            if registro.complemento:
                txt += ' '
                txt += registro.complemento

            if registro.partner_id:
                txt += ' '
                txt += registro.partner_id.name

            if registro.data_vencimento:
                txt += ' V.' + formata_data(parse_datetime(registro.data_vencimento))

            if registro.data_quitacao:
                txt += ' Q.' + formata_data(parse_datetime(registro.data_quitacao))

            if registro.data_baixa:
                txt += ' B.' + formata_data(parse_datetime(registro.data_baixa))

            if registro.valor_documento:
                txt += ' R$ ' + formata_valor(registro.valor_documento)

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [('numero_documento', 'ilike', texto)]

        return procura

    def _situacao(self, cursor, user_id, ids, fields, arg, context=None):
        '''
        Define se o lançamento está quitado, em aberto, a vencer ou vencido
        '''

        retorno = {}

        for lancamento in self.browse(cursor, user_id, ids):
            #
            # Transferência não tem sentido estar a vencer ou quitado, nem vencido
            #
            if lancamento.tipo in [TIPO_LANCAMENTO_TRANSFERENCIA, TIPO_LANCAMENTO_TRANSACAO_ENTRADA, TIPO_LANCAMENTO_TRANSACAO_SAIDA]:
                retorno[lancamento.id] = SITUACAO_CONCILIADO

            else:
                if lancamento.conciliado:
                    retorno[lancamento.id] = SITUACAO_CONCILIADO
                elif lancamento.data_baixa:
                    if lancamento.valor:
                        retorno[lancamento.id] = SITUACAO_BAIXADO_PARCIAL
                    else:
                        retorno[lancamento.id] = SITUACAO_BAIXADO
                elif lancamento.data_quitacao:
                    retorno[lancamento.id] = SITUACAO_QUITADO
                elif not lancamento.data_vencimento:
                    retorno[lancamento.id] = 'Sem informação de vencimento'
                else:
                    data_vencimento = datetime.strptime(lancamento.data_vencimento, '%Y-%m-%d').date()

                    if data_vencimento == date.today():
                        retorno[lancamento.id] = SITUACAO_VENCE_HOJE

                    elif data_vencimento > date.today():
                        retorno[lancamento.id] = SITUACAO_A_VENCER

                    else:
                        retorno[lancamento.id] = SITUACAO_VENCIDO

        return retorno

    def _procura_situacao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = []
        if texto == SITUACAO_BAIXADO or texto == SITUACAO_BAIXADO_PARCIAL:
            procura = [('data_baixa', '!=', False)]

        elif texto == SITUACAO_CONCILIADO:
            procura = [('data', '!=', False)]

        elif texto == SITUACAO_QUITADO:
            procura = [('data_quitacao', '!=', False)]

        #
        # Atenção!!!!
        #
        # Nos filtros abaixo é necessário:
        # · do último para o primeiro, contar 2 itens e acrescentar o '&' - AND
        # · a partir daí, acrescentar o '&' intercalado entre cada filtro
        #
        elif texto == SITUACAO_VENCE_HOJE:
            procura = ['&', ('data_baixa', '=', False),
                       '&', ('data', '=', False),
                       '&', ('data_quitacao', '=', False),
                       ('data_vencimento', '=', str(date.today()))]

        elif texto == SITUACAO_A_VENCER:
            procura = ['&', ('data_baixa', '=', False),
                       '&', ('data', '=', False),
                       '&', ('data_quitacao', '=', False),
                       ('data_vencimento', '>', str(date.today()))]

        elif texto == SITUACAO_VENCIDO:
            procura = ['&', ('data_baixa', '=', False),
                       '&', ('data', '=', False),
                       '&', ('data_quitacao', '=', False),
                       ('data_vencimento', '<', str(date.today()))]

        else:
            procura = ['&', ('data_baixa', '=', False),
                       '&', ('data', '=', False),
                       '&', ('data_quitacao', '=', False),
                       ('data_vencimento', '=', False)]

        return procura

    def _ano_vencimento(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for lancamento in self.browse(cursor, user_id, ids):
            if lancamento.data_vencimento:
                retorno[lancamento.id] = lancamento.data_vencimento[:4]
            else:
                retorno[lancamento.id] = ''

        return retorno

    def _ano_mes_vencimento(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for lancamento in self.browse(cursor, user_id, ids):
            if lancamento.data_vencimento:
                retorno[lancamento.id] = lancamento.data_vencimento[:7]
            else:
                retorno[lancamento.id] = ''

        return retorno

    def _soma_saldo(self, cr, uid, ids, nome_campo, args, context=None):
        if ids:
            lanc_obj = self.browse(cr, uid, ids[0])
            res_partner_bank_id = lanc_obj.res_partner_bank_id.id
            #data = lanc_obj.data

            if lanc_obj.res_partner_bank_creditar_id:
                res_partner_bank_creditar_id = lanc_obj.res_partner_bank_creditar_id.id
            else:
                res_partner_bank_creditar_id = False

            if nome_campo == 'saldo_banco_creditar':
                res_partner_bank_id = res_partner_bank_creditar_id

        else:

            #if 'data' not in context:
                #return {}

            #data = context['data']

            if nome_campo == 'saldo_banco':
                if 'res_partner_bank_id' not in context:
                    if ids:
                        return {}
                    elif ids == []:
                        return 0
                else:
                    res_partner_bank_id = context['res_partner_bank_id']
            elif nome_campo == 'saldo_banco_creditar':
                if 'res_partner_bank_creditar_id' not in context:
                    if ids:
                        return {}
                    elif ids == []:
                        return 0
                else:
                    res_partner_bank_id = context['res_partner_bank_creditar_id']

        data = fields.date.today()

        if not res_partner_bank_id or not data:
            if ids:
                return {}
            elif ids == []:
                return 0

        sql_saldo_banco = """
            select
                coalesce(sum(e.valor_compensado_credito), 0) as valor_compensado_credito,
                coalesce(sum(e.valor_compensado_debito), 0) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_quitacao <= '%s';
            """

        cr.execute(sql_saldo_banco % (res_partner_bank_id, data))
        credito, debito = cr.fetchall()[0]
        saldo_banco = credito - debito

        #print(credito, debito, saldo_banco, ids)

        res = {}
        if ids:
            for id in ids:
                res[id] = saldo_banco
        elif ids == []:
            res = saldo_banco

        return res

    #def _get_soma_pagamento(self, cr, uid, ids, nome_campo, args, context=None):
        #res = {}

        #if nome_campo == 'valor_pago':
            #nome_campo = 'valor_documento'
        #elif nome_campo == 'total_juros':
            #nome_campo = 'valor_juros'
        #elif nome_campo == 'total_multa':
            #nome_campo = 'valor_multa'
        #elif nome_campo == 'total_desconto':
            #nome_campo = 'valor_desconto'

        #for lancamento_obj in self.browse(cr, uid, ids):
            #if lancamento_obj.tipo not in [TIPO_LANCAMENTO_A_PAGAR, TIPO_LANCAMENTO_A_RECEBER, TIPO_LANCAMENTO_LOTE_PAGAMENTO, TIPO_LANCAMENTO_LOTE_RECEBIMENTO]:
                #res[lancamento_obj.id] = D('0')
            #else:
                #soma = D('0')
                #for pagamento_obj in lancamento_obj.pagamento_ids:
                    #soma += D(str(getattr(pagamento_obj, 'valor_documento', 0)))

                #soma = soma.quantize(D('0.01'))

                #res[lancamento_obj.id] = soma

        #return res

    #def _saldo_lancamento(self, cr, uid, ids, nome_campo, args=None, context={}):
        #res = {}
        #for lancamento_obj in self.browse(cr, uid, ids):
            #if lancamento_obj.tipo not in [TIPO_LANCAMENTO_A_PAGAR, TIPO_LANCAMENTO_A_RECEBER, TIPO_LANCAMENTO_LOTE_PAGAMENTO, TIPO_LANCAMENTO_LOTE_RECEBIMENTO]:
                #res[lancamento_obj.id] = D('0')
            #else:
                #valor_pago = self._get_soma_pagamento(cr, uid, [lancamento_obj.id], 'valor_pago', None, None).items()[0][1] or 0
                #res[lancamento_obj.id] = D(str(lancamento_obj.valor_documento)) - D(str(valor_pago))

        #return res

    def onchange_juros_multa_desconto(self, cr, uid, ids, tipo, valor_documento, valor_juros, valor_multa, valor_desconto, outros_acrescimos, context=None):
        if valor_documento <= 0:
            raise osv.except_osv(u'Inválido !', u'É obrigatório informar o valor do documento/valor a abater!')

        if tipo == 'PP':
            return {'value': {'valor': valor_documento + valor_juros + valor_multa + outros_acrescimos - valor_desconto}}
        else:
            return {'value': {'valor': valor_documento + valor_juros + valor_multa - valor_desconto}}

    def onchange_valor(self, cr, uid, ids, valor):
        if valor <= 0:
            raise osv.except_osv(u'Inválido !', u'É obrigatório informar o valor da transação!')

        return {'value': {'valor_documento': valor}}

    def onchange_tipo_transacao(self, cr, uid, ids, tipo_transacao):
        if not tipo_transacao:
            raise osv.except_osv(u'Inválido !', u'É obrigatório informar o tipo da transação!')

        return {'value': {'tipo': tipo_transacao}}

    def _get_debito_credito(self, cr, uid, ids, nome_campo, args, context=None):
        if not ids:
            return {}

        if not context:
            context = {}

        if 'res_partner_bank_id' in context:
            res_partner_bank_id = context['res_partner_bank_id']
        else:
            res_partner_bank_id = False

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            valor = 0
            if lancamento_obj.res_partner_bank_id and lancamento_obj.res_partner_bank_id.id == res_partner_bank_id:
                if lancamento_obj.tipo in ['PR', 'R', 'E', 'LR']:
                    valor = 1
                elif lancamento_obj.tipo in ['PP', 'P', 'S', 'LP', 'T']:
                    valor = -1
            elif lancamento_obj.res_partner_bank_creditar_id and lancamento_obj.res_partner_bank_creditar_id.id == res_partner_bank_id:
                if lancamento_obj.tipo == 'T':
                    valor = 1

            res[lancamento_obj.id] = valor

        return res

    def _get_valor_conciliacao(self, cr, uid, ids, nome_campo, args, context):
        if not ids:
            return {}

        #print('ids', ids)

        if not context:
            context = {}

        if 'res_partner_bank_id' in context:
            res_partner_bank_id = context['res_partner_bank_id']
        else:
            res_partner_bank_id = False

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            valor = 0
            if lancamento_obj.res_partner_bank_id and lancamento_obj.res_partner_bank_id.id == res_partner_bank_id:
                if lancamento_obj.tipo in ['PR', 'R', 'E', 'LR']:
                    valor = 1
                elif lancamento_obj.tipo in ['PP', 'P', 'S', 'LP', 'T']:
                    valor = -1
            elif lancamento_obj.res_partner_bank_creditar_id and lancamento_obj.res_partner_bank_creditar_id.id == res_partner_bank_id:
                if lancamento_obj.tipo == 'T':
                    valor = 1

            res[lancamento_obj.id] = lancamento_obj.valor * valor

        return res

    def _get_banco_contrapartida(self, cr, uid, ids, nome_campo, args, context):
        if not ids:
            return {}

        if not context:
            context = {}

        if 'res_partner_bank_id' in context:
            res_partner_bank_id = context['res_partner_bank_id']
        else:
            res_partner_bank_id = False

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = False
            #if lancamento_obj.tipo != 'T' and lancamento_obj.res_partner_bank_id:
                #res[lancamento_obj.id] = lancamento_obj.res_partner_bank_id.id
            if lancamento_obj.tipo != 'T':
                pass
            elif lancamento_obj.res_partner_bank_id:
                if lancamento_obj.res_partner_bank_id.id == res_partner_bank_id:
                    res[lancamento_obj.id] = lancamento_obj.res_partner_bank_creditar_id.id
            elif lancamento_obj.res_partner_bank_creditar_id:
                if lancamento_obj.res_partner_bank_creditar_id.id == res_partner_bank_id:
                    res[lancamento_obj.id] = lancamento_obj.res_partner_bank_id.id

        return res

    def _get_banco_formapagamento_id(self, cr, uid, ids, nome_campo, args, context):
        if not ids:
            return {}

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = False
            if lancamento_obj.tipo in ['PP', 'PR']:
                if lancamento_obj.lancamento_id.formapagamento_id:
                    res[lancamento_obj.id] = lancamento_obj.lancamento_id.formapagamento_id.id
            elif lancamento_obj.formapagamento_id:
                res[lancamento_obj.id] = lancamento_obj.formapagamento_id.id

        return res

    def _get_banco_conta_id(self, cr, uid, ids, nome_campo, args, context):
        if not ids:
            return {}

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = False
            if lancamento_obj.tipo in ['PP', 'PR']:
                if lancamento_obj.lancamento_id.conta_id:
                    res[lancamento_obj.id] = lancamento_obj.lancamento_id.conta_id.id
            elif lancamento_obj.conta_id:
                res[lancamento_obj.id] = lancamento_obj.conta_id.id

        return res

    def _get_banco_partner_id(self, cr, uid, ids, nome_campo, args, context):
        if not ids:
            return {}

        res = {}
        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = False
            if lancamento_obj.tipo in ['PP', 'PR']:
                if lancamento_obj.lancamento_id.partner_id:
                    res[lancamento_obj.id] = lancamento_obj.lancamento_id.partner_id.id
            elif lancamento_obj.partner_id:
                res[lancamento_obj.id] = lancamento_obj.partner_id.id

        return res

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.company_id.partner_id.cnpj_cpf:
                res[obj.id] = obj.company_id.partner_id.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    def _get_parcial(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.situacao in [SITUACAO_A_VENCER, SITUACAO_VENCIDO, SITUACAO_VENCE_HOJE]
            res[obj.id] = res[obj.id] and len(obj.pagamento_ids) > 0

        return res

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.id

        return res

    _columns = {
        'codigo': fields.function(_codigo, string=u'Código', method=True, type='integer', store=True),
        'descricao': fields.function(_descricao, string='Documento', method=True, type='char', fnct_search=_procura_descricao),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', relation='res.company', string=u'Empresa mãe', store=True, select=True),
        'company_id': fields.many2one('res.company', u'Empresa', required=True, select=True, ondelete='restrict'),
        'company_partner_id': fields.related('company_id', 'partner_id', type='many2one', string=u'Empresa', relation='res.partner', store=True),
        'cnpj_cpf': fields.related('company_partner_id', 'cnpj_cpf', type='char', string=u'CNPJ/CPF', store=True, method=True),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True),
        'tipo': fields.selection(TIPO_LANCAMENTO, u'Tipo', required=True, select=True),
        'tipo_transacao': fields.selection(TIPO_TRANSACAO, u'Tipo'),
        'provisionado': fields.boolean(u'Provisionado', required=True, select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', select=True, ondelete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True, ondelete='restrict'),
        'res_partner_bank_creditar_id': fields.many2one('res.partner.bank', u'Conta Bancária a creditar', select=True),
        'sugestao_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária de previsão', select=True, ondelete='restrict'),
        #'situacao': fields.function(_situacao, string=u'Situação', method=True, type='char', fnct_search=_procura_situacao, store=True, select=True),
        'situacao': fields.char(u'Situação', type='char', size=30, select=True),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'rateio_ids': fields.one2many('finan.lancamento.rateio', 'lancamento_id', u'Rateio por centros de custo'),
        'phonecall_ids': fields.one2many('crm.phonecall', 'lancamento_id', u'Contato telefonico'),
        'partner_id': fields.many2one('res.partner', u'Parceiro', select=True, ondelete='restrict'),
        'create_uid': fields.many2one('res.users', u'Usuário', select=True, ondelete='restrict'),
        'res_partner_address_id': fields.many2one('res.partner.address', u'Endereço de cobrança', select=True, ondelete='restrict'),
        'historico': fields.text(u'Histórico'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),
        'write_date': fields.datetime( u'Data Alteração'),

        #
        # Data e valor de caixa - movimentação do banco
        #
        'data': fields.date(u'Data', select=True),
        'valor': CampoDinheiro(u'Valor'),

        #
        # Dados necessários para controle de documentos a receber ou a pagar
        #
        'data_vencimento': fields.date(u'Data de vencimento', select=True),
        'numero_documento': fields.char(u'Número do documento', size=30, select=True),
        'data_documento':  fields.date(u'Data do documento', select=True),
        'valor_documento': CampoDinheiro(u'Valor do documento'),

        #
        # Dados necessários para controle de quitação
        #
        'data_quitacao': fields.date(u'Data de quitação', select=True),
        'data_baixa': fields.date(u'Data de baixa', select=True),
        #'motivo_baixa': fields.text(u'Motivo da baixa'),
        'motivo_baixa_id': fields.many2one('finan.motivobaixa', u'Motivo para a baixa', select=True),

        #
        # Boletos
        #
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', select=True, ondelete='restrict'),
        'nosso_numero': fields.char(u'Nosso número', size=20),
        'data_boleto': fields.date(u'Data do boleto'),

        'data_juros': fields.date(u'Juros a partir de'),
        'porcentagem_juros': CampoPorcentagem(u'% de juros por dia'),
        'data_multa': fields.date(u'Multa a partir de'),
        'porcentagem_multa': CampoPorcentagem(u'% de multa'),
        'data_desconto': fields.date(u'Desconto até'),
        'porcentagem_desconto': CampoPorcentagem(u'% de desconto'),

        #
        # Para contas a receber e a pagar, juros, descontos ou multa
        #
        'valor_juros': CampoDinheiro(u'Juros'),
        'valor_desconto': CampoDinheiro(u'Desconto'),
        'valor_multa': CampoDinheiro(u'Multa'),
        'outros_acrescimos': CampoDinheiro(u'Outros acréscimos'),
        'outros_debitos': CampoDinheiro(u'Outros débitos'),

        'valor_juros_previsto': CampoDinheiro(u'Juros Previsto'),
        'valor_desconto_previsto': CampoDinheiro(u'Desconto Previsto'),
        'valor_multa_prevista': CampoDinheiro(u'Multa Prevista'),

        'exige_centro_custo': fields.related('conta_id', 'exige_centro_custo', type='boolean', relation='finan.conta', string=u'Exige centro de custo?', store=False),

        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'finan.lancamento')]),

        #
        # Funcoes para filtrar datas por periodo
        #
        'data_vencimento_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De vencimento'),
        'data_vencimento_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A vencimento'),
        'data_documento_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De documento'),
        'data_documento_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A documento'),
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De vencimento'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A vencimento'),
        'data_quitacao_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De quitacao'),
        'data_quitacao_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A quitacao'),
        'data_baixa_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De baixa'),
        'data_baixa_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A baixa'),
        'valor_documento_from': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'De valor'),
        'valor_documento_to': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'A valor'),
        'valor_from': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'De valor'),
        'valor_to': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'A valor'),

        'ano_vencimento': fields.function(_ano_vencimento, string=u'Ano de vencimento', method=True, type='char', store=True),
        'ano_mes_vencimento': fields.function(_ano_mes_vencimento, string=u'Mês de vencimento', method=True, type='char', store=True),

        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
        'exige_numero': fields.related('formapagamento_id', 'exige_numero', type='boolean', string=u'Exige documento?'),
        #
        # lancamento_id pode ser:
        # 1. pagamentos simples, a conta a receber ou pagar que está sendo paga
        # 2. pagamentos múltiplos, o registro do lote de pagamento
        #
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento pai', select=True, domain=[('tipo', 'in', [TIPO_LANCAMENTO_A_PAGAR, TIPO_LANCAMENTO_A_RECEBER, TIPO_LANCAMENTO_LOTE_PAGAMENTO, TIPO_LANCAMENTO_LOTE_RECEBIMENTO])], ondelete='set null'),

        #
        # Pagamentos simples, só pode ser do tipo pagamento de conta a pagar ou a receber
        #
        'pagamento_ids': fields.one2many('finan.lancamento', 'lancamento_id', u'Pagamentos', domain=[('tipo', 'in', [TIPO_LANCAMENTO_PAGAMENTO_PAGO, TIPO_LANCAMENTO_PAGAMENTO_RECEBIDO])]),

        #
        # Para tela de pagamento em lote
        #
        'lote_pago_ids': fields.one2many('finan.lancamento', 'lancamento_id', u'Pagos', domain=[('tipo', 'in', [TIPO_LANCAMENTO_A_PAGAR, TIPO_LANCAMENTO_A_RECEBER])]),
        'lote_pagamento_ids': fields.related('lancamento_id', 'pagamento_ids', type='one2many', string=u'Pagamentos', relation='finan.lancamento'),

        #
        # Somas dos pagamentos
        #
        #'valor_pago': fields.function(_get_soma_pagamento, type='float', string=u'Valor quitado', store=True, digits=(18, 2)),
        #'total_juros': fields.function(_get_soma_pagamento, type='float', string=u'Total de juros', store=True, digits=(18, 2)),
        #'total_multa': fields.function(_get_soma_pagamento, type='float', string=u'Total de multa', store=True, digits=(18, 2)),
        #'total_desconto': fields.function(_get_soma_pagamento, type='float', string=u'Total de desconto', store=True, digits=(18, 2)),
        #'valor_saldo': fields.function(_saldo_lancamento, type='float', string=u'Saldo em aberto', store=True, digits=(18, 2), method=True),
        'valor_saldo': CampoDinheiro(string=u'Saldo em aberto'),
        'valor_previsto': CampoDinheiro(string=u'Valor previsto'),
        'data_ultimo_pagamento': fields.date(u'Último pagamento'),
        'parcial': fields.function(_get_parcial, type='boolean', string=u'Pago parcialmente', store=True, method=True),

        'conciliado': fields.boolean(u'Conciliado?', select=True),
        'lancamento_partner_id': fields.related('lancamento_id', 'partner_id', type='many2one', string=u'Cliente/Fornecedor', relation='res.partner'),
        'complemento': fields.char(u'Histórico', size=60),
        'valor_conciliacao': fields.function(_get_valor_conciliacao, type='float', string=u'Valor'),
        'debito_credito': fields.function(_get_debito_credito, type='integer', string=u'Déb/Créd'),
        'banco_contrapartida_id': fields.function(_get_banco_contrapartida, type='many2one', string=u'Contrapartida', relation='res.partner.bank'),
        'banco_formapagamento_id': fields.function(_get_banco_formapagamento_id, type='many2one', string=u'Forma de pagamento', relation='finan.formapagamento'),
        'banco_conta_id': fields.function(_get_banco_conta_id, type='many2one', string=u'Conta', relation='finan.conta'),
        'banco_partner_id': fields.function(_get_banco_partner_id, type='many2one', string=u'Cliente/Fornecedor', relation='res.partner'),
        'saldo_banco': fields.function(_soma_saldo, type='float', string=u'Saldo no banco', method=True),
        'saldo_banco_creditar': fields.function(_soma_saldo, type='float', string=u'Saldo no banco creditado', method=True),

        'remessa_id': fields.many2one('finan.remessa', u'Arquivo de remessa'),
        'retorno_id': fields.many2one('finan.retorno', u'Arquivo de retorno'),
        'retorno_item_id': fields.many2one('finan.retorno_item', u'Item do arquivo de retorno'),
        'retorno_item_ids': fields.one2many('finan.retorno_item', 'lancamento_id', u'Arquivos de retorno'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.lancamento', context=c),
        'conciliado': False,
        'data_documento': fields.date.today,
        'data_vencimento': fields.date.today,
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores

        company_pool = self.pool.get('res.company')
        company_obj = company_pool.browse(cr, uid, company_id)

        if company_obj.partner_id:
            valores['cnpj_cpf'] = company_obj.partner_id.cnpj_cpf
            valores['raiz_cnpj'] = company_obj.raiz_cnpj
        else:
            raise osv.except_osv(u'Inválido !', u'Não existe Cnpj/Cpf na Empresa selecionada!')

        return retorno

    def onchange_formapagamento_id(self, cr, uid, ids, formapagamento_id):
        valores = {}
        retorno = {'value': valores}
        if not formapagamento_id:
            return res

        formapagamento_obj = self.pool.get('finan.formapagamento').browse(cr, uid, formapagamento_id)
        valores['exige_numero'] = formapagamento_obj.exige_numero
        valores['conciliado'] = formapagamento_obj.conciliado

        return retorno

    def onchange_company_banco (self, cr, uid, ids, res_partner_bank_id):
        valores = {}
        retorno = {'value': valores}
        if not res_partner_bank_id:
            return res

        res_partner_bank_obj = self.pool.get('res.partner.bank').browse(cr, uid, res_partner_bank_id)
        valores['company_id'] = res_partner_bank_obj.company_id.id

        return retorno

    def onchange_data_quitacao(self, cr, uid, ids, data_quitacao, data_vencimento, context={}):
        #if not (data_quitacao and data_vencimento):
            #return

        #if data_quitacao != data_vencimento:
            #raise osv.except_osv(u'Aviso!', u'A data de quitação é diferente da data de vencimento!')

        return True

    def onchange_centrocusto_id(self, cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, partner_id=False, data_vencimento=False, data_documento=False, context={}):
        valores = {}
        res = {'value': valores}

        if not context:
            context = {}

        context.update({
            'partner_id': partner_id,
            'data_vencimento': data_vencimento,
            'data_documento': data_documento,
        })

        valor_documento = valor_documento or 0
        valor = valor or 0
        company_id = company_id or False
        conta_id = conta_id or False
        centrocusto_id = centrocusto_id or False

        if centrocusto_id:
            centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)

            #
            # Define os valores padrão para o rateio
            # outros valores podem vir do contexto
            #
            padrao = copy(context)
            padrao['company_id'] = company_id
            padrao['conta_id'] = conta_id
            padrao['centrocusto_id'] = centrocusto_id

            if ids:
                lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, ids[0], context=context)

                if getattr(lancamento_obj, 'contrato_id', False):
                    padrao['contrato_id'] = lancamento_obj.contrato_id.id

                    if getattr(lancamento_obj.contrato_id, 'imovel_id', False):
                        padrao['imovel_id'] = lancamento_obj.contrato_id.imovel_id.id
                        padrao['project_id'] = lancamento_obj.contrato_id.imovel_id.project_id.id

                if getattr(lancamento_obj, 'contrato_imovel_id', False):
                    padrao['contrato_id'] = lancamento_obj.contrato_imovel_id.id
                    padrao['imovel_id'] = lancamento_obj.contrato_imovel_id.imovel_id.id
                    padrao['project_id'] = lancamento_obj.contrato_imovel_id.imovel_id.project_id.id

            rateio = {}
            rateio = self.pool.get('finan.centrocusto').realiza_rateio(cr, uid, [centrocusto_id], context=context, rateio=rateio, padrao=padrao, valor=valor_documento)
            #print('rateio', rateio)

            campos = self.pool.get('finan.centrocusto').campos_rateio(cr, uid)

            dados = []
            self.pool.get('finan.centrocusto').monta_dados(rateio, campos=campos, lista_dados=dados, valor=valor_documento)
            valores['rateio_ids'] = dados

            #print('rateio', dados)

            ###rateio_ids = []
            ###valores['rateio_ids'] = rateio_ids

            ###for rateio_obj in centrocusto_obj.rateio_ids:
                ###dados = {
                    ###'centrocusto_id': rateio_obj.centrocusto_id.id,
                    ###'porcentagem': rateio_obj.porcentagem,
                    ###'valor_documento': valor_documento * (rateio_obj.porcentagem / 100.00),
                    ###'valor': valor * (rateio_obj.porcentagem / 100.00),
                ###}

                ###if rateio_obj.company_id:
                    ###dados['company_id'] = rateio_obj.company_id.id
                ###else:
                    ###dados['company_id'] = company_id

                ###if rateio_obj.conta_id:
                    ###dados['conta_id'] = rateio_obj.conta_id.id
                ###else:
                    ###dados['conta_id'] = conta_id

                ###rateio_ids.append([0, False, dados])
        #
        # Força a geração de pelo menos 1 registro para a conta financeira
        #
        else:
            rateio_ids = [[5, False, False]]
            valores['rateio_ids'] = rateio_ids

            dados = {
                'centrocusto_id': False,
                'porcentagem': 100,
                'valor_documento': valor_documento,
                'valor': valor,
                'conta_id': conta_id,
                'company_id': company_id,
            }

            rateio_ids.append([0, False, dados])

        return res

    def onchange_conta_id(self, cr, uid, ids, conta_id, company_id, centrocusto_id, valor_documento, valor, partner_id=False, data_vencimento=False, data_documento=False):
        valores = {}
        res = {'value': valores}
        conta_id = conta_id or False

        #print('entrou aqui na conta_id')

        context = {
            'partner_id': partner_id,
            'data_vencimento': data_vencimento,
            'data_documento': data_documento,
        }

        if conta_id:
            conta_obj = self.pool.get('finan.conta').browse(cr, uid, conta_id)
            valores['exige_centro_custo'] = conta_obj.exige_centro_custo

            rateio = self.onchange_centrocusto_id(cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, partner_id, data_vencimento, data_documento)
            if 'value' in rateio:
                valores['rateio_ids'] = rateio['value']['rateio_ids']

        return res

    def recalcula_rateio(self, cr, uid, lancamento_id, context=None):
        lancamento_obj = self.browse(cr, uid, lancamento_id)

        dados = []
        if lancamento_obj.rateio_ids:
            for rateio_obj in lancamento_obj.rateio_ids:
                rateio_obj.valor_documento = lancamento_obj.valor_documento * (rateio_obj.porcentagem / 100.00)
                rateio_obj.valor = lancamento_obj.valor * (rateio_obj.porcentagem / 100.00)

                dados.append(
                    [
                        1,
                        rateio_obj.id,
                        {
                            'valor_documento': rateio_obj.valor_documento,
                            'valor': rateio_obj.valor,
                        }
                    ]
                )

        return dados

    def verifica_valor_rateio(self, cr, uid, ids, vals, context=None):
        if 'rateio_ids' not in vals or not vals['rateio_ids']:
            return

        rateios = vals['rateio_ids']
        rateios_alterados_porcentagem = []

        #print('rateios', rateios)

        total_porcentagem = D('0')
        for operacao, rateio_id, valores in rateios:
            #
            # Cada lanc_item tem o seguinte formato
            # [operacao, id_original, valores_dos_campos]
            #
            # operacao pode ser:
            # 0 - criar novo registro (no caso aqui, vai ser ignorado)
            # 1 - alterar o registro
            # 2 - excluir o registro (também vai ser ignorado)
            # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
            # 4 - vincular a um registro existente
            # 5 - excluiu todos a vai incluir todos de novo

            #print(operacao, 'operacao', rateio_id, valores)

            if operacao == 5:
                excluido_ids = self.pool.get('finan.lancamento.rateio').search(cr, uid, [('lancamento_id', 'in', ids)])
                rateios_alterados_porcentagem += excluido_ids

            if operacao == 2:
                rateios_alterados_porcentagem += [rateio_id]

            if operacao in [0, 1] and valores and 'porcentagem' in valores:
                if operacao == 1:
                    rateios_alterados_porcentagem += [rateio_id]

                total_porcentagem += D(str(valores['porcentagem'] or 0))

        #
        # Ajusta com os possíveis não alterados
        #
        rateio_ids = []
        if ids and ids[0]:
            rateio_pool = self.pool.get('finan.lancamento.rateio')
            rateio_ids = rateio_pool.search(cr, uid, [('lancamento_id', '=', ids[0]), ('id', 'not in', rateios_alterados_porcentagem)])

            for rateio_obj in rateio_pool.browse(cr, uid, rateio_ids):
                total_porcentagem += D(str(rateio_obj.porcentagem or 0))

        total_porcentagem = total_porcentagem.quantize(D('0.01'))
        #print(rateios_alterados_valor, rateios_alterados_valor_documento, rateio_ids, total_valor_documento, total_valor)

        if total_porcentagem and total_porcentagem != 100:
            raise osv.except_osv(u'Inválido !', u'A soma dos percentuais deveria ser 100%; deu ' + formata_valor(total_porcentagem) + '%')

    def verifica_fechamento_caixa(self, cr, uid, ids, vals={}, context=None):
        if isinstance(ids, (list, tuple)):
            if ids and ids[0]:
                lancamento_obj = self.browse(cr, uid, ids[0])
            else:
                lancamento_obj = None
        else:
            lancamento_obj = self.browse(cr, uid, ids)

        #
        # Só é necessário verificar o caixa se a data de quitação, a data de crédio
        # ou o valor estejam sendo alterados
        #
        if (not 'data_quitacao' in vals) and (not 'valor' in vals) and (not 'res_partner_bank_id' in vals):
            return

        if 'res_partner_bank_id' in vals:
            res_partner_bank_id = vals['res_partner_bank_id']
        elif lancamento_obj and lancamento_obj.res_partner_bank_id:
            res_partner_bank_id = lancamento_obj.res_partner_bank_id.id
        else:
           res_partner_bank_id = False

        if 'tipo' in vals:
            tipo = vals['tipo']
        elif lancamento_obj:
            tipo = lancamento_obj.tipo
        else:
            tipo = ''

        if 'data_quitacao' in vals:
            data_quitacao = vals['data_quitacao']
        elif lancamento_obj:
            data_quitacao = lancamento_obj.data_quitacao
        else:
            data_quitacao = False

        if 'data' in vals:
            data = vals['data']
        elif lancamento_obj:
            data = lancamento_obj.data
        else:
            data = False

        if 'res_partner_bank_creditar_id' in vals:
            res_partner_bank_creditar_id = vals['res_partner_bank_creditar_id']
        elif lancamento_obj and lancamento_obj.res_partner_bank_creditar_id:
            res_partner_bank_creditar_id = lancamento_obj.res_partner_bank_creditar_id.id
        else:
            res_partner_bank_creditar_id = False

        saldo_pool = self.pool.get('finan.saldo')

        #
        # Abre uma exceção para poder alterar o número original do contrato e
        # possivelmente o valor original do contrato, ou ainda a data de vencimento original
        #
        #print('valores novos', vals)
        if ('numero_documento_original' in vals or 'valor_original_contrato' in vals or 'contrato_id' in vals or 'data_vencimento_original') and len(vals) == 1:
            pass

        else:
            #
            # Verifica a data
            #
            if tipo in ('T', 'E', 'S'):
                saldo_id = saldo_pool.search(cr, 1, [('res_partner_bank_id', '=', res_partner_bank_id), ('data', '>=', data), ('fechado', '=', True)], order='data desc', limit=1)

                banco_obj = self.pool.get('res.partner.bank').browse(cr, 1, res_partner_bank_id)

                if len(saldo_id):
                    raise osv.except_osv(u'Erro!', u'É proibido fazer um lançamento de {tipo} para a data {data}, no banco {banco}, pois esse movimento já foi fechado!'.format(data=formata_data(data), banco=banco_obj.name, tipo=TIPO_LANCAMENTO_DICT[tipo]))

                if res_partner_bank_creditar_id:
                    saldo_id = saldo_pool.search(cr, 1, [('res_partner_bank_id', '=', res_partner_bank_creditar_id), ('data', '>=', data), ('fechado', '=', True)], order='data desc', limit=1)

                    banco_obj = self.pool.get('res.partner.bank').browse(cr, 1, res_partner_bank_creditar_id)

                    if len(saldo_id):
                        raise osv.except_osv(u'Erro!', u'É proibido fazer um lançamento de {tipo} para a data {data}, no banco {banco}, pois esse movimento já foi fechado!'.format(data=formata_data(data), banco=banco_obj.name, tipo=TIPO_LANCAMENTO_DICT[tipo]))

            elif tipo in ('PP', 'PR'):
                saldo_id = saldo_pool.search(cr, 1, [('res_partner_bank_id', '=', res_partner_bank_id), ('data', '>=', data_quitacao), ('fechado', '=', True)], order='data desc', limit=1)

                #print('data_quitacao', data_quitacao)
                #print('data_quitacao', vals)

                banco_obj = self.pool.get('res.partner.bank').browse(cr, 1, res_partner_bank_id)

                if len(saldo_id):
                    raise osv.except_osv(u'Erro!', u'É proibido fazer um lançamento de {tipo} para a data {data}, no banco {banco}, pois esse movimento já foi fechado!'.format(data=formata_data(data_quitacao), banco=banco_obj.name, tipo=TIPO_LANCAMENTO_DICT[tipo]))

            elif tipo in ('P', 'R'):
                saldo_id = saldo_pool.search(cr, 1, [('res_partner_bank_id', '=', res_partner_bank_id), ('data', '>=', data_quitacao), ('fechado', '=', True)], order='data desc', limit=1)

                banco_obj = self.pool.get('res.partner.bank').browse(cr, 1, res_partner_bank_id)

                if len(saldo_id):
                    raise osv.except_osv(u'Erro!', u'É proibido fazer um lançamento para a data {data}, no banco {banco}, pois esse movimento já foi fechado!'.format(data=formata_data(data_quitacao), banco=banco_obj.name))

    def ajusta_data_quitacao(self, cr, uid, ids, vals={}, context={}):
        for id in ids:
            cr.execute(SQL_AJUSTA_QUITACAO.replace('%d', str(id)))

        return True

    def verifica_duplicidade(self, cr, uid, ids, vals, operacao='I', context=None):
        if isinstance(ids, (list, tuple)):
            if ids and ids[0]:
                lancamento_obj = self.browse(cr, uid, ids[0])
            else:
                lancamento_obj = None
        else:
            lancamento_obj = self.browse(cr, uid, ids)

        if 'numero_documento' in vals:
            numero_documento = vals['numero_documento']
        elif lancamento_obj and lancamento_obj.numero_documento:
            numero_documento = lancamento_obj.numero_documento
        else:
            numero_documento = ''

        if 'partner_id' in vals:
            partner_id = vals['partner_id']
        elif lancamento_obj and lancamento_obj.partner_id:
            partner_id = lancamento_obj.partner_id.id
        else:
            partner_id = False

        if 'tipo' in vals:
            tipo = vals['tipo']
        elif lancamento_obj:
            tipo = lancamento_obj.tipo
        else:
            tipo = ''

        #
        # Verifica a data
        #
        if tipo in ('R', 'P'):
            lancamento_ids = self.search(cr, uid, [('tipo', '=', tipo), ('numero_documento', '=', numero_documento), ('partner_id', '=', partner_id)])

            if operacao == 'I' and lancamento_ids:
                if tipo == 'R':
                    raise osv.except_osv(u'Erro!', u'Número do documento “{numero}” e cliente já existem!'.format(numero=numero_documento))
                else:
                    raise osv.except_osv(u'Erro!', u'Número do documento “{numero}” e fornecedor já existem!'.format(numero=numero_documento))

            elif operacao == 'A' and lancamento_ids:
                if partner_id != lancamento_obj.partner_id.id or numero_documento != lancamento_obj.numero_documento:
                    if tipo == 'R':
                        raise osv.except_osv(u'Alteração não permitida!', u'Número do documento “{numero}” e cliente já existem!'.format(numero=numero_documento))
                    else:
                        raise osv.except_osv(u'Alteração não permitida!', u'Número do documento “{numero}” e fornecedor já existem!'.format(numero=numero_documento))

    def create(self, cr, uid, vals, context={}):
        #print('dados')
        #print(vals)
        self.verifica_valor_rateio(cr, uid, [], vals)
        self.verifica_fechamento_caixa(cr, uid, [], vals)
        #self.verifica_duplicidade(cr, uid, [], vals, 'I')

        res = super(finan_lancamento, self).create(cr, uid, vals, context)

        self.ajusta_data_quitacao(cr, uid, [res], context)

        #
        # Ajusta situação dos lançamentos a receber e a pagar nos pagamentos
        #
        ajustar_situacao = []
        for lanc_obj in self.browse(cr, uid, [res]):
            if lanc_obj.lancamento_id and lanc_obj.lancamento_id.id not in ajustar_situacao:
                ajustar_situacao.append(lanc_obj.lancamento_id.id)
        self.ajusta_data_quitacao(cr, uid, ajustar_situacao, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        #saldo_pool =  self.pool.get('finan.saldo')

        #print('vai gravar')
        #print(vals)

        self.verifica_valor_rateio(cr, uid, ids, vals)
        if 'conciliacao' not in context:
            self.verifica_fechamento_caixa(cr, uid, ids, vals)
        #self.verifica_duplicidade(cr, uid, ids, vals, 'A')

        res = super(finan_lancamento, self).write(cr, uid, ids, vals, context)

        self.ajusta_data_quitacao(cr, uid, ids, context)
        #self.acao_demorada_ajusta_situacao_juros(cr, uid, ids, context)

        #
        # Ajusta situação dos lançamentos a receber e a pagar nos pagamentos
        #
        ajustar_situacao = []
        for lanc_obj in self.browse(cr, uid, ids):
            if lanc_obj.lancamento_id and lanc_obj.lancamento_id.id not in ajustar_situacao:
                ajustar_situacao.append(lanc_obj.lancamento_id.id)

        if len(ajustar_situacao):
            self.ajusta_data_quitacao(cr, uid, ajustar_situacao, context)
            #self.acao_demorada_ajusta_situacao_juros(cr, uid, ajustar_situacao, context)

        #saldo_pool.cria_fechamentos_gerais(cr, uid, ids, context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        self.verifica_fechamento_caixa(cr, uid, ids, vals={})

        ajustar_situacao = []
        excluir_tambem = []

        for lanc_obj in self.browse(cr, uid, ids):
            if lanc_obj.lancamento_id and lanc_obj.lancamento_id.id not in ajustar_situacao:
                ajustar_situacao.append(lanc_obj.lancamento_id.id)

            #
            # No caso de estar excluindo um lote, excluir também os pagamentos vinculados
            # ao lote, mas não as dívidas;
            # No caso de lançamento a receber ou a pagar, excluir os pagamentos vinculados
            #
            #print(lanc_obj.id, lanc_obj.tipo, TIPO_LANCAMENTO_LOTE_PAGAMENTO, lanc_obj.tipo == TIPO_LANCAMENTO_LOTE_PAGAMENTO)

            if str(lanc_obj.tipo) in [TIPO_LANCAMENTO_LOTE_PAGAMENTO, TIPO_LANCAMENTO_LOTE_RECEBIMENTO]:
                #print(lanc_obj.pagamento_ids)
                for pag_obj in lanc_obj.pagamento_ids:
                    #print('a', pag_obj.id, pag_obj.tipo)
                    excluir_tambem.append(pag_obj.id)

                for div_obj in lanc_obj.lote_pago_ids:
                    #print('b', div_obj.id, div_obj.tipo)
                    ajustar_situacao.append(div_obj.id)

            elif str(lanc_obj.tipo) in ['P', 'R']:
                for pag_obj in lanc_obj.pagamento_ids:
                    #print('b', pag_obj.id, pag_obj.tipo)
                    if str(pag_obj.tipo) in [TIPO_LANCAMENTO_PAGAMENTO_RECEBIDO, TIPO_LANCAMENTO_PAGAMENTO_PAGO]:
                        excluir_tambem.append(pag_obj.id)

        #for lanc_obj in self.browse(cr, uid, ids):
            #if lanc_obj.situacao != ['A vencer', 'Vencido', 'Vence hoje']:
                #raise osv.except_osv(u'Exclusão não permitida!', u'É proibido excluir um lançamento que tenha sido quitado, baixado ou conciliado!')

        #
        # Exclui agora os vinculados, verificando fechamento de caixa etc. etc.
        #
        #print('excluir tambem', excluir_tambem)
        for lanc_id in excluir_tambem:
            self.pool.get('finan.lancamento').unlink(cr, uid, [lanc_id], context)

        #
        # Agora, exclui o próprio lançamento
        #
        res = super(finan_lancamento, self).unlink(cr, uid, ids, context)

        #print('ajustar situacao', ajustar_situacao)
        self.ajusta_data_quitacao(cr, uid, ajustar_situacao, context)
        #self.acao_demorada_ajusta_situacao_juros(cr, uid, ajustar_situacao, context)

        return res

    def copy(self, cr, uid, id, default={}, context={}):
        #print('default', default)

        default.update({
            'numero_documento': '',
            'nosso_numero': '',
            'carteira_id': False,
            'saldo_banco': False,
            'saldo_banco_creditar': False,
        })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res

    def personaliza_boleto(self, cr, uid, lancamento_obj, boleto):
        #
        # Função para ser herdada pelas customizações dos cliente
        # para ajustar campos no boleto conforme as situações
        #
        return boleto

    def gerar_boleto(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        lancamento_obj = self.browse(cr, uid, id)

        #print('vai gerar boleto do lancamento id ', lancamento_obj.id)

        if not lancamento_obj.carteira_id:
            return

        if (not lancamento_obj.nosso_numero) or D(lancamento_obj.nosso_numero) == 0:
            #
            # Força buscar a carteira no banco novamente, pra trazer o
            # último nosso número
            #
            carteira_obj = self.pool.get('finan.carteira').browse(cr, uid, lancamento_obj.carteira_id.id)
            if carteira_obj.nosso_numero_pelo_banco:
                nosso_numero = 0
            else:
                nosso_numero = D(carteira_obj.ultimo_nosso_numero) + 1

            if lancamento_obj.provisionado:
                self.write(cr, uid, [lancamento_obj.id], {'nosso_numero': str(nosso_numero), 'data_boleto': datetime.now().strftime('%Y-%m-%d'), 'provisionado': False, 'data_documento': datetime.now().strftime('%Y-%m-%d')})
                lancamento_obj.data_documento = datetime.now().strftime('%Y-%m-%d')
            else:
                self.write(cr, uid, [lancamento_obj.id], {'nosso_numero': str(nosso_numero), 'data_boleto': datetime.now().strftime('%Y-%m-%d'), 'provisionado': False})
            self.pool.get('finan.carteira').write(cr, 1, [carteira_obj.id], {'ultimo_nosso_numero': str(nosso_numero)})
            cr.commit()
        else:
            nosso_numero = D(lancamento_obj.nosso_numero)

        boleto = Boleto()

        if lancamento_obj.carteira_id.res_partner_bank_id.bank_bic == '104':
            boleto.local_pagamento = u'PREFERENCIALMENTE NAS CASAS LOTÉRICAS ATÉ O VALOR LIMITE'

        elif lancamento_obj.carteira_id.res_partner_bank_id.bank_bic == '085':
            boleto.local_pagamento = u'Pagar preferencialmente nas cooperativas do Sistema CECRED'

        #
        # Banco
        #
        boleto.banco = BANCO_CODIGO[lancamento_obj.carteira_id.res_partner_bank_id.bank_bic]
        boleto.banco.carteira = lancamento_obj.carteira_id.carteira or ''
        boleto.banco.modalidade = lancamento_obj.carteira_id.modalidade or ''
        boleto.identificacao = 'ix_' + base_repr(int(lancamento_obj.id), 36)

        #
        # Beneficiario
        #
        beneficiario_obj = lancamento_obj.carteira_id.res_partner_bank_id.partner_id
        boleto.beneficiario.nome = beneficiario_obj.razao_social or beneficiario_obj.name or ''
        boleto.beneficiario.cnpj_cpf = beneficiario_obj.cnpj_cpf or ''
        boleto.beneficiario.endereco = beneficiario_obj.endereco or ''
        boleto.beneficiario.numero = beneficiario_obj.numero or ''
        boleto.beneficiario.complemento = beneficiario_obj.complemento or ''
        boleto.beneficiario.bairro = beneficiario_obj.bairro or ''
        boleto.beneficiario.cidade = beneficiario_obj.municipio_id.nome or ''
        boleto.beneficiario.estado = beneficiario_obj.municipio_id.estado_id.uf or ''
        boleto.beneficiario.cep = beneficiario_obj.cep or ''

        boleto.beneficiario.agencia.numero = lancamento_obj.carteira_id.res_partner_bank_id.agencia or ''
        boleto.beneficiario.agencia.digito = lancamento_obj.carteira_id.res_partner_bank_id.agencia_digito or ''
        boleto.beneficiario.conta.numero = lancamento_obj.carteira_id.res_partner_bank_id.acc_number or ''
        boleto.beneficiario.conta.digito = lancamento_obj.carteira_id.res_partner_bank_id.conta_digito or ''
        boleto.beneficiario.codigo_beneficiario.numero = lancamento_obj.carteira_id.beneficiario or ''
        boleto.beneficiario.codigo_beneficiario.digito = lancamento_obj.carteira_id.beneficiario_digito or ''
        boleto.beneficiario.conta.convenio = lancamento_obj.carteira_id.res_partner_bank_id.codigo_convenio or ''

        #
        # Pagador e endereço de cobrança
        #
        pagador_obj = lancamento_obj.partner_id
        boleto.pagador.nome = pagador_obj.razao_social or pagador_obj.name or ''
        boleto.pagador.cnpj_cpf = pagador_obj.cnpj_cpf or ''
        boleto.pagador.endereco = pagador_obj.endereco or ''
        boleto.pagador.numero = pagador_obj.numero or ''
        boleto.pagador.complemento = pagador_obj.complemento or ''
        boleto.pagador.bairro = pagador_obj.bairro or ''

        try:
            boleto.pagador.cidade = pagador_obj.municipio_id.nome or ''
            boleto.pagador.estado = pagador_obj.municipio_id.estado_id.uf or ''
        except:
            raise osv.except_osv(u'Inválido !', u'Sem município ou incompleto para o cliente “{cliente}”!'.format(cliente= boleto.pagador.nome))

        boleto.pagador.cep = pagador_obj.cep or ''

        modelo_endereco = u'''
<u>EMITENTE</u>:<br/>
${ beneficiario.nome }<br/>
${ beneficiario.endereco_numero_complemento }<br/>
${ beneficiario.bairro }<br/>
${ beneficiario.cidade } - ${ beneficiario.estado }<br/>
${ beneficiario.cep }<br/>
<br/>
<br/>
<br/>
<u>CLIENTE</u>:<br/>
${ pagador.nome }<br/>
${ pagador.endereco_numero_complemento }<br/>
${ pagador.bairro }<br/>
${ pagador.cidade } - ${ pagador.estado }<br/>
${ pagador.cep }<br/>
'''
        contrato_obj = getattr(lancamento_obj, 'contrato_id', False)

        if contrato_obj:
            if contrato_obj.res_partner_address_id:
                endereco_obj = contrato_obj.res_partner_address_id
                boleto.pagador.endereco = endereco_obj.endereco or ''
                boleto.pagador.numero = endereco_obj.numero or ''
                boleto.pagador.complemento = endereco_obj.complemento or ''
                boleto.pagador.bairro = endereco_obj.bairro or ''
                try:
                    boleto.pagador.cidade = endereco_obj.municipio_id.nome or ''
                    boleto.pagador.estado = endereco_obj.municipio_id.estado_id.uf or ''
                except:
                    raise osv.except_osv(u'Inválido !', u'Endereço de cobrança sem município ou incompleto para o cliente “{cliente}”!'.format(cliente= boleto.pagador.nome))

                boleto.pagador.cep = endereco_obj.cep or ''

        elif len(pagador_obj.address) > 0 and pagador_obj.address[0].endereco:
            endereco_obj = pagador_obj.address[0]

            boleto.pagador.endereco = endereco_obj.endereco or ''
            boleto.pagador.numero = endereco_obj.numero or ''
            boleto.pagador.complemento = endereco_obj.complemento or ''
            boleto.pagador.bairro = endereco_obj.bairro or ''
            try:
                boleto.pagador.cidade = endereco_obj.municipio_id.nome or ''
                boleto.pagador.estado = endereco_obj.municipio_id.estado_id.uf or ''
            except:
                raise osv.except_osv(u'Inválido !', u'Endereço de cobrança sem município ou incompleto para o cliente “{cliente}”!'.format(cliente= boleto.pagador.nome))

            boleto.pagador.cep = endereco_obj.cep or ''

        else:
            boleto.pagador.endereco = pagador_obj.endereco or ''
            boleto.pagador.numero = pagador_obj.numero or ''
            boleto.pagador.complemento = pagador_obj.complemento or ''
            boleto.pagador.bairro = pagador_obj.bairro or ''
            try:
                boleto.pagador.cidade = pagador_obj.municipio_id.nome or ''
                boleto.pagador.estado = pagador_obj.municipio_id.estado_id.uf or ''
            except:
                raise osv.except_osv(u'Inválido !', u'Endereço sem município ou incompleto para o cliente “{cliente}”!'.format(cliente= boleto.pagador.nome))

            boleto.pagador.cep = pagador_obj.cep or ''

        #
        # Acresenta as tags de template do Mako
        #
        template_imports = [
            'from pybrasil.base import (tira_acentos, primeira_maiuscula)',
            'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
            'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade, formata_valor)',
        ]
        template = Template(modelo_endereco.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
        texto = template.render(beneficiario=boleto.beneficiario, pagador=boleto.pagador)
        boleto.endereco_cobranca = texto.decode('utf-8')

        #
        # Retorna o endereço do boleto para o do cadastro
        #
        boleto.pagador.endereco = pagador_obj.endereco or ''
        boleto.pagador.numero = pagador_obj.numero or ''
        boleto.pagador.complemento = pagador_obj.complemento or ''
        boleto.pagador.bairro = pagador_obj.bairro or ''
        boleto.pagador.cidade = pagador_obj.municipio_id.nome or ''
        boleto.pagador.estado = pagador_obj.municipio_id.estado_id.uf or ''
        boleto.pagador.cep = pagador_obj.cep or ''

        boleto.nosso_numero = str(nosso_numero)

        #
        # Gera boleto com juros e multa já embutido, em caso de atraso
        #
        if context.get('atualizar', False):
            if 'data' in context:
                data = parse_datetime(context['data']).date()
            else:
                data =  hoje()
            boleto.dias_atraso = data - parse_datetime(lancamento_obj.data_vencimento).date()
            boleto.dias_atraso = boleto.dias_atraso.days

            if boleto.dias_atraso > 0:
                boleto.data_vencimento = data
                boleto.instrucoes.append(u'Valor original: R$ ' + formata_valor(lancamento_obj.valor_documento) + u' - Vencimento original: ' + formata_data(lancamento_obj.data_vencimento) )
            else:
                boleto.dias_atraso = 0
                boleto.data_vencimento = datetime.strptime(lancamento_obj.data_vencimento, '%Y-%m-%d').date()

        else:
            boleto.data_vencimento = datetime.strptime(lancamento_obj.data_vencimento, '%Y-%m-%d').date()

        #if lancamento_obj.sped_documento_id and lancamento_obj.nf_numero > 0:
            #boleto.documento.numero = str(lancamento_obj.nf_numero)
            #boleto.documento.data = datetime.strptime(lancamento_obj.nf_data, '%Y-%m-%d %H:%M:%S').date()
        #else:
        boleto.documento.numero = lancamento_obj.numero_documento

        if lancamento_obj.numero_documento_original:
            boleto.documento.numero_original = lancamento_obj.numero_documento_original
        else:
            boleto.documento.numero_original = lancamento_obj.numero_documento

        boleto.documento.data = datetime.strptime(lancamento_obj.data_documento, '%Y-%m-%d').date()

        #print('context', context)
        if context.get('boleto_valor_saldo', False):
            boleto.documento.valor = D(str(lancamento_obj.valor_saldo))
        else:
            boleto.documento.valor = D(str(lancamento_obj.valor_documento))

        boleto.data_processamento = datetime.now()

        if lancamento_obj.carteira_id.porcentagem_juros:
            boleto.data_juros = boleto.data_vencimento + timedelta(days=1)
            porcentagem_juros = D(str(lancamento_obj.carteira_id.porcentagem_juros))
            boleto.valor_juros = boleto.documento.valor * porcentagem_juros / D('100.00')
            boleto.valor_juros = boleto.valor_juros.quantize(D('0.01'))

            porcentagem_juros = porcentagem_juros.quantize(D('0.0001'))
            lancamento_obj.porcentagem_juros = D(lancamento_obj.porcentagem_juros or 0).quantize(D('0.0001'))
            boleto.percentual_juros = porcentagem_juros

            if boleto.dias_atraso <= 0 and (lancamento_obj.data_juros != str(boleto.data_juros) or lancamento_obj.porcentagem_juros != porcentagem_juros):
                self.write(cr, uid, [lancamento_obj.id], {'data_juros': str(boleto.data_juros), 'porcentagem_juros': porcentagem_juros})

            #
            # 08/07/2016 - 10:42 - Para a Exata
            #
            # O SICOOB quer porque quer que o juros seja informado em meses, não em dias, tem que ser de 1% ao mês
            #
            if lancamento_obj.carteira_id.res_partner_bank_id.bank_bic == '756':
                porcentagem_juros = D(1)
                boleto.percentual_juros = porcentagem_juros
                valor_juros_sicoob = boleto.documento.valor * porcentagem_juros / D('100.00')
                #valor_juros_sicoob = valor_juros_sicoob.quantize(D('0.01'))

                boleto.instrucoes.append(u'A partir de ' + datetime.strftime(boleto.data_juros, '%d/%m/%Y') + u' cobrar R$ ' + formata_valor(valor_juros_sicoob) + ' (' + valor_por_extenso_unidade(valor_juros_sicoob) + u') de juros de mora por mês;')

            else:
                boleto.instrucoes.append(u'A partir de ' + datetime.strftime(boleto.data_juros, '%d/%m/%Y') + u' cobrar R$ ' + formata_valor(boleto.valor_juros) + ' (' + valor_por_extenso_unidade(boleto.valor_juros) + u') de juros de mora por dia;')

        if lancamento_obj.carteira_id.porcentagem_multa:
            boleto.data_multa = boleto.data_vencimento + timedelta(days=1)
            porcentagem_multa = D(str(lancamento_obj.carteira_id.porcentagem_multa))
            boleto.valor_multa = boleto.documento.valor * porcentagem_multa / D('100.00')
            boleto.valor_multa = boleto.valor_multa.quantize(D('0.01'))
            boleto.percentual_multa = porcentagem_multa

            porcentagem_multa = porcentagem_multa.quantize(D('0.0001'))
            lancamento_obj.porcentagem_multa = D(lancamento_obj.porcentagem_multa or 0).quantize(D('0.0001'))

            if boleto.dias_atraso <= 0 and (lancamento_obj.data_multa != str(boleto.data_multa) or lancamento_obj.porcentagem_multa != porcentagem_multa):
                self.write(cr, uid, [lancamento_obj.id], {'data_multa': str(boleto.data_multa), 'porcentagem_multa': porcentagem_multa})

            boleto.instrucoes.append(u'A partir de ' + datetime.strftime(boleto.data_multa, '%d/%m/%Y') + ' cobrar R$ ' + formata_valor(boleto.valor_multa) + ' (' + valor_por_extenso_unidade(boleto.valor_multa) + ') de multa;')

        if lancamento_obj.porcentagem_desconto and lancamento_obj.data_desconto:
            boleto.data_desconto = datetime.strptime(lancamento_obj.data_desconto, '%Y-%m-%d').date()
            porcentagem_desconto = D(str(lancamento_obj.porcentagem_desconto))
            boleto.valor_desconto = boleto.documento.valor * porcentagem_desconto / D('100.00')
            boleto.valor_desconto = boleto.valor_desconto.quantize(D('0.01'))
            boleto.instrucoes.append(u'Até ' + datetime.strftime(boleto.data_desconto, '%d/%m/%Y') + ' conceder R$ ' + formata_valor(boleto.valor_desconto) + ' (' + valor_por_extenso_unidade(boleto.valor_desconto) + ') de desconto;')

        if lancamento_obj.carteira_id.dias_protesto:
            boleto.dias_protesto = lancamento_obj.carteira_id.dias_protesto
            boleto.data_protesto = boleto.data_vencimento + timedelta(days=boleto.dias_protesto)
            boleto.instrucoes.append(u'Enviar para protesto a partir de ' + datetime.strftime(boleto.data_protesto, '%d/%m/%Y') + ' (' + data_por_extenso(boleto.data_protesto) + ');')

        if lancamento_obj.historico:
            boleto.descricao = lancamento_obj.historico.split(';')

        if lancamento_obj.carteira_id.res_partner_bank_id.bank_bic == '085':
            boleto.instrucoes.append(u'Ápos vencimento acesse o site: www.viacredi.coop.br para atualizar o boleto')

        if context.get('taxa_boleto', False):
            if lancamento_obj.carteira_id.taxa_boleto:
                valor_taxa_boleto =  D(str(lancamento_obj.carteira_id.taxa_boleto))
                boleto.documento.valor += valor_taxa_boleto
                self.write(cr, uid, [lancamento_obj.id], {'outros_acrescimos': valor_taxa_boleto})

        if context.get('atualizar', False) and boleto.dias_atraso > 0:
            boleto.documento.valor += D(boleto.valor_multa)
            boleto.documento.valor += D(boleto.valor_juros) * boleto.dias_atraso
            #boleto.imprime_juros_multa = boleto.valor_multa
            #boleto.imprime_juros_multa += boleto.valor_juros * boleto.dias_atraso
            boleto.data_multa = None
            boleto.valor_multa = 0

            instrucao_multa = -1
            for i in range(len(boleto.instrucoes)):
                if 'multa' in boleto.instrucoes[i]:
                    instrucao_multa = i
            if instrucao_multa != -1:
                boleto.instrucoes.pop(instrucao_multa)

        if lancamento_obj.carteira_id.instrucao:
            boleto.instrucoes.append(lancamento_obj.carteira_id.instrucao)

        template_imports = [
            'from pybrasil.base import (tira_acentos, primeira_maiuscula)',
            'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
            'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade, formata_valor)',
        ]
        for i in range(len(boleto.descricao)):
            template = Template(boleto.descricao[i].encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
            texto = template.render(beneficiario=boleto.beneficiario, pagador=boleto.pagador, lancamento=lancamento_obj)
            boleto.descricao[i] = texto.decode('utf-8')

        for i in range(len(boleto.instrucoes)):
            template = Template(boleto.instrucoes[i].encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
            texto = template.render(beneficiario=boleto.beneficiario, pagador=boleto.pagador, lancamento=lancamento_obj)
            boleto.instrucoes[i] = texto.decode('utf-8')

        boleto = self.personaliza_boleto(cr, uid, lancamento_obj, boleto)

        if not 'evita_pdf' in context:
            pdf = gera_boletos_pdf([boleto])
            nome_boleto = 'boleto_' + lancamento_obj.carteira_id.res_partner_bank_id.bank_name + '_' + str(nosso_numero) + '.pdf'

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.lancamento'), ('res_id', '=', lancamento_obj.id), ('name', '=', nome_boleto)])
            #
            # Apaga os boletos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_boleto,
                'datas_fname': nome_boleto,
                'res_model': 'finan.lancamento',
                'res_id': lancamento_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        return boleto

    def enviar_email_boleto(self, cr, uid, ids, context={}):

        lancamento_pool = self.pool.get('finan.lancamento')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)
        mail_pool = self.pool.get('mail.message')
        attachment_pool = self.pool.get('ir.attachment')

        #
        # Verificamos se tem modelo pré-definido
        #
        template_pool = self.pool.get('email.template')
        template_ids = template_pool.search(cr, 1, [('name', '=', 'Boleto emitido'), ('model_id.model', '=', 'finan.lancamento')])

        if user_obj.user_email:
            for lancamento_obj in lancamento_pool.browse(cr, uid, ids):
                if lancamento_obj.partner_id.email_nfe:

                    if template_ids:
                        dados = template_pool.generate_email(cr, 1, template_ids[0], lancamento_obj.id, context=context)

                        if 'attachment_ids' in dados:
                            del dados['attachment_ids']

                        dados.update({
                            'model': 'finan.lancamento',
                            'res_id': lancamento_obj.id,
                            'user_id': uid,
                            'email_to': lancamento_obj.partner_id.email_nfe or '',
                            #'email_to': 'william@erpintegra.com.br',
                            'email_from': user_obj.user_email,
                            'date': str(fields.datetime.now()),
                            'reply_to': user_obj.user_email,
                            'state': 'outgoing',
                        })

                    else:
                        dados = {
                            'subject':  u'Envio de Boleto',
                            'model': 'finan.lancamento',
                            'res_id': lancamento_obj.id,
                            'user_id': uid,
                            'email_to': lancamento_obj.partner_id.email_nfe or '',
                            #'email_to': 'william@erpintegra.com.br',
                            'email_from': user_obj.user_email,
                            'date': str(fields.datetime.now()),
                            'headers': '{}',
                            'email_cc': '',
                            'reply_to': user_obj.user_email,
                            'state': 'outgoing',
                            'message_id': False,
                        }

                    mail_id = mail_pool.create(cr, uid, dados)

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.lancamento'), ('res_id', '=', lancamento_obj.id)])
                    if len(attachment_ids):
                        anexos = []
                        for attachment_id in attachment_ids:
                            anexos.append((4, attachment_id))
                        mail_pool.write(cr, uid, mail_id, {'attachment_ids': anexos})

                    mail_pool.process_email_queue(cr, uid, [mail_id])

        return {'value': {}, 'warning': {'title': u'Confirmação', 'message': u'Envio agendado!'}}


    def gerar_boleto_anexo(self, cr, uid, ids, context={}):
        for id in ids:
            self.gerar_boleto(cr, uid, id, context=context)

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            lancamento_id = ids[0]

        if not lancamento_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'finan', 'finan_nota_wizard')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'finan.nota',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'finan.lancamento', 'active_ids': [lancamento_id]},
        }

        return retorno

    def concilia_lancamento(self, cr, uid, ids, conciliado, data):
        if conciliado and data:
            return {'value': {'data': data}}
        else:
            return {'value': {'data': None}}

    def onchange_banco_data(self, cr, uid, ids, tipo, res_partner_bank_id, data, data_quitacao=None, res_partner_bank_creditar_id=None):
        saldo_banco = self._soma_saldo(cr, uid, ids, 'saldo_banco', None, {'res_partner_bank_id': res_partner_bank_id, 'data': data})
        saldo_banco_creditar = self._soma_saldo(cr, uid, ids, 'saldo_banco', None, {'res_partner_bank_creditar_id': res_partner_bank_creditar_id, 'data': data})

        if not isinstance(saldo_banco, (int, float)):
            saldo_banco = 0

        if not isinstance(saldo_banco_creditar, (int, float)):
            saldo_banco_creditar = 0

        if (not data_quitacao) or tipo in ('T', 'E', 'S'):
            data_quitacao = data

        if tipo in ('T', 'E', 'S'):
            data_documento = data

            return {
                'value': {
                    'saldo_banco': saldo_banco,
                    'saldo_banco_creditar': saldo_banco_creditar,
                    'data_quitacao': data_quitacao,
                    'data_documento': data,
                }
            }

        return {
            'value': {
                'saldo_banco': saldo_banco,
                'saldo_banco_creditar': saldo_banco_creditar,
                'data_quitacao': data_quitacao
            }
        }

    def _ajusta_situacao_juros(self, cr, uid, ids=[], context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        carteira_pool = self.pool.get('finan.carteira')

        if not ids:
            ids = lancamento_pool.search(cr, 1, [('situacao', 'in', ['Vencido', 'A vencer', 'Vence hoje'])])

        #print(ids)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for id in ids:
            #cr.execute(SQL_AJUSTA_QUITACAO.replace('%d', str(id)))

            campos = lancamento_pool.read(cr, 1, [id], ['tipo', 'situacao', 'conciliado', 'data_baixa', 'data_quitacao', 'data_vencimento', 'carteira_id', 'valor_documento', 'valor_saldo', 'valor'])

            if len(campos) == 0:
                continue

            campos = campos[0]

            # campos = [{'situacao': u'Vencido', 'tipo': u'R', 'data_vencimento': '2012-04-15', 'data_quitacao': False, 'valor_documento': 234.96, 'carteira_id': (2, u'BRADESCO-COBRANCA - 0343/0146441 - 01- PATRIMONIAL SEGURAN\xc7A LTDA - CHAPECO - 09'), 'conciliado': False, 'valor_saldo': 234.96, 'id': 1514666, 'data_baixa': False}]

            situacao = campos['situacao']
            tipo = campos['tipo']
            data_vencimento = campos['data_vencimento']
            data_quitacao = campos['data_quitacao']
            data_baixa = campos['data_baixa']
            carteira_id = campos['carteira_id']
            conciliado = campos['conciliado']
            valor_documento = campos['valor_documento']
            valor_saldo = campos['valor_saldo']
            valor = campos['valor']

            nova_situacao = situacao

            mantem_vence_hoje = (hoje().weekday == 0) and (parse_datetime(data_vencimento).date().weekday >= 5)

            if tipo in ['T', 'LP', 'LR'] and conciliado:
                nova_situacao = u'Conciliado'
            elif tipo in ['P', 'R'] and data_baixa:
                if valor:
                    nova_situacao = u'Baixado parcial'
                else:
                    nova_situacao = u'Baixado'
            elif tipo in ['P', 'R', 'PP', 'PR', 'E', 'S'] and (not valor_saldo):#data_quitacao:
                nova_situacao = u'Quitado'
            elif tipo in ['P', 'R'] and not data_vencimento:
                nova_situacao = u'Sem vencimento'
            elif tipo in ['P', 'R'] and (data_vencimento == str(hoje()) or mantem_vence_hoje):
                nova_situacao = u'Vence hoje'
            elif tipo in ['P', 'R'] and data_vencimento < str(hoje()):
                nova_situacao = u'Vencido'
            elif tipo in ['P', 'R'] and data_vencimento > str(hoje()):
                nova_situacao = u'A vencer'
            else:
                nova_situacao = u'Nao identificado'

            sql = u"""
            update finan_lancamento set situacao = '{nova_situacao}'
            """.format(nova_situacao=nova_situacao)

            if carteira_id and tipo == 'R':
                if nova_situacao == u'Baixado':
                    sql += """
                        , valor_juros_previsto = 0, valor_multa_prevista = 0, valor_previsto = 0, valor_saldo = 0
                    """

                elif nova_situacao == u'Baixado parcial':
                    sql += """
                        , valor_juros_previsto = 0, valor_multa_prevista = 0, valor_previsto = 0, valor_saldo = 0
                    """

                elif nova_situacao in [u'Quitado', u'Conciliado']:
                    sql += """
                        , valor_juros_previsto = 0, valor_multa_prevista = 0, valor_previsto = 0
                    """

                elif nova_situacao == u'Vencido' and valor_saldo > 0:
                    carteira_id = carteira_id[0]
                    campos = carteira_pool.read(cr, 1, [carteira_id], ['porcentagem_juros', 'porcentagem_multa'])
                    valor_previsto = valor_saldo

                    if len(campos):
                        campos = campos[0]
                        porcentagem_juros = campos['porcentagem_juros']
                        porcentagem_multa = campos['porcentagem_multa']
                        dias_atraso = hoje() - parse_datetime(data_vencimento).date()
                        dias_atraso = dias_atraso.days

                        if porcentagem_juros:
                            valor_juros = D(valor_saldo or 0)
                            valor_juros *= D(porcentagem_juros or 0) / D('100.00')
                            valor_juros = valor_juros.quantize(D('0.01'))
                            valor_juros *= dias_atraso
                            valor_juros = valor_juros.quantize(D('0.01'))
                            valor_previsto += valor_juros

                            sql += """
                                , valor_juros_previsto = {valor_juros}
                            """.format(valor_juros=valor_juros)

                        if porcentagem_multa:
                            valor_multa = D(valor_documento or 0)
                            valor_multa *= D(porcentagem_multa or 0) / D('100.00')
                            valor_multa = valor_multa.quantize(D('0.01'))
                            valor_previsto += valor_multa

                            sql += """
                                , valor_multa_prevista = {valor_multa}
                            """.format(valor_multa=valor_multa)

                        sql += """
                            , valor_previsto = {valor_previsto}
                        """.format(valor_previsto=valor_previsto)

            sql += """
                where id = {id};
            """.format(id=id)
            if situacao != nova_situacao or 'valor_juros_previsto' in sql:
                #print(sql)
                cr.execute(sql)

    def acao_demorada_ajusta_situacao_juros(self, cr, uid, ids=[], context={}):
        lancamento_pool = self.pool.get('finan.lancamento')

        if not ids:
            ids = lancamento_pool.search(cr, 1, [('situacao', 'in', ['Vencido', 'Vence hoje'])])
            lancamento_pool._ajusta_situacao_juros(cr, uid, ids, context=context)

            ids = lancamento_pool.search(cr, 1, [('situacao', '=', 'A vencer'), ('data_vencimento', '<=', str(hoje()))])
            lancamento_pool._ajusta_situacao_juros(cr, uid, ids, context=context)

    def solicita_alteracao_vencimento(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        lancamento_obj = lancamento_pool.browse(cr, uid, ids[0])

        altera_pool = self.pool.get('finan.altera.vencimento')

        dados = {
            'lancamento_id': lancamento_obj.id,
            'data_vencimento_anterior': lancamento_obj.data_vencimento,
        }

        altera_id = altera_pool.create(cr, uid, dados)

        res = {
            'type': 'ir.actions.act_window',
            'name': u'Alteração de vencimento',
            'res_model': 'finan.altera.vencimento',
            'res_id': altera_id,
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            #'context': {'lancamento_id': lancamento_obj.id},
        }

        return res


finan_lancamento()


class finan_lancamento_rateio(orm.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.lancamento.rateio'

    def _calcula_valores(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for rateio_obj in self.browse(cr, uid, ids):
            res[rateio_obj.id] = D(0)

            if nome_campo == 'valor_documento':
                base = D(rateio_obj.lancamento_id.valor_documento or 0)
            else:
                base = D(rateio_obj.lancamento_id.valor or 0)

            porcentagem = D(rateio_obj.porcentagem or 0)
            valor = base * porcentagem / D(100)
            valor = valor.quantize(D('0.01'))

            res[rateio_obj.id] = valor

        return res

    _columns = {
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento', ondelete='cascade', select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', ondelete='restrict', select=True),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', domain=[('tipo', '=', 'C')], ondelete='restrict', select=True),
        'company_id': fields.many2one('res.company', u'Empresa/Unidade de negócio', ondelete='restrict', select=True),
        'porcentagem': CampoPorcentagem(u'Porcentagem'),
        'valor_documento': fields.function(_calcula_valores, type='float', string=u'Valor parcial do documento', store=True),
        'valor': fields.function(_calcula_valores, type='float', string=u'Valor parcial', store=True),
        #'valor_documento': CampoDinheiro(u'Valor parcial do documento'),
        #'valor': CampoDinheiro(u'Valor parcial'),

        'hr_contract_id': fields.integer(u'Contrato do RH'),
        'hr_department_id': fields.integer(u'Departamento do RH'),
        'project_id': fields.integer(u'Projeto'),
        'veiculo_id': fields.integer(u'Veículo'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.lancamento.rateio', context=c),
    }

    #_sql_constraints = [
        #('rateio_centrocusto_unique', 'unique(lancamento_id, centrocusto_id, company_id, conta_id)',
            #u'Não é permitido repetir um mesmo rateio!'),
    #]

    def onchange_porcentagem(self, cr, uid, ids, porcentagem, valor_documento, valor):
        valores = {}
        retorno = {'value': valores}
        porcentagem = porcentagem or 100
        valor_documento = valor_documento or 0
        valor = valor or 0

        valores['valor_documento'] = valor_documento * (porcentagem / 100.00)
        valores['valor'] = valor * (porcentagem / 100.00)

        return retorno


finan_lancamento_rateio()


class finan_pagamento_resumo(osv.Model):
    _name = 'finan.pagamento.resumo'
    _auto = False
    _sql = SQL_VIEW_PAGAMENTO_RESUMO
    _columns = {
        'tipo': fields.char('Tipo', size="2"),
    }

finan_pagamento_resumo()
