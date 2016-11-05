# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
import tools
from caixa_movimento_base import caixa_movimento_base
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia


class caixa_pagamento(orm.Model):
    _inherit = 'caixa.movimento_base'
    _name = 'caixa.pagamento'
    _description = 'Pagamento de caixa'
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

        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', select=True),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira', select=True),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária', select=True),
        'valor': fields.float(u'Valor'),
        'vencimento': fields.date(u'Vencimento', select=True),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento', select=True),

        'condicao_pagamento_id': fields.many2one('caixa.condicao_pagamento', u'Condição de pagamento', ondelete='cascade'),
    }


caixa_pagamento()


class caixa_pagamento_relatorio(orm.Model):
    _name = 'caixa.pagamento_relatorio'
    _inherit = 'caixa.pagamento'
    _auto = False

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'caixa_pagamento_relatorio')
        cr.execute("""
            create or replace view caixa_pagamento_relatorio as (
                select * from caixa_pagamento
            )
        """)


caixa_pagamento_relatorio()
