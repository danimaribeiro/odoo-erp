# -*- encoding: utf-8 -*-


from datetime import datetime
from decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    def _valor_comissao(self, cr, uid, ids, nome_campo, arg=None, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            vr_comissao = 0.00
            if item_obj.comissao:
                vr_comissao = item_obj.vr_total_margem_desconto * item_obj.comissao / 100.00

            res[item_obj.id] = vr_comissao

        return res

    _columns = {
        'date_order': fields.related('order_id', 'date_order', type='date', string=u'Data'),
        'peso_liquido': fields.related('product_id', 'weight_net', type='float', string=u'Peso'),
        'aprovado': fields.boolean(u'Aprovado'),
        'comissao': fields.float(u'% comissão'),
        'vr_comissao': fields.function(_valor_comissao, string=u'Valor comissão', method=True, type='float', store=True),
    }

    _defaults = {
        'aprovado': True,
    }

    def on_change_quantidade_margem_desconto(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=0, vr_unitario_minimo=0, vr_unitario_venda=0, margem=0, desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context=None, desconto_direto=True, margem_direta=True, comissao=0):
        res = super(sale_order_line, self).on_change_quantidade_margem_desconto(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, desconto, autoinsert, mudou_quantidade, usa_unitario_minimo, context, desconto_direto=True, margem_direta=True)

        if comissao and qty and vr_unitario_venda:
            valores = res['value']
            bc_comissao = valores['vr_total_margem_desconto']
            valores['vr_comissao'] = bc_comissao * comissao / 100.00

        return res

    def calcula_total_orcamento(self, cr, uid, sale_order_id):
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        #self.pool.get('sale.order').cria_resumo_locacao(cr, uid, sale_order_id)
        #
        # Reunimos os totais de todas as categorias
        #
        cr.execute('''
             select
              sum(coalesce(ol.vr_total_custo, 0)) as vr_total_custo,
              sum(coalesce(ol.vr_total, 0)) as vr_total,
              sum(coalesce(ol.vr_total_margem_desconto, 0)) as vr_total_margem_desconto,
              0 as vr_mensal,
              sum(coalesce(ol.vr_comissao, 0)) as vr_comissao,
              sum(coalesce(ol.vr_comissao_locacao, 0)) as vr_comissao_locacao,
              0 as meses_retorno_investimento,
              coalesce(max(coalesce(prod.parcelas,0)), 0) as max_parcelas

            from
              sale_order_line ol
              join product_product as prod on prod.id = ol.product_id

            where
              ol.aprovado = true and
              ol.order_id = %d;''' % sale_order_id)

        totais = cr.fetchall()[0]

        #
        # Atualizamos o registro mestre, para termos o valor mensal final
        #

        totais = list(totais)
        for i in range(len(totais)):
            if totais[i] is None:
                totais[i] = D(0)
            else:
                totais[i] = D(str(totais[i]))

        vr_total_custo = totais[0]
        vr_total_margem_desconto = totais[2]
        vr_total = vr_total_margem_desconto
        totais[1] = vr_total
        vr_mensal = totais[3]
        vr_comissao = totais[4]
        vr_comissao_locacao = totais[5]
        meses_retorno_investimento = totais[6]
        if totais[7] > 0:
            max_parcelas = totais[7]
        else:
            max_parcelas = D(10)

        valor_parcela = D(0)
        valor_parcela_primeira = D(0)
        if max_parcelas > 0:
            print(totais)
            valor_parcela = (vr_total_margem_desconto + vr_comissao) / max_parcelas
            valor_parcela_primeira = valor_parcela
            if sale_order_obj.valor_frete:
                if sale_order_obj.frete_primeira:
                    valor_parcela_primeira = valor_parcela + D(str(sale_order_obj.valor_frete))
                else:
                    valor_parcela_primeira = valor_parcela + (D(str(sale_order_obj.valor_frete)) / max_parcelas)
                    valor_parcela = valor_parcela_primeira
                totais[1] += D(str(sale_order_obj.valor_frete))
                #totais[2] += D(str(sale_order_obj.valor_frete))

            #
            # totais[1] == vr_total
            # totais[2] == vr_total_margem_desconto
            #
            totais[1] += vr_comissao
            #totais[2] += vr_comissao

        totais.append(valor_parcela)
        totais.append(valor_parcela_primeira)

        totais = tuple(totais)
        totais += (sale_order_id,)

        cr.execute('''
            begin;
            update sale_order set
              vr_total_custo = %.2f,
              vr_total = %.2f,
              vr_total_margem_desconto = %.2f,
              vr_mensal = %.2f,
              vr_comissao = %.2f,
              vr_comissao_locacao = %.2f,
              meses_retorno_investimento = %.2f,
              parcelas = %.2f,
              vr_parcelas = %.2f,
              vr_primeira_parcela = %2f
            where
              id = %d;
            commit work;''' % totais)

        return totais

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        resposta = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context)

        if not product_id:
            return resposta

        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)

        resposta['value'].update(
            {
                'name': product_obj.nome_apresentacao,
            }
        )
        return resposta

    def calcula_comissao_itens(self, cr, uid, sale_order_id):
        #
        # Primeiro, recalculamos os itens e as comissões
        #
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        for item_obj in sale_order_obj.order_line:
            bc_comissao = item_obj.vr_total_margem_desconto

            if item_obj.orcamento_categoria_id.abate_impostos_comissao:
                bc_comissao -= item_obj.vr_total_margem_desconto * (item_obj.orcamento_categoria_id.abate_impostos_comissao / 100.00)

            if item_obj.orcamento_categoria_id.abate_custo_comissao:
                bc_comissao -= item_obj.vr_total_custo

            if item_obj.vr_total_custo:
                margem_real = item_obj.vr_total_margem_desconto / item_obj.vr_total_custo
            else:
                margem_real = 0
            #if item_obj.desconto:
            #    margem_real = item_obj.margem * (1 - (item_obj.desconto / 100))
            #elif item_obj.margem:
            #    margem_real = item_obj.margem

            vr_comissao = 0
            comissao = item_obj.comissao or 0

            if item_obj.orcamento_categoria_id.considera_venda and sale_order_obj.orcamento_aprovado == 'venda':
                if item_obj.comissao_venda_id:
                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.comissao_venda_id.id), ('margem', '>=', margem_real)], order='margem')

                    if item_comissao_ids:
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])

                        if item_obj.usa_unitario_minimo:
                            comissao = item_comissao_obj.comissao_preco_minimo
                        else:
                            comissao = item_comissao_obj.comissao

            else:
                if item_obj.orcamento_categoria_id.considera_venda:
                    pass
                    #item_obj.write({'vr_comissao': 0}, context={'calculo_resumo': True})

                elif item_obj.comissao_locacao_id:
                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.comissao_locacao_id.id), ('meses_retorno_investimento', '>=', 1)], order='meses_retorno_investimento')

                    if item_comissao_ids:
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])
                        comissao = item_comissao_obj.comissao

            vr_comissao = bc_comissao * (comissao / 100.00)
            item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

    #def onchange_comissao(self, cr, uid, comissao, quantidade, )

sale_order_line()
