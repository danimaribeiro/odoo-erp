# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.data import hoje


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def write(self, cr, uid, ids, dados, context=None):
        if dados.get('state', '') in ['manual', 'done']:
            #
            # Gera os registros de caixa
            #
            for id in ids:
                self.cria_caixa(cr, uid, id)

            res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        else:
            res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        return res

    def cria_caixa(self, cr, uid, sale_order_id):
        caixa_pool = self.pool.get('caixa.caixa')
        movimento_pool = self.pool.get('caixa.movimento')
        item_pool = self.pool.get('caixa.item')
        condpag_pool = self.pool.get('caixa.condicao_pagamento')

        pedido_obj = self.browse(cr, uid, sale_order_id)

        #
        # Localiza o caixa para a empresa em questão
        #
        caixa_ids = caixa_pool.search(cr, uid, [('company_id', '=', pedido_obj.company_id.id)])

        #
        # Localiza os movimentos abertos
        #
        data = hoje()
        movimento_ids = movimento_pool.search(cr, uid, [('caixa_id', 'in', caixa_ids), ('data_abertura', '<=', str(data)), ('data_fechamento', '=', False)])

        if not movimento_ids:
            raise osv.except_osv(u'Erro!', u'Não há nenhum caixa aberto no momento!')

        movimento_id = movimento_ids[0]

        dados = {
            'movimento_id': movimento_id,
            'user_id': pedido_obj.user_id.id,
            'tipo': 'E',
            'sale_order_id': pedido_obj.id,
            'vr_devido': pedido_obj.vr_total_margem_desconto,
            'vr_saldo': pedido_obj.vr_total_margem_desconto,
            'partner_id': pedido_obj.partner_id.id,
        }

        item_id = item_pool.create(cr, uid, dados)

        if pedido_obj.payment_term:
            dados = {
                'item_id': item_id,
                'payment_term_id': pedido_obj.payment_term.id,
            }
            condpag_pool.create(cr, uid, dados)

        self.log(cr, uid, pedido_obj.id, u'Enviado ao caixa para pagamento')


sale_order()
