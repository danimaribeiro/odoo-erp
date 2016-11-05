# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_operacao(osv.Model):
    _description = u'Operações fiscais'
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'finan_documento_id': fields.many2one('finan.documento', u'Tipo do documento', ondelete='restrict', select=True),
        'finan_conta_id': fields.many2one('finan.conta', u'Conta financeira', ondelete='restrict', select=True),
        'finan_centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio', ondelete='restrict', select=True),
        'finan_carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict', select=True),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento', ondelete='restrict', select=True),

        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        #'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
    }



sped_operacao()
