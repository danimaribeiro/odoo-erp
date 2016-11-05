# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'

    def realiza_rateio(self, cr, uid, ids, padrao={}, rateio={}, context={}):
        if not ids:
            return D(0)

        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        total = D(0)
        for item_obj in self.browse(cr, uid, ids):
            p = copy(padrao)
            p['company_id'] = item_obj.order_id.company_id.id
            produto_obj = item_obj.product_id

            if getattr(produto_obj, 'conta_despesa_id', False):
                conta_entrada_obj = produto_obj.conta_despesa_id
            elif getattr(produto_obj, 'account_despesa_id', False):
                conta_entrada_obj = produto_obj.account_despesa_id.finan_conta_id
            else:
                conta_entrada_obj = item_obj.order_id.operacao_id.finan_conta_id

            if getattr(produto_obj, 'conta_receita_id', False):
                conta_saida_obj = produto_obj.conta_receita_id
            elif getattr(produto_obj, 'account_receita_id', False):
                conta_saida_obj = produto_obj.account_receita_id.finan_conta_id
            else:
                conta_saida_obj = item_obj.order_id.operacao_id.finan_conta_id

            #
            # Estrutura para determinar qual conta usar quando
            # despesa, custo ou receita no rateio
            #
            conta_id = [
                'tipo_conta',
                {
                    'D': conta_entrada_obj.id,
                    'C': conta_entrada_obj.id,
                    False: conta_entrada_obj.id,
                }
            ]

            p['conta_id'] = conta_id
            valor = D(item_obj.price_subtotal)

            #
            # Tratamos o rateio do projeto e do item do projeto, quando houver
            #
            if 'project_id' in campos and getattr(item_obj, 'project_id', False):
                p['project_id'] = item_obj.project_id.id
                #
                # Quando houver projeto, a empresa tem que ser a empresa do projeto
                #
                p['company_id'] = item_obj.project_id.company_id.id

            if 'project_orcamento_item_id' in campos and getattr(item_obj, 'orcamento_item_id', False):
                p['project_orcamento_item_id'] = item_obj.orcamento_item_id.id

            if 'project_orcamento_item_planejamento_id' in campos and getattr(item_obj, 'orcamento_planejamento_id', False):
                p['project_orcamento_item_planejamento_id'] = item_obj.orcamento_planejamento_id.id

            if valor <= 0:
                continue

            total += valor

            if getattr(item_obj, 'centrocusto_id', False):
                cc_pool.realiza_rateio(cr, uid, [item_obj.centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)

            elif item_obj.order_id.centrocusto_id:
                cc_pool.realiza_rateio(cr, uid, [item_obj.order_id.centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)

            elif item_obj.order_id.rateio_ids:
                cc_pool.realiza_rateio(cr, uid, [item_obj.order_id.id], valor=valor, padrao=p, rateio=rateio, context=context, tabela_pool=self.pool.get('purchase.order'))

            else:
                cc_pool._realiza_rateio(valor, 100, campos, p, rateio)

        return total


purchase_order_line()
