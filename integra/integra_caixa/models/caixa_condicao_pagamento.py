# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from caixa_movimento_base import caixa_movimento_base
from pybrasil.data import parse_datetime, formata_data


class caixa_condicao_pagamento(orm.Model):
    _inherit = 'caixa.movimento_base'
    _name = 'caixa.condicao_pagamento'
    _description = u'Condição de Pagamento de caixa'
    #_rec_name = 'nome'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            mov_obj = self.browse(cr, 1, id)
            texto = mov_obj.caixa_id.nome
            data = parse_datetime(mov_obj.data)
            texto += ' - ' + formata_data(data, '%d/%m/%Y %G:%i')

            res += [(id, texto)]

        return dict(res)


    _columns = {
        #'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', store=True),
        'item_id': fields.many2one('caixa.item', u'Item', select=True, ondelete='cascade'),
        'movimento_id': fields.related('item_id', 'movimento_id', type='many2one', relation='caixa.movimento', string=u'Movimento', select=True, store=True),
        'caixa_id': fields.related('movimento_id', 'caixa_id', type='many2one', relation='caixa.caixa', string=u'Caixa', store=True, select=True),
        'company_id': fields.related('caixa_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True),

        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', select=True),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira', select=True),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária', select=True),
        'valor': fields.float(u'Valor'),

        'pagamento_ids': fields.one2many('caixa.pagamento', 'condicao_pagamento_id', u'Pagamentos'),
    }

    def gera_pagamentos(self, cr, uid, ids, context={}):
        for cp_obj in self.browse(cr, uid, ids):
            for p_obj in cp_obj.pagamento_ids:
                p_obj.unlink()

            lista_vencimentos = cp_obj.payment_term_id.compute(cp_obj.valor, cp_obj.item_id.data_abertura)

            if lista_vencimentos:
                for data, valor in lista_vencimentos:
                    dados = {
                        'item_id': cp_obj.item_id.id,
                        'condicao_pagamento_id': cp_obj.id,
                        'data_hora_abertura': cp_obj.data_hora_abertura,
                        'data_hora_fechamento': cp_obj.data_hora_fechamento,
                        'formapagamento_id': cp_obj.formapagamento_id.id,
                        'conta_id': cp_obj.conta_id.id,
                        'carteira_id': cp_obj.carteira_id.id if cp_obj.carteira_id else False,
                        'partner_bank_id': cp_obj.partner_bank_id.id if cp_obj.partner_bank_id else False,
                        'vencimento': data,
                        'valor': valor,
                    }
                    self.pool.get('caixa.pagamento').create(cr, uid, dados)

            return


caixa_condicao_pagamento()