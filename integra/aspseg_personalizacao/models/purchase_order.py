# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class purchase_order(osv.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'


    _columns = {
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento', ondelete='restrict', select=True),
        'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal', ondelete='restrict', select=True),
    }

    def wkf_approve_order(self, cr, uid, ids, context=None):
        lancamento_pool = self.pool.get('finan.lancamento')

        res = super(purchase_order, self).wkf_approve_order(cr, uid, ids, context=context)

        for ordem_obj in self.browse(cr, uid, ids, context=context):
            amount_total = D(0)
            amount_total = D(ordem_obj.amount_total or 0 )

            if amount_total > 0 and ordem_obj.state == 'approved':

                if not ordem_obj.payment_term_id:
                    raise osv.except_osv(u'Erro!', u'Pedido sem condição de pagamento!!')

                if not ordem_obj.operacao_id:
                    raise osv.except_osv(u'Erro!', u'Pedido sem operação fiscal!!')

                payment_term_obj = self.pool.get('account.payment.term').browse(cr, uid, ordem_obj.payment_term_id.id)
                operacao_obj = ordem_obj.operacao_id

                lista_vencimentos = payment_term_obj.compute(amount_total, date_ref= ordem_obj.date_order[:10])

                if lista_vencimentos:
                    parcela = 1
                    for data, valor in lista_vencimentos:
                        dados = {}
                        dados = {
                            'company_id': ordem_obj.company_id.id,
                            'tipo': 'P',
                            'provisionado': True,
                            'conta_id': operacao_obj.finan_conta_id.id,
                            'documento_id': operacao_obj.finan_documento_id.id,
                            'partner_id': ordem_obj.partner_id.id,
                            'numero_documento': ordem_obj.name + '_' + str(parcela),
                            'data_documento': ordem_obj.date_order[:10],
                            'data_vencimento': data,
                            'valor_documento': valor
                        }
                        print(dados)
                        parcela += 1
                        lancamento_pool.create(cr, uid, dados)
                else:
                    dados = {
                            'company_id': ordem_obj.company_id.id,
                            'tipo': 'P',
                            'provisionado': True,
                            'conta_id': operacao_obj.finan_conta_id.id,
                            'documento_id': operacao_obj.finan_documento_id.id,
                            'partner_id': ordem_obj.partner_id.id,
                            'data_documento': ordem_obj.date_order[:10],
                            'valor_documento': amount_total,
                            'numero_documento': ordem_obj.name,
                        }
                    lancamento_pool.create(cr, uid, dados)

                ordem_obj.write({'state': 'done'})
            elif ordem_obj.state == 'done':
                ordem_obj.write({'state': 'approved'})

        return res

purchase_order()
