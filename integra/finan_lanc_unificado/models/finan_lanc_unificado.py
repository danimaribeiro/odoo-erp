# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes


NATUREZA = (
    ('R', 'Receber'),
    ('P', 'Pagar'),
)

TIPO = (
    ('U', u'Unificado'),
    ('R', u'Renegociação de contrato'),
)


class finan_lanc_unificado(osv.Model):
    _description = u'Finan Lançamento Unificado'
    _name = 'finan.lanc.unificado'

    _columns = {
        'tipo': fields.selection(TIPO, u'Tipo', select=True),
        'data': fields.date(u'Data'),
        'data_vencimento': fields.date(u'Data de vencimento'),
        'natureza': fields.selection(NATUREZA, u'Natureza'),
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', u'Parceiro', ondelete='restrict'),
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_unificados_item', 'lanc_unificado_id', 'lancamento_id', u'Lançamento unificado itens'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', select=True, ondelete='restrict'),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict'),
        'uni_lanc_id': fields.many2one('finan.lancamento', u'Lançamento Unificado', select=True, ondelete='restrict'),
        'parcelamento_id': fields.many2one('finan.contrato', string=u'Parcelamento', ondelete='restrict'),

        'sugestao_bank_id': fields.many2one('res.partner.bank', string=u'Previsão de crédito na conta', ondelete='restrict'),
        'valor': fields.float(u'Valor', digits=(18, 2)),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),

        'parcelado_ids': fields.one2many('finan.lancamento', 'unificado_id', u'Lançamentos parcelados'),
        'data_inicio': fields.date(u'Data de início da cobrança'),
        'duracao': fields.integer(u'Duração em meses'),

    }

    _defaults = {
        'tipo': 'U',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'finan.lanc.unificado', context=context),
        'data':  fields.date.today,
        'data_vencimento':  fields.date.today,
    }

    def gerar_lancamento_unificado(self, cr, uid, id, context=None):
        if not id:
            return {}

        if isinstance(id, list):
            id = id[0]

        lanc_unificado_obj = self.browse(cr, uid, id)

        if lanc_unificado_obj.uni_lanc_id:
            raise osv.except_osv(u'Aviso!', u'Lançamento Unificado ja criado!')

        dados = {}
        total = 0

        for obj_lanc in lanc_unificado_obj.lancamento_ids:
            dados = {}

            if lanc_unificado_obj.tipo == 'U':
                total += obj_lanc.valor_documento or 0
            else:
                total += obj_lanc.valor_saldo or 0

            if obj_lanc.valor:
                dados = {
                    'lancamento_id': obj_lanc.id,
                    'situacao': 'Baixado parcial',
                    'data_baixa': lanc_unificado_obj.data,
                }

            else:
                dados = {
                    'lancamento_id': obj_lanc.id,
                    'situacao': 'Baixado',
                    'data_baixa': lanc_unificado_obj.data,
                }

            obj_lanc.write(dados)

        dados = {
            'data_documento': lanc_unificado_obj.data,
            'company_id': lanc_unificado_obj.company_id.id,
            'partner_id': lanc_unificado_obj.partner_id.id,
            'centrocusto_id': lanc_unificado_obj.centrocusto_id.id,
            'documento_id': lanc_unificado_obj.documento_id.id,
            'tipo': lanc_unificado_obj.natureza,
            'valor_documento': D(total),
            'conta_id': lanc_unificado_obj.conta_id.id,
            'data_vencimento': lanc_unificado_obj.data_vencimento,
        }

        if lanc_unificado_obj.tipo == 'U':
            dados['numero_documento'] = u'UNI-' + str(lanc_unificado_obj.id)
        else:
            dados['numero_documento'] = u'RENE-' + str(lanc_unificado_obj.id) + '-' + lanc_unificado_obj.contrato_id.numero

        if lanc_unificado_obj.sugestao_bank_id:
            dados['sugestao_bank_id'] = lanc_unificado_obj.sugestao_bank_id.id

        if lanc_unificado_obj.carteira_id:
            dados['carteira_id'] = lanc_unificado_obj.carteira_id.id

        uni_lanc_id = self.pool.get('finan.lancamento').create(cr, uid, dados)

        lanc_unificado_obj.write({'uni_lanc_id': str(uni_lanc_id), 'valor': total})

        return

    def gerar_parcelamento(self, cr, uid, ids, context=None):
        unificado_id = ids[0]

        unificado_obj = self.browse(cr, uid, unificado_id)

        if not unificado_obj.uni_lanc_id:
            return False

        unificado_obj.uni_lanc_id.gerar_parcelamento()

        unificado_obj = self.browse(cr, uid, unificado_id)

        parcelamento_obj = unificado_obj.uni_lanc_id.parcelamento_ids[0]

        unificado_obj.write({'parcelamento_id': parcelamento_obj.id})

        unificado_obj = self.browse(cr, uid, unificado_id)

        dados = {
            'duracao': unificado_obj.duracao,
            'data_inicio': unificado_obj.data_inicio,
            'natureza': 'RR',
        }

        parcelamento_obj.write(dados)

        parcelamento_obj.gera_provisao_wizard(context={'lancamento_id': unificado_obj.uni_lanc_id.id})

        unificado_obj = self.browse(cr, uid, unificado_id)

        for lanc_obj in unificado_obj.parcelamento_id.lancamento_ids:
            lanc_obj.write({'unificado_id': unificado_obj.id, 'contrato_id': unificado_obj.contrato_id.id})

        return {}

    def onchange_contrato_id(self, cr, uid, ids, contrato_id, context={}):
        if not contrato_id:
            return {}

        valores = {}
        res = {}
        res['value'] = valores

        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, contrato_id, context=context)

        if contrato_obj.documento_id:
            valores['documento_id'] = contrato_obj.documento_id.id
        elif getattr(contrato_obj, 'condicao_ids', False):
            valores['documento_id'] = contrato_obj.condicao_ids[0].documento_id.id

        if contrato_obj.conta_id:
            valores['conta_id'] = contrato_obj.conta_id.id
        elif getattr(contrato_obj, 'condicao_ids', False):
            valores['conta_id'] = contrato_obj.condicao_ids[0].conta_id.id

        if contrato_obj.centrocusto_id:
            valores['centrocusto_id'] = contrato_obj.centrocusto_id.id
        elif getattr(contrato_obj, 'condicao_ids', False):
            valores['centrocusto_id'] = contrato_obj.condicao_ids[0].centrocusto_id.id

        if contrato_obj.res_partner_bank_id:
            valores['sugestao_bank_id'] = contrato_obj.res_partner_bank_id.id
        elif getattr(contrato_obj, 'condicao_ids', False):
            valores['sugestao_bank_id'] = contrato_obj.condicao_ids[0].res_partner_bank_id.id

        if contrato_obj.carteira_id:
            valores['carteira_id'] = contrato_obj.carteira_id.id
        elif getattr(contrato_obj, 'condicao_ids', False):
            valores['carteira_id'] = contrato_obj.condicao_ids[0].carteira_id.id

        return res


finan_lanc_unificado()


