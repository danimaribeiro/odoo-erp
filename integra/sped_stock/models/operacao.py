# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_operacao(osv.Model):
    _description = u'Operações fiscais'
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'finan_documento_id': fields.many2one('finan.documento', u'Tipo do documento'),
        'finan_conta_id': fields.many2one('finan.conta', u'Conta financeira'),
        'finan_centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio'),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'traz_custo_medio': fields.boolean(u'Traz custo médio automático?'),
        'local_custo_ids': fields.one2many('sped.operacao.local.custo', 'operacao_id', u'Locais de origem para o custo médio'),

        #'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito'),
        #'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança'),
    }

    _defaults = {
        'traz_custo_medio': False,
    }



sped_operacao()


class sped_operacaoitem(osv.Model):
    _description = u'Item da operação fiscal'
    _name = 'sped.operacaoitem'
    _inherit = 'sped.operacaoitem'

    _columns = {
        'stock_location_id': fields.many2one('stock.location', u'Local de origem', ondelete='restrict'),
        'stock_location_dest_id': fields.many2one('stock.location', u'Local de destino', ondelete='restrict'),
    }


sped_operacaoitem()


class sped_operacao_local_custo(osv.Model):
    _description = u'Locais para custo da operação fiscal'
    _name = 'sped.operacao.local.custo'
    _order = 'operacao_id, ordem'

    _columns = {
        'operacao_id': fields.many2one('sped.operacao', u'Operação', ondelete='cascade'),
        'ordem': fields.integer(u'Ordem de seleção', select=True),
        'stock_location_id': fields.many2one('stock.location', u'Local de origem', ondelete='restrict'),
    }


sped_operacao_local_custo()


