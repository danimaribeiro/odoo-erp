# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from caixa_movimento_base import caixa_movimento_base
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia
import tools


class caixa_movimento(orm.Model):
    _inherit = 'caixa.movimento_base'
    _name = 'caixa.movimento'
    _description = 'Movimento de caixa'
    _rec_name = 'nome'
    _order = 'nome_caixa, data_hora_fechamento desc, data_hora_abertura desc'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            mov_obj = self.browse(cr, 1, id)
            texto = mov_obj.caixa_id.nome
            data = parse_datetime(mov_obj.data_hora_abertura)
            data = data_hora_horario_brasilia(data)
            texto += ' - ' + formata_data(data, '%d/%m/%Y %R')

            res += [(id, texto)]

        return dict(res)

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for mov_obj in self.browse(cr, uid, ids):
            res[mov_obj.id] = 0

            devido = 0
            recebido = 0
            troco = 0
            fechamento = 0
            dif = 0
            abertura = mov_obj.vr_abertura or 0
            liquido = abertura

            for item_obj in mov_obj.item_ids:
                if item_obj.tipo == 'E':
                    devido += item_obj.vr_devido or 0
                    recebido += item_obj.vr_recebido or 0
                    troco += item_obj.vr_troco or 0

                    for pag_obj in item_obj.pagamento_ids:
                        if pag_obj.formapagamento_id.conciliado:
                            liquido += pag_obj.valor or 0

                    #
                    # Troco é sempre em dinheiro, líquido
                    #
                    liquido -= item_obj.vr_troco or 0

                else:
                    devido -= item_obj.vr_devido or 0
                    recebido -= item_obj.vr_recebido or 0
                    troco -= item_obj.vr_troco or 0

                    for pag_obj in item_obj.pagamento_ids:
                        if pag_obj.formapagamento_id.conciliado:
                            liquido -= pag_obj.valor or 0

                    #
                    # Troco é sempre em dinheiro, líquido
                    #
                    liquido += item_obj.vr_troco or 0


            fechamento = abertura + recebido - troco
            dif = fechamento - abertura

            if nome_campo == 'vr_devido':
                res[mov_obj.id] = devido
            elif nome_campo == 'vr_recebido':
                res[mov_obj.id] = recebido
            elif nome_campo == 'vr_troco':
                res[mov_obj.id] = troco
            elif nome_campo == 'vr_fechamento':
                res[mov_obj.id] = fechamento
            elif nome_campo == 'vr_diferenca':
                res[mov_obj.id] = dif
            elif nome_campo == 'vr_liquido':
                res[mov_obj.id] = liquido

        return res

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', store=True),
        'caixa_id': fields.many2one('caixa.caixa', u'Caixa', select=True),
        'nome_caixa': fields.related('caixa_id', 'nome', type='char', string=u'Caixa', store=True, select=True),
        'company_id': fields.related('caixa_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True),
        'partner_bank_id': fields.related('caixa_id', 'partner_bank_id', type='many2one', relation='res.partner.bank', string=u'Conta bancária', store=True, select=True),
        'user_id': fields.many2one('res.users', u'Responsável', select=True),
        'vr_abertura': fields.float(u'Abertura'),
        #'vr_saldo': fields.float(u'Saldo'),

        'vr_devido': fields.function(_get_soma_funcao, type='float', string=u'Devido', store=True),
        'vr_recebido': fields.function(_get_soma_funcao, type='float', string=u'Recebido', store=True),
        'vr_troco': fields.function(_get_soma_funcao, type='float', string=u'Troco', store=True),
        'vr_fechamento': fields.function(_get_soma_funcao, type='float', string=u'Fechamento', store=True),
        'vr_diferenca': fields.function(_get_soma_funcao, type='float', string=u'Diferença', store=True),
        'vr_liquido': fields.function(_get_soma_funcao, type='float', string=u'Líquido', store=True),

        'item_ids': fields.one2many('caixa.item', 'movimento_id', u'Itens'),
        'condicao_pagamento_ids': fields.one2many('caixa.condicao_pagamento', 'movimento_id', u'Condições de pagamento'),
        'pagamento_ids': fields.one2many('caixa.pagamento', 'movimento_id', u'Pagamentos'),
        'pagamento_resumo_ids': fields.one2many('caixa.movimento_pagamento', 'movimento_id', u'Pagamentos'),
    }


caixa_movimento()
