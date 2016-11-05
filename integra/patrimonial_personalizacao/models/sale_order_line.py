# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID
from copy import copy
from pybrasil.base import DicionarioBrasil
from sped.models.fields import *

#
# Tratamento dos itens com comissão específica na Patrimonial
#
RONDA_ID = 3195
ANIMAL_ADESTRADO_ID = 3187
POSTO_MOVEL_ID = 3196
PATRIMONIAL_IDS = [RONDA_ID, ANIMAL_ADESTRADO_ID, POSTO_MOVEL_ID]


STORE_DESCRICAO = {
    'sale.order.line': (
        lambda item_pool, cr, uid, ids, context={}: ids,
        ['product_id'],
        20  #  Prioridade
    )
}


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    def _descricao(self, cr, uid, ids, nome_campo, arg, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids, context=context):
            descricao = ''

            if item_obj.product_id:
                descricao = getattr(item_obj.product_id, 'nome_generico', '')

                if not descricao:
                    descricao = item_obj.product_id.name or ''

            if item_obj.order_line_id:
                descricao += ' [ '

                if hasattr(item_obj.order_line_id.product_id, 'nome_generico') and getattr(item_obj.order_line_id.product_id, 'nome_generico', False):
                    descricao += item_obj.order_line_id.product_id.nome_generico
                else:
                    descricao += item_obj.order_line_id.product_id.name
                descricao += ' ]'

            res[item_obj.id] = descricao

        return res

    _columns = {
        'name': fields.function(_descricao, string=u'Descrição', type='char', size=256, select=True, store=STORE_DESCRICAO),
        #'name': fields.char('Description', size=256, required=True, select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_uom_qty': fields.float(u'Quantidade', digits=(18,4), required=True, readonly=False, states=False),
        'discount': fields.float(u'Desconto (%)', digits=(16, 2), readonly=False, states=False),
        'ignora_impostos': fields.boolean(u'Ignora impostos?'),
        'vr_unitario_custo': CampoDinheiro(u'Custo unitário', digits=(21, 10)),
        'vr_unitario_venda_impostos': CampoDinheiro(u'Unitário venda', digits=(18, 2)),
        'crm_meeting_id': fields.many2one('crm.meeting', u'Instalação', ondelete='restrict'),
    }

    def _comissao(self, cr, uid, ids, nome_campo, arg=None, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            if nome_campo == 'comissao':
                if item_obj.vr_total_margem_desconto:
                    res[item_obj.id] = item_obj.vr_comissao / item_obj.vr_total_margem_desconto * 100.00
                else:
                    res[item_obj.id] = 0

            elif nome_campo == 'comissao_locacao':
                if item_obj.vr_total_margem_desconto:
                    res[item_obj.id] = item_obj.vr_comissao_locacao / item_obj.vr_total_minimo * 100.00
                else:
                    res[item_obj.id] = 0

        return res

    def calcula_comissao_itens(self, cr, uid, sale_order_id):
        #
        # Primeiro, recalculamos os itens e as comissões
        #
        sale_order_obj = self.pool.get('sale.order').browse(cr, 1, sale_order_id)

        #
        # Ajustamos o usuário para ser o usuário dono do cliente
        #
        if sale_order_obj.partner_id.user_id:
            uid = sale_order_obj.partner_id.user_id.id

        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        for item_obj in sale_order_obj.order_line:
            bc_comissao = item_obj.vr_total_margem_desconto

            #if item_obj.orcamento_categoria_id.abate_impostos_comissao:
                #bc_comissao -= item_obj.vr_total_margem_desconto * (item_obj.orcamento_categoria_id.abate_impostos_comissao / 100.00)

            #if item_obj.orcamento_categoria_id.abate_custo_comissao:
                #bc_comissao -= item_obj.vr_total_custo

            #margem_real = 0
            #if item_obj.desconto:
                #margem_real = item_obj.margem * (1 - (item_obj.desconto / 100))
            #elif item_obj.margem:
            #margem_real = item_obj.margem

            vr_comissao = 0

            if item_obj.product_id.id in PATRIMONIAL_IDS:
                if item_obj.product_id.id == ANIMAL_ADESTRADO_ID:
                    vr_comissao = bc_comissao * 0.6
                elif item_obj.product_id.id == POSTO_MOVEL_ID:
                    vr_comissao = bc_comissao * 0.1
                else:
                    vr_comissao = ((bc_comissao - 150) * 0.3) + 150

                item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

                continue

            if item_obj.orcamento_categoria_id.considera_venda and sale_order_obj.orcamento_aprovado == 'venda':
                if item_obj.orcamento_categoria_id.comissao_venda_id:
                    ##
                    ## Forçando a busca pela comissão de margem 0
                    ##
                    #item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.orcamento_categoria_id.comissao_venda_id.id), ('margem', '=', 0)], order='margem')

                    if item_obj.orcamento_categoria_id.comissao_venda_id.comissao_item_ids:
                        item_comissao_obj = item_obj.orcamento_categoria_id.comissao_venda_id.comissao_item_ids[0]
                        if item_obj.usa_unitario_minimo:
                            vr_comissao = bc_comissao * (item_comissao_obj.comissao_preco_minimo / 100.00)
                        else:
                            bc_comissao = D(item_obj.vr_total_minimo)
                            vr_comissao = bc_comissao * D(item_comissao_obj.comissao) / D(100)

                            #
                            # Sobre a dif. do sugerido para o preço com margem,
                            # acrescenta 20%
                            #
                            bc_comissao = D(item_obj.vr_total_margem_desconto)
                            bc_comissao -= D(item_obj.vr_unitario_venda) * D(item_obj.product_uom_qty)
                            vr_comissao_adicional = bc_comissao * D('0.2')
                            vr_comissao += vr_comissao_adicional

                        item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

            else:
                if item_obj.orcamento_categoria_id.considera_venda:
                    item_obj.write({'vr_comissao': 0}, context={'calculo_resumo': True})

                elif item_obj.orcamento_categoria_id.comissao_locacao_id:
                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.orcamento_categoria_id.comissao_locacao_id.id), ('meses_retorno_investimento', '>=', 1)], order='meses_retorno_investimento')

                    if item_comissao_ids:
                        bc_comissao = item_obj.vr_total_minimo
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])
                        vr_comissao = bc_comissao * (item_comissao_obj.comissao / 100.00)
                        item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

    def calcula_resumo_locacao(self, cr, uid, sale_order_id):
        sale_order_obj = self.pool.get('sale.order').browse(cr, 1, sale_order_id)
        #
        # Ajustamos o usuário para ser o usuário dono do cliente
        #
        if sale_order_obj.partner_id.user_id:
            uid = sale_order_obj.partner_id.user_id.id

        self.calcula_comissao_itens(cr, uid, sale_order_id)
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        #
        # Agora, faz o resumo por categoria para a locação
        #
        #sale_order_obj.cria_resumo_locacao(cr, uid, sale_order_id)
        resumo = self.calcula_resumo_categoria_com_autocalc(cr, uid, sale_order_id)

        #
        # Primeiro, atualizamos os totais de cada categoria de orçamento na tabela de
        # locação/resumo
        #
        for categoria_id in resumo:
            total = resumo[categoria_id]
            vr_total_custo = total['vr_total_custo']
            if vr_total_custo is None:
                vr_total_custo = 0
            vr_total_minimo = total['vr_total_minimo']
            if vr_total_minimo is None:
                vr_total_minimo = 0
            vr_total = total['vr_total']
            if vr_total is None:
                vr_total = 0
            vr_total_margem_desconto = total['vr_total_margem_desconto']
            if vr_total_margem_desconto is None:
                vr_total_margem_desconto = 0
            vr_comissao = total['vr_comissao']
            if vr_comissao is None:
                vr_comissao = 0

            resumo_id = self.pool.get('orcamento.orcamento_locacao').search(cr, uid, [('sale_order_id', '=', sale_order_id), ('orcamento_categoria_id', '=', categoria_id)])

            if resumo_id:
                resumo_obj = self.pool.get('orcamento.orcamento_locacao').browse(cr, uid, resumo_id[0])

                comissao_locacao_obj = False
                if sale_order_obj.partner_id.comissao_locacao_id:
                    comissao_locacao_obj = sale_order_obj.partner_id.comissao_locacao_id

                elif resumo_obj.orcamento_categoria_id.comissao_locacao_id:
                    comissao_locacao_obj = resumo_obj.orcamento_categoria_id.comissao_locacao_id

                #
                # No caso da Patrimonial, a comissão de locação da categoria
                # das mensalidades já foi calculada como se fosse a comissão
                # de venda
                #
                vr_comissao_locacao = 0
                if not resumo_obj.orcamento_categoria_id.considera_venda:
                    vr_comissao_locacao = vr_comissao

                elif comissao_locacao_obj:
                    bc_comissao = resumo_obj.vr_mensal
                    resumo_obj.meses_retorno_investimento = D(resumo_obj.meses_retorno_investimento)
                    resumo_obj.meses_retorno_investimento = resumo_obj.meses_retorno_investimento.quantize(D('0.01'))

                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', comissao_locacao_obj.id), ('meses_retorno_investimento', '>=', resumo_obj.meses_retorno_investimento)], order='meses_retorno_investimento')

                    #print('meses_retorno_investimento', resumo_obj.meses_retorno_investimento, item_comissao_ids)
                    if not item_comissao_ids:
                        #raise osv.except_osv(u'Inválido!', u'A regra de validação de meses para retorno do investimento para a categoria “%s” não permite essa quantidade de meses que foi informada, ou o valor informado gera um nº de parcelas superior ao nº de meses máximo!' % resumo_obj.orcamento_categoria_id.nome)
                        vr_comissao_locacao = 0
                    else:
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])
                        vr_comissao_locacao = bc_comissao * (item_comissao_obj.comissao / 100.00)

                if not resumo_obj.orcamento_categoria_id.considera_venda:
                    vr_total_custo = 0
                    vr_total = 0
                    vr_total_margem_desconto = 0
                    vr_total_minimo = 0
                    vr_comissao = 0

                resumo_obj.write({'vr_total_custo': vr_total_custo, 'vr_total': vr_total, 'vr_total_margem_desconto': vr_total_margem_desconto, 'vr_comissao': vr_comissao, 'vr_comissao_locacao': vr_comissao_locacao, 'vr_total_minimo': vr_total_minimo}, context={'calcula_resumo': True})

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        resposta = super(sale_order_line, self).product_id_change(cr, 1, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context=context)

        if not product_id:
            return resposta

        if 'price_unit' in context:
            return resposta

        #
        # Usa o admin para buscar o produto, para evitar problemas de acesso
        # no custos da matriz, para usuários que não tenham permissão de
        # acesso na matriz
        #
        product_obj = self.pool.get('product.product').browse(cr, 1, product_id, context=context)

        aprovado = context.get('orcamento_aprovado', 'venda')

        if 'price_unit' not in context:
            ###
            ### Ajustas os valores
            ###
            ##vr_unitario_custo = D(0)
            ##company_id = context.get('company_id', False)

            ###
            ### Na venda, busca o custo sempre da matriz
            ###
            ##company_pool = self.pool.get('res.company')
            ##company_obj = company_pool.browse(cr, 1, company_id)
            ##cnpj_matriz = company_obj.partner_id.cnpj_cpf[:10] + '/0001-'

            ###
            ### Busca a empresa matriz
            ###
            ##matriz_ids = company_pool.search(cr, 1 , [('matriz_id', '=', False), ('cnpj_cpf', 'like', cnpj_matriz)])
            ##matriz_id = matriz_ids[0]

            ##for custo_obj in product_obj.custo_ids:
                ##if aprovado == 'venda' and custo_obj.company_id.id == matriz_id:
                    ##if custo_obj.location_id.padrao_venda:
                        ##vr_unitario_custo = D(custo_obj.vr_unitario)
                        ##break

                ##elif aprovado != 'venda' and custo_obj.company_id.id == matriz_id:
                    ##if custo_obj.location_id.padrao_locacao:
                        ##vr_unitario_custo = D(custo_obj.vr_unitario)
                        ##break

            if aprovado == 'venda':
                vr_unitario_custo = D(product_obj.custo_ultima_compra or 0)
            else:
                vr_unitario_custo = D(product_obj.custo_ultima_compra_locacao or 0)

            #
            # Caso não haja custo de entrada de notas, usar um custo pré-cadastrado
            #
            if vr_unitario_custo == 0:
                vr_unitario_custo = D(product_obj.standard_price)
                #raise osv.except_osv(u'Problema!', u'O produto informado não possui preço de custo, impossível continuar!')

            #
            # Ajusta o preço mínimo com a taxa administrativa
            #
            vr_unitario_minimo = D(vr_unitario_custo)
            adm_pool = self.pool.get('sale.taxa_administrativa')
            adm_ids = adm_pool.search(cr, 1, [])
            for adm_obj in adm_pool.browse(cr, 1, adm_ids):
                if vr_unitario_custo <= adm_obj.valor:
                    vr_unitario_minimo *= D(1) + (D(adm_obj.taxa) / D(100))
                    break

            #
            # Ajusta o preço de venda com a comissão mínima
            #
            comissao = D(0)
            if 'comissao_venda_id' in resposta['value'] and resposta['value']['comissao_venda_id']:
                comissao_venda_obj = self.pool.get('orcamento.comissao').browse(cr, 1, resposta['value']['comissao_venda_id'])
                if comissao_venda_obj.comissao_item_ids:
                    comissao = D(comissao_venda_obj.comissao_item_ids[0].comissao)

            #
            # à taxa de comissão, somam 10% de margem de lucro
            #
            comissao += D(10)
            list_price = vr_unitario_minimo / (D(1) - (comissao / D(100)))
            vr_unitario_venda = vr_unitario_minimo / (D(1) - (comissao / D(100)))
            vr_unitario_venda_impostos = vr_unitario_minimo / (D(1) - (comissao / D(100)))

            price_unit = vr_unitario_minimo / (D(1) - (comissao / D(100)))
            if 'margem' in resposta['value'] and resposta['value']['margem']:
                price_unit = price_unit / (D(1) - (D(resposta['value']['margem']) / D(100)))

            #price_unit = price_unit.quantize(D('0.01'))

        else:
            price_unit = context.get('price_unit', 0)

        #print('contexto_novo')
        #print(context)
        contexto_novo = copy(context)
        contexto_novo['price_unit'] = price_unit

        impostos = super(sale_order_line, self).product_id_change(cr, 1, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, contexto_novo)

        if 'price_unit' not in context and 'vr_desconto' not in context:
            quantidade = D(qty or 1)
            price_subtotal = price_unit * quantidade
            #price_subtotal = price_subtotal.quantize(D('01'))

            impostos['value']['price_unit'] = price_unit
            impostos['value']['price_subtotal'] = price_subtotal
            impostos['value']['vr_unitario_venda'] = price_unit
            impostos['value']['vr_total_venda'] = price_subtotal
            impostos['value']['vr_unitario_custo'] = vr_unitario_custo
            impostos['value']['vr_total_custo'] = vr_unitario_custo * quantidade
            impostos['value']['vr_unitario_minimo'] = vr_unitario_minimo
            impostos['value']['vr_total_minimo'] = vr_unitario_minimo * quantidade
            impostos['value']['vr_unitario_margem_desconto'] = price_unit
            impostos['value']['vr_total_margem_desconto'] = price_unit * quantidade

        return impostos

    def on_change_quantidade_margem_desconto(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=0, vr_unitario_minimo=0, vr_unitario_venda=0, margem=0, desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context={}, desconto_direto=False, margem_direta=False):
        if autoinsert:
            return {}

        resposta = {'value': {}}
        valores = resposta['value']

        quantidade = D(qty or 1)
        #vr_unitario_custo = D(vr_unitario_custo or 0).quantize(D('0.01'))
        vr_total_custo = quantidade * vr_unitario_custo
        #vr_total_custo = vr_total_custo.quantize(D('0.01'))

        #vr_unitario_minimo = D(vr_unitario_minimo).quantize(D('0.01'))
        vr_total_minimo = quantidade * vr_unitario_minimo
        #vr_total_minimo = vr_total_minimo.quantize(D('0.01'))

        #vr_unitario_venda = resposta['value']['price_unit']

        #vr_unitario_venda = D(vr_unitario_venda or 0).quantize(D('0.01'))
        vr_total_venda = vr_unitario_venda * quantidade
        #vr_total_venda = vr_total_venda.quantize(D('0.01'))

        #print('vr_unitario_custo', vr_unitario_custo)

        if usa_unitario_minimo:
            vr_total = quantidade * vr_unitario_minimo
            #vr_total = vr_total.quantize(D('0.01'))
            vr_total_margem_desconto = vr_total
            margem = 0
            desconto = 0

        else:
            vr_total = quantidade * vr_unitario_venda
            #vr_total = vr_total.quantize(D('0.01'))

        margem = D(margem or 0).quantize(D('0.01'))
        desconto = D(desconto or 0).quantize(D('0.01'))

        if not (margem_direta or context.get('margem_direta', False)):
            margem = vr_total / (1- (margem / D('100.00')))
            margem -= vr_total
            #margem = margem.quantize(D('0.01'))

        vr_total_margem_desconto = vr_total + margem

        #
        # Na Patrimonial, o desconto é sempre em valor
        #
        #if not(desconto_direto or context.get('margem_direta', False)):
            #desconto = vr_total_margem_desconto * (desconto / D('100.00'))
            #desconto = desconto.quantize(D('0.01'))

        #
        # Ajusta o desconto para embutir os impostos
        #
        proporcao_impostos = 0
        if desconto:
            #if isinstance(ids, (list, tuple)):
                #item_id = ids[0]
            #else:
                #item_id = ids

            #item_obj = self.pool.get('sale.order.line').browse(cr, uid, item_id)
            #if D(item_obj.vr_total_venda_impostos or 0):
                ##proporcao_impostos = D(item_obj.vr_total_margem_desconto) / D(item_obj.vr_total_venda_impostos)
                #proporcao_impostos = D(item_obj.proporcao_imposto or 100) / D(100)

            #else:
                #proporcao_impostos = D(context.get('proporcao_imposto', 1) or 1) / D(100)

            proporcao_impostos = D(context.get('proporcao_imposto', 1) or 1) / D(100)
            print(proporcao_impostos)

            desconto = D(desconto or 0) * proporcao_impostos
            #desconto = desconto.quantize(D('0.01'))

        vr_total_margem_desconto -= desconto
        #vr_total_margem_desconto = vr_total_margem_desconto.quantize(D('0.01'))

        if product_id:
            produto_obj = self.pool.get('product.product').browse(cr, 1, product_id)
            #if vr_total_margem_desconto < vr_total_minimo:
                #raise osv.except_osv(u'Problema!', u'O produto “{produto}” não pode ser vendido por um preço menor do que o mínimo!'.format(produto=produto_obj.name_template))

        vr_unitario_margem_desconto = vr_total_margem_desconto / quantidade
        #vr_unitario_margem_desconto = vr_unitario_margem_desconto.quantize(D('0.01'))

        #print(vr_unitario_margem_desconto, 'desconto', desconto, proporcao_impostos)

        #if vr_unitario_venda:
            #nova_margem = D(vr_unitario_margem_desconto) / D(vr_unitario_venda) * 100
        #else:
            #nova_margem = D(0)

        #nova_margem = nova_margem.quantize(D('0.01'))

        contexto_novo = copy(context)
        contexto_novo['price_unit'] = vr_unitario_margem_desconto

        impostos = self.pool.get('sale.order.line').product_id_change(cr, 1, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, contexto_novo)

        valores = impostos['value']
        valores['vr_unitario_custo'] = vr_unitario_custo
        valores['vr_total_custo'] = vr_total_custo
        valores['vr_unitario_margem_desconto'] = vr_unitario_margem_desconto
        valores['vr_total_margem_desconto'] = vr_total_margem_desconto
        valores['vr_unitario_minimo'] = vr_unitario_minimo
        valores['vr_total_minimo'] = vr_total_minimo
        valores['vr_unitario_venda'] = vr_unitario_venda
        valores['vr_total_venda'] = vr_total_venda

        return impostos
        #return {}

    #def ajusta_produtos_relacionados(self, cr, uid, item_pai_obj, context={}):
        ##
        ## Buscamos os itens que serão relacionados
        ##
        #item_pool = self.pool.get('sale.order.line')
        #item_ids = item_pool.search(cr, uid, [('order_id', '=', item_pai_obj.order_id.id), ('order_line_id', '=', item_pai_obj.id)])

        ##
        ## Excluímos os antigos
        ##
        #item_pool.unlink(cr, uid, item_ids)

        ##
        ## Verificamos se o novo produto tem itens relacionados
        ##
        #if len(item_pai_obj.product_id.relacionado_orcamento_ids):
            #for produto_relacionado_obj in item_pai_obj.product_id.relacionado_orcamento_ids:
                #dados = {
                    #'order_id': item_pai_obj.order_id.id,
                    #'product_id': produto_relacionado_obj.produto_relacionado_id.id,
                    #'name': produto_relacionado_obj.produto_relacionado_id.name,
                    #'orcamento_categoria_id': produto_relacionado_obj.produto_relacionado_id.orcamento_categoria_id.id,
                    #'product_uom_qty': produto_relacionado_obj.quantidade * item_pai_obj.product_uom_qty,
                    #'vr_unitario_custo': produto_relacionado_obj.produto_relacionado_id.standard_price,
                    #'vr_total_custo': 0,
                    #'vr_unitario_minimo': produto_relacionado_obj.produto_relacionado_id.preco_minimo or produto_relacionado_obj.produto_relacionado_id.list_price,
                    #'vr_total_minimo': 0,
                    #'vr_unitario_venda': produto_relacionado_obj.produto_relacionado_id.list_price,
                    #'vr_unitario_venda_impostos': produto_relacionado_obj.produto_relacionado_id.list_price,
                    #'usa_unitario_minimo': False,
                    #'margem': produto_relacionado_obj.produto_relacionado_id.orcamento_categoria_id.margem,
                    #'discount': 0,
                    #'vr_unitario_margem_desconto': 0,
                    #'price_subtotal': 0,
                    #'order_line_id': item_pai_obj.id,
                    #'autoinsert': False,
                #}
                #calculo = item_pool.on_change_quantidade_margem_desconto(cr, uid, [], None, None, qty=dados['product_uom_qty'], vr_unitario_custo=dados['vr_unitario_custo'], vr_unitario_minimo=dados['vr_unitario_minimo'], vr_unitario_venda=dados['vr_unitario_venda'], margem=dados['margem'], desconto=dados['discount'], autoinsert=dados['autoinsert'], mudou_quantidade=False, usa_unitario_minimo=dados['usa_unitario_minimo'], context=context)
                #dados['vr_total_custo'] = calculo['value']['vr_total_custo']
                #dados['vr_total_minimo'] = calculo['value']['vr_total_minimo']
                #dados['vr_unitario_venda'] = calculo['value']['vr_unitario_venda']
                ##dados['price_unit'] = calculo['value']['price_unit']
                #dados['vr_total_margem_desconto'] = calculo['value']['vr_total_margem_desconto']
                #dados['vr_unitario_margem_desconto'] = calculo['value']['vr_unitario_margem_desconto']
                ##dados['vr_unitario_venda_impostos'] = calculo['value']['vr_unitario_venda_impostos']

                #item_pool.create(cr, uid, dados)

    def unlink(self, cr, uid, ids, context={}):
        #
        # Não deixa excluir itens de algumas categorias, depois que o
        # saldo da obra for liberado
        # Categorias equipamentos empresa, equipamentos backup, equipamentos TI,
        # infraestrutura
        #
        if 'alimenta_saldo_obra' not in context and 'complementar' not in context:
            for item_obj in self.pool.get('sale.order.line').browse(cr, uid, ids):
                if item_obj.order_id.saldo_obra_liberado:
                    if item_obj.orcamento_categoria_id.id in (1, 2, 5, 3):
                        raise osv.except_osv(u'Inválido!', u'Se o saldo da obra já foi liberado, não é mais permitido excluir os itens da proposta!')

        #for rec in self.browse(cr, uid, ids, context=context):
            #if rec.state not in ['draft', 'cancel']:
                #raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sales order line which is in state \'%s\'!') %(rec.state,))
        return super(osv.Model, self).unlink(cr, uid, ids, context=context)

    def create(self, cr, uid, dados, context={}):
        #
        # Não deixa incluir novos itens de algumas categorias, depois que o
        # saldo da obra for liberado
        # Categorias equipamentos empresa, equipamentos backup, equipamentos TI,
        # infraestrutura
        #
        if 'alimenta_saldo_obra' not in context and 'complementar' not in context:
            if 'order_id' in dados:
                order_obj = self.pool.get('sale.order').browse(cr, uid, dados['order_id'])

                if order_obj.saldo_obra_liberado:
                    if 'orcamento_categoria_id' in dados and dados['orcamento_categoria_id'] in (1, 2, 5, 3):
                        raise osv.except_osv(u'Inválido!', u'Se o saldo da obra já foi liberado, não é mais permitido incluir novos itens na proposta!')

        res = super(sale_order_line, self).create(cr, uid, dados, context)
        return res

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Não deixa alterar as quantidades dos itens de algumas categorias,
        # depois que o saldo da obra for liberado
        # Categorias equipamentos empresa, equipamentos backup, equipamentos TI,
        # infraestrutura
        #
        if 'alimenta_saldo_obra' not in context and 'complementar' not in context:
            #print(dados)
            for item_obj in self.pool.get('sale.order.line').browse(cr, uid, ids):
                if getattr(item_obj, 'order_id', False) and item_obj.order_id.saldo_obra_liberado:
                    if item_obj.orcamento_categoria_id.id in (1, 2, 5, 3):
                        if 'product_uom_qty' in dados:
                            raise osv.except_osv(u'Inválido!', u'Se o saldo da obra já foi liberado, não é mais permitido alterar a quantidade dos itens na proposta!')

                        if 'product_id' in dados:
                            raise osv.except_osv(u'Inválido!', u'Se o saldo da obra já foi liberado, não é mais permitido alterar o produto dos itens na proposta!')

        res = super(sale_order_line, self).write(cr, uid, ids, dados, context)

        #if 'alimenta_saldo_obra' not in context and 'complementar' not in context and 'calculo_resumo' not in context and 'recalcula_fora_validade' not in context:
            ##if 'margem' in dados or 'discount' in dados:
            #self.pool.get('sale.order.line').recalculo_forcado_vendedor(cr, uid, ids, context=context)

        return res

    def recalculo_forcado_vendedor(self, cr, uid, ids, context={}):
        #
        # Quanto o vendedor alterar a quantidade, a margem ou o desconto, vamos forçar o recálculo
        # do item, novamente
        #
        item_pool = self.pool.get('sale.order.line')

        for item_obj in item_pool.browse(cr, uid, ids, context=context):
            #
            # Não recalcula mão de obra
            #
            if item_obj.orcamento_categoria_id.id == 6 and item_obj.order_id.mao_de_obra_instalacao_faturamento_direto:
                continue

            dados_totais = {}
            contexto_item = {
                'default_orcamento_categoria_id': item_obj.orcamento_categoria_id.id,
                'orcamento_aprovado': item_obj.order_id.orcamento_aprovado,
                'default_usa_unitario_minimo': item_obj.order_id.bonificacao_venda,
                'operacao_fiscal_produto_id': item_obj.order_id.operacao_fiscal_produto_id.id,
                'operacao_fiscal_servico_id': item_obj.order_id.operacao_fiscal_servico_id.id,
                'company_id': item_obj.order_id.company_id.id,
            }

            dados_produto = item_pool.product_id_change(cr, uid, [id], item_obj.order_id.pricelist_id.id, item_obj.product_id.id, item_obj.product_uom_qty, False, False, False, item_obj.name, item_obj.order_id.partner_id.id, False, True, item_obj.order_id.date_order, item_obj.product_packaging, item_obj.order_id.fiscal_position, False, contexto_item)
            dados_totais.update(dados_produto['value'])

            contexto_item = {
                'partner_id': item_obj.order_id.partner_id.id,
                'pricelist': item_obj.order_id.pricelist_id.id,
                'shop': item_obj.order_id.shop_id.id,
                'operacao_fiscal_produto_id': item_obj.order_id.operacao_fiscal_produto_id.id,
                'operacao_fiscal_servico_id': item_obj.order_id.operacao_fiscal_servico_id.id,
                'company_id': item_obj.order_id.company_id.id,
                'quantity': item_obj.product_uom_qty,
                'uom': item_obj.product_id.uom_id.id,
            }

            dados_calculo = item_pool.on_change_quantidade_margem_desconto(cr, uid, [id], item_obj.order_id.pricelist_id.id, item_obj.product_id.id, item_obj.product_uom_qty, False, False, False, item_obj.name, item_obj.order_id.partner_id.id, False, True, item_obj.order_id.date_order, item_obj.product_packaging, item_obj.order_id.fiscal_position, False, item_obj.vr_unitario_custo, item_obj.vr_unitario_minimo, item_obj.vr_unitario_venda, item_obj.margem, item_obj.discount, item_obj.autoinsert, False, item_obj.usa_unitario_minimo, contexto_item)

            dados_totais.update(dados_calculo['value'])

            dados_alterar = {}
            for chave in dados_totais:
                #
                # Campos que não existem na tabela, mas tem no objeto.... vai entender...
                #
                if chave in ('price_subtotal', 'uom_id', 'contribuinte', 'documento_id', 'infcomplementar'):
                    continue

                if chave.startswith('tela_'):
                    continue

                if not hasattr(item_obj, chave):
                    continue

                if chave not in item_pool._columns:
                    continue

                if unicode(dados_totais[chave]) == unicode(getattr(item_obj, chave, False)):
                    continue

                if '_id' not in chave and not isinstance(dados_totais[chave], (str, unicode)):
                    if D(dados_totais[chave] or 0) == D(getattr(item_obj, chave, 0)):
                        continue

                #print(chave, unicode(dados_totais[chave]), unicode(getattr(item_obj, chave, False)))
                dados_alterar[chave] = dados_totais[chave]

            if len(dados_alterar):
                sql = """
                    update sale_order_line set
                """
                for chave in dados_alterar:
                    if '_id' in chave:
                        if dados_alterar[chave]:
                            sql += '\n' + chave + ' = ' + str(dados_alterar[chave]) + ','
                        else:
                            sql += '\n' + chave + ' = null,'

                    elif isinstance(dados_alterar[chave], (str, unicode)):
                        sql += '\n' + chave + " = '" + unicode(dados_alterar[chave]).encode('utf-8') + "',"

                    else:
                        sql += '\n' + chave + " = " + str(dados_alterar[chave]) + ','

                sql += 'where id = ' + str(item_obj.id) + ';'

                sql = sql.replace(',where', '\nwhere')

                print(sql)

                cr.execute(sql)

    def nada(self, cr, uid, ids, context={}):
        return {}


sale_order_line()
