# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, valida_cnpj, valida_cpf)


NATUREZA = (
    ('R', 'Receber'),
    ('P', 'Pagar'),
)

SITUACAO_CHEQUE = (
    ('RB', 'Recebido'),
    ('DP', 'Depositado'),
    ('DF', 'Devolvido'),
    ('RP', 'Repassado'),
)


class finan_cheque(osv.Model):
    _description = u'Administração de Cheques'
    _name = 'finan.cheque'

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.company_id.partner_id.cnpj_cpf:
                res[obj.id] = obj.company_id.partner_id.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict'),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True),
        'receber_id': fields.many2one('finan.lancamento', u'Conta a receber', ondelete='restrict'),
        'bank_id': fields.many2one('res.bank', u'Banco', select=True, ondelete='restrict'),
        'agencia': fields.char(u'Agência', size=5),
        'conta_corrente': fields.char('Conta Corrente', size=14),
        'numero_cheque': fields.char(u'Número', size=10),
        'valor': fields.float('Valor'),
        'titular_cnpj_cpf': fields.char('CNPJ/CPF do titular', size=14),
        'titular_nome': fields.char('Nome do titular', size=80),
        'partner_id': fields.many2one('res.partner', u'Pagador', ondelete='restrict'),
        'data': fields.date(u'Data'),
        'data_recebimento': fields.date(u'Data de recebimento'),
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_cheques_itens', 'cheque_id', 'lancamento_id', string=u'Lançamentos', ondelete='cascade'),
        'situacao': fields.selection(SITUACAO_CHEQUE, u'Situacão'),
        'motivo_sfundo': fields.text(u'Motivo s/ Fundo?', size=80),
        'codigo_barra': fields.char(u'Código de Barras',size=80),
        'data_devolucao': fields.date(u'Data da devolução'),
        'data_pre_datado': fields.date(u'Pré-datado para'),
        'order_id': fields.many2one('sale.order', u'Orçamento', ondelete='cascade'),
        'create_uid': fields.many2one('res.users', u'Usuário'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária atual', ondelete='restrict'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'finan.cheque', context=context),
        'data_devolucao':  fields.date.today,
        'data':  fields.date.today,
        'data_recebimento':  fields.date.today,
        'situacao': 'RB',
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        if not partner_id:
            return {}

        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

        return {'value': {'titular_cnpj_cpf': partner_obj.cnpj_cpf, 'titular_nome': partner_obj.razao_social or partner_obj.name}}

    def onchange_cnpj_cpf(self, cr, uid, ids, cnpj_cpf, context={}):
        if not cnpj_cpf:
            return {}

        if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
            raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

        cnpj_cpf = limpa_formatacao(cnpj_cpf)

        if len(cnpj_cpf) == 14:
            cnpj_cpf = formata_cnpj(cnpj_cpf)
        else:
            cnpj_cpf = formata_cpf(cnpj_cpf)

        return {'value': {'titular_cnpj_cpf': cnpj_cpf}}

    def onchange_codigo_barra(self, cr, uid, ids, codigo_barra, context={}):
        valores = {}
        retorno = {'value': valores}

        bank_pool = self.pool.get('res.bank')

        if not codigo_barra:
            return {}

        if len(codigo_barra) < 34:
            return retorno
        else:
            banco = codigo_barra[1:4]
            cooperativa = codigo_barra[4:8]
            comp = codigo_barra[10:13]
            numero_chq = codigo_barra[13:19]
            conta = codigo_barra[26:32]

            banco_ids = bank_pool.search(cr, uid, [('bic', '=', banco)])

            for banco_id in banco_ids:
                valores['bank_id'] = banco_id

            valores['agencia'] = cooperativa
            valores['numero_cheque'] = numero_chq
            valores['conta_corrente'] = conta

        return retorno


finan_cheque()



