# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from caixa_movimento_base import caixa_movimento_base
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia
from sped.models import trata_nfe


SITUACAO = (
    ('aberto', u'Em aberto'),
    ('aguardando_nfe', u'Aguardando autorização da(s) NF-e(s)'),
    ('fechado', u'Fechado'),
)


class caixa_item(orm.Model):
    _inherit = 'caixa.movimento_base'
    _name = 'caixa.item'
    _description = 'Item de movimento de caixa'
    _rec_name = 'nome'
    _order = 'data_hora_fechamento desc, data_hora_abertura desc'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            item_obj = self.browse(cr, 1, id)
            texto = item_obj.movimento_id.nome
            data = parse_datetime(item_obj.data_hora_abertura)
            texto += ' - ' + formata_data(data, '%d/%m/%Y %G:%i')

            res += [(id, texto)]

        return dict(res)

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', store=True, select=True),
        'movimento_id': fields.many2one('caixa.movimento', u'Movimento', select=True),
        'caixa_id': fields.related('movimento_id', 'caixa_id', type='many2one', relation='caixa.caixa', string=u'Caixa', store=True, select=True),
        'nome_caixa': fields.related('caixa_id', 'nome', type='char', string=u'Caixa', store=True, select=True),
        'company_id': fields.related('caixa_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True),
        'partner_bank_id': fields.related('caixa_id', 'partner_bank_id', type='many2one', relation='res.partner.bank', string=u'Conta bancária', store=True, select=True),
        'user_id': fields.many2one('res.users', u'Responsável', select=True),
        'tipo': fields.selection((('E', u'Entrada'), ('S', u'Saída')), u'Tipo', select=True),
        'sale_order_id': fields.many2one('sale.order', u'Pedido', select=True),
        'sale_order_line_ids': fields.related('sale_order_id', 'order_line', type='one2many', relation='sale.order.line', string=u'Itens'),

        'sped_documento_ids': fields.related('sale_order_id', 'sped_documento_ids', type='many2many', relation='sped.documento', string=u'Notas Fiscais'),


        'partner_id': fields.many2one('res.partner', u'Cliente', select=True),
        'vr_devido': fields.float(u'Valor'),
        'vr_recebido': fields.float(u'Recebido'),
        'vr_troco': fields.float(u'Troco'),
        'vr_saldo': fields.float(u'Saldo'),

        'condicao_pagamento_ids': fields.one2many('caixa.condicao_pagamento', 'item_id', u'Condições de pagamento'),
        'pagamento_ids': fields.one2many('caixa.pagamento', 'item_id', u'Pagamentos'),

        'state': fields.selection(SITUACAO, string=u'Situação', select=True),
    }

    _defaults = {
        'state': 'aberto'
    }

    def recalcula(self, cr, uid, ids, context={}):
        for item_obj in self.browse(cr, uid, ids):
            vr_pago = 0

            for cp_obj in item_obj.condicao_pagamento_ids:
                cp_obj.gera_pagamentos()

            for p_obj in item_obj.pagamento_ids:
                vr_pago += p_obj.valor

            dados = {
                'vr_recebido': vr_pago,
            }

            if vr_pago > item_obj.vr_devido:
                dados['vr_troco'] = vr_pago - item_obj.vr_devido
                dados['vr_saldo'] = 0
            else:
                dados['vr_troco'] = 0
                dados['vr_saldo'] = item_obj.vr_devido - vr_pago

            item_obj.write(dados)

    def gera_notas(self, cr, uid, ids, context={}):
        for item_obj in self.browse(cr, uid, ids):
            pedido_obj = item_obj.sale_order_id
            pedido_obj.gera_notas()

            for nota_obj in pedido_obj.sped_documento_ids:
                if nota_obj.modelo == '55':
                    nfe = trata_nfe.monta_nfe(self, cr, uid, nota_obj)
                    pdf = trata_nfe.processador.danfe.conteudo_pdf

                    trata_nfe.grava_nfe(self, cr, uid, item_obj, nfe, tabela='caixa.item')
                    trata_nfe.grava_danfe(self, cr, uid, item_obj, nfe, pdf, tabela='caixa.item')

            item_obj.write({'state': 'aguardando_nfe'})

            #
            # Por agora, que não tem a aprovação da NF-e
            #
            self.gera_financeiro(cr, uid, [item_obj.id], context=context)
            item_obj.write({'state': 'fechado', 'data_hora_fechamento': fields.datetime.now()})

    def gera_financeiro(self, cr, uid, ids, context={}):
        lanc_pool = self.pool.get('finan.lancamento')

        for item_obj in self.browse(cr, uid, ids):
            i = 0
            for pag_obj in item_obj.pagamento_ids:
                i += 1
                dados = {
                    'company_id': item_obj.company_id.id,
                    'tipo': 'E',  # Padrão é transação de entrada (rec. em dinheiro)
                    'data': pag_obj.vencimento,
                    'valor': pag_obj.valor,
                    'documento_id': 1,
                    'numero_documento': item_obj.sale_order_id.name + '.' + str(i).zfill(2) + '/' + str(len(item_obj.pagamento_ids)).zfill(2) ,
                    'data_documento': pag_obj.data_abertura,
                    'valor_documento': pag_obj.valor,
                    'partner_id': item_obj.partner_id.id,
                    'data_vencimento': pag_obj.vencimento,
                    'conta_id': 12,
                    'res_partner_bank_id': item_obj.partner_bank_id.id,
                    'carteira_id': False,
                    'data_quitacao': pag_obj.vencimento,
                }

                lanc_id = lanc_pool.create(cr, uid, dados)
                pag_obj.write({'lancamento_id': lanc_id})


caixa_item()
