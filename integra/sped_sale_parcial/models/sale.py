# -*- encoding: utf-8 -*-
import os
import base64
from sped.models.fields import CampoDinheiro
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.base import DicionarioBrasil
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID
from copy import copy
import decimal_precision as dp
from tools.translate import _
from sale_order_line import *
from finan.wizard.finan_relatorio import Report
DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        currency_pool = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': D(0),
                'amount_tax': D(0),
                'amount_total': D(0),
            }
            valor_sem_impostos = D(0)
            valor_com_impostos = D(0)
            total_impostos = D(0)

            currency_obj = order.pricelist_id.currency_id

            for item_obj in order.order_line:
                valor_sem_impostos += D(item_obj.price_subtotal or 0)
                valor_com_impostos += D(item_obj.vr_total_venda_impostos or 0)
                percentual_impostos = D(item_obj.total_imposto or 0) / D(item_obj.price_subtotal or 1)
                total_impostos += D(item_obj.vr_total_venda_impostos or 0) *  percentual_impostos

            if order.vr_desconto_rateio:
                valor_com_impostos -= D(order.vr_desconto_rateio)

            #res[order.id]['amount_tax'] = currency_pool.round(cr, uid, currency_obj, total_impostos)
            #res[order.id]['amount_untaxed'] = currency_pool.round(cr, uid, currency_obj, valor_sem_impostos)
            #res[order.id]['amount_total'] = currency_pool.round(cr, uid, currency_obj, valor_com_impostos)
            res[order.id]['amount_tax'] = total_impostos
            res[order.id]['amount_untaxed'] = valor_sem_impostos
            res[order.id]['amount_total'] = valor_com_impostos
            print(valor_com_impostos)

        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'operacao_fiscal_produto_id': fields.many2one('sped.operacao', u'Operação fiscal para produtos'),
        'operacao_fiscal_servico_id': fields.many2one('sped.operacao', u'Operação fiscal para serviços'),
        'sped_documento_ids': fields.many2many('sped.documento', 'sale_order_sped_documento', 'sale_order_id', 'sped_documento_id', string=u'Notas Fiscais'),

        'finan_formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'modalidade_frete': fields.selection(MODALIDADE_FRETE, u'Modalidade do frete'),
        'transportadora_id': fields.many2one('res.partner', u'Transportadora', domain=[('cnpj_cpf', '!=', False)]),

        'vr_icms_proprio': CampoDinheiro(u'Valor do ICMS próprio'),
        #'vr_icms_st': CampoDinheiro(u'Valor do ICMS ST'),
        'vr_ipi': CampoDinheiro(u'Valor do IPI'),
        #'vr_ii': CampoDinheiro(u'Valor do imposto de importação'),
        'vr_pis_proprio': CampoDinheiro(u'Valor do PIS próprio'),
        'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS própria'),
        'vr_iss': CampoDinheiro(u'Valor do ISS'),

        #
        # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
        #
        #'vr_pis_retido': CampoDinheiro(u'PIS retido'),
        #'vr_cofins_retido': CampoDinheiro(u'COFINS retida'),
        'vr_csll': CampoDinheiro(u'Valor da CSLL'),
        'vr_irrf': CampoDinheiro(u'Valor do IRRF'),
        #'vr_previdencia': CampoDinheiro(u'Base do INSS'),
        #'vr_iss_retido': CampoDinheiro(u'Valor do ISS'),
        'total_imposto': CampoDinheiro(u'Total dos impostos'),
        'vr_liquido': fields.float(u'Valor líquido'),
        'vr_desconto_rateio': fields.float(u'Valor desconto'),
        'margem_liquida': fields.float(u'Margem líquida'),
        'vr_total_venda_impostos': fields.float(u'Valor venda'),

        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'vr_desconto_rateio'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos'], 10),
            },
            multi='sums', help="The total amount."),
    }

    _defaults = {
        'operacao_fiscal_produto_id': lambda s, cr, uid, c: s.pool.get('res.company').browse(cr, uid, s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c)).operacao_id.id,
        'operacao_fiscal_servico_id': lambda s, cr, uid, c: s.pool.get('res.company').browse(cr, uid, s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c)).operacao_servico_id.id,
    }

    def onchange_cliente_id(self, cr, uid, ids, partner_id, company_id, context={}):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id or not company_id:
            return res

        valores = res['value']

        partner_obj = self.pool.get('res.partner').browse(cr, 1, partner_id)
        company_obj = self.pool.get('res.company').browse(cr, 1, company_id)

        if partner_obj.operacao_fiscal_produto_id:
            valores['operacao_fiscal_produto_id'] = partner_obj.operacao_fiscal_produto_id.id
        elif company_obj.operacao_id:
            valores['operacao_fiscal_produto_id'] = company_obj.operacao_id.id

        if partner_obj.operacao_fiscal_servico_id:
            valores['operacao_fiscal_servico_id'] = partner_obj.operacao_fiscal_servico_id.id
        elif company_obj.operacao_servico_id:
            valores['operacao_fiscal_servico_id'] = company_obj.operacao_servico_id.id

        if partner_obj.finan_formapagamento_id:
            valores['finan_formapagamento_id'] = partner_obj.finan_formapagamento_id.id

        if partner_obj.transportadora_id:
            valores['transportadora_id'] = partner_obj.transportadora_id.id

        return res

    def _gera_itens_nota(self, cr, uid, nota_obj, pedido_item_ids, contexto_item, temporario=False):
        pedido_item_pool = self.pool.get('sale.order.line')
        documento_item_pool = self.pool.get('sped.documentoitem')

        vr_total_rateio_desconto = D(0)
        for pedido_item_obj in self.pool.get('sale.order.line').browse(cr, uid, pedido_item_ids):
            if pedido_item_obj.valor_divergente:
                continue

            vr_total_rateio_desconto += D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty)

        vr_total_rateio_desconto = vr_total_rateio_desconto.quantize(D('0.01'))

        #
        # Adiciona os produtos
        #
        for pedido_item_obj in self.pool.get('sale.order.line').browse(cr, uid, pedido_item_ids):
                if temporario and pedido_item_obj.valor_divergente:
                    pedido_item_pool.write(cr, uid, [pedido_item_obj.id], {'vr_total_venda_impostos': D(pedido_item_obj.vr_unitario_venda_impostos) * D(pedido_item_obj.product_uom_qty)})
                    continue

                #try:
                produto_obj = pedido_item_obj.product_id

                if temporario:
                    dados = {
                        'documento_id': nota_obj,
                        'produto_id': produto_obj.id,
                        'quantidade': pedido_item_obj.product_uom_qty,
                        'quantidade_tributacao': pedido_item_obj.product_uom_qty,
                        'modelo': nota_obj.modelo,
                        'vr_produtos': D(0),
                        'vr_produtos_tributacao': D(0),
                        'vr_operacao': D(0),
                        'vr_operacao_tributacao': D(0),
                        'bc_previdencia': D(0),
                        'vr_previdencia': D(0),
                    }

                else:
                    dados = {
                        'documento_id': nota_obj.id,
                        'produto_id': produto_obj.id,
                        'quantidade': pedido_item_obj.product_uom_qty,
                        'quantidade_tributacao': pedido_item_obj.product_uom_qty,
                        'modelo': nota_obj.modelo,
                    }

                if pedido_item_obj.vr_desconto_rateio > 0:
                    vr_desconto_rateio = D(pedido_item_obj.vr_desconto_rateio)
                    vr_desconto_rateio *= D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty)
                    vr_desconto_rateio /= vr_total_rateio_desconto
                    dados['vr_desconto'] = vr_desconto_rateio

                #
                # Não é mais simulação?
                #
                if not temporario:
                    if hasattr(pedido_item_obj, 'vr_total_venda_impostos'):
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_venda_impostos / pedido_item_obj.product_uom_qty
                    elif getattr(pedido_item_obj, 'usa_unitario_minimo', False):
                        pedido_item_obj.price_unit = pedido_item_obj.vr_unitario_minimo
                    elif hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_margem_desconto / pedido_item_obj.product_uom_qty

                else:
                    #
                    # É simulação
                    #
                    if getattr(pedido_item_obj, 'usa_unitario_minimo', False):
                        pedido_item_obj.price_unit = pedido_item_obj.vr_unitario_minimo
                    elif hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_margem_desconto / pedido_item_obj.product_uom_qty

                taxa = D(0)
                meses = D(0)
                if pedido_item_obj.order_id.payment_term and pedido_item_obj.order_id.payment_term.taxa_juros:
                    taxa = D(pedido_item_obj.order_id.payment_term.taxa_juros) / D(100)

                    if pedido_item_obj.order_id.payment_term.tipo_taxa == '1':
                        taxa = D(pedido_item_obj.order_id.payment_term.taxa_juros) / D(12)

                    meses = D(len(pedido_item_obj.order_id.payment_term.line_ids))

                    #
                    # formula juros compostos
                    #
                    pedido_item_obj.price_unit = D(pedido_item_obj.price_unit) * ((D(1.0) + taxa) ** meses)

                dados['vr_taxa_juros'] = D(taxa)
                dados['vr_unitario'] = pedido_item_obj.price_unit
                dados['vr_unitario_tributacao'] = pedido_item_obj.price_unit

                if temporario:
                    item_obj = DicionarioBrasil()
                    item_obj.update(documento_item_pool._defaults)
                    item_obj.update(contexto_item)
                    item_obj.update(dados)
                    item_obj['uf_partilha_id'] = False
                    item_obj['vr_ibpt'] = D(0)

                    for chave in item_obj:
                        if 'default_' in chave and chave.replace('default_', '') not in item_obj:
                            item_obj[chave.replace('default_')] = item_obj[chave]

                else:
                    item_id = documento_item_pool.create(cr, uid, dados, context=contexto_item)
                    item_obj = documento_item_pool.browse(cr, uid, item_id)

                dados_item = documento_item_pool.onchange_produto(cr, uid, False, produto_obj.id, context=contexto_item)

                if not 'value' in dados_item:
                    raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % produto_obj.name)

                if temporario:
                    item_obj.update(dados_item['value'])
                else:
                    item_obj.write(dados_item['value'])

                dados_item = documento_item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)

                if temporario:
                    item_obj.update(dados_item['value'])

                else:
                    item_obj.write(dados_item['value'])

                if contexto_item.get('ajusta_valor_venda', False) and not (pedido_item_obj.valor_divergente):
                    #
                    # Abrir configuração na empresa para definir a presunção de lucro
                    #  há casos de faturamento anual inferior a 120.000,00 no ano
                    #  em que a presunção de lucro dos serviços cai a 16%, só pra IRPF
                    #  pra CSLL é sempre 32% mesmo
                    #
                    # Cálculo do IRPJ e CSLL para lucro presumido:
                    #
                    # Para produtos, presunção de lucro de 8%
                    # Para serviços, presunção de lucro de 32%
                    #
                    # alíquota do IRPJ:
                    #     para lucro abaixo de 20.000 (faturamento * 8%) no mês corrente: 15%
                    #     para lucro acima ou igual a 20.000 (faturamento * 8%) no mês corrente: 25%
                    #     no caso de serviços, o lucro seria faturamento * 32%
                    #
                    # Para CSLL:
                    #   para produtos, presunção de lucro de 12%
                    #   para serviços, presunção de lucro de 32%
                    # alíquota da CSLL: 9%, para produto ou serviço
                    #
                    total_impostos = dados_item['value']['vr_icms_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_ipi'] or D('0')
                    total_impostos += dados_item['value']['vr_pis_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_cofins_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_iss'] or D('0')
                    vr_irrf = D('0')
                    vr_csll = D('0')
                    if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
                    #if nota_obj.company_id.al_pis_cofins_id.al_pis == 0.65:
                        lucro_servico = D('0')
                        lucro_produto = D('0')

                        if produto_obj.type == 'service':
                            lucro_servico = dados_item['value']['vr_nf'] or D('0')
                            lucro_servico *= D('32') / D('100')

                        else:
                            lucro_produto = dados_item['value']['vr_nf'] or D('0')
                            lucro_produto *= D('8') / D('100')

                        vr_irrf = lucro_produto * D('25') / D('100')
                        vr_irrf += lucro_servico * D('25') / D('100')
                        vr_irrf = vr_irrf.quantize(D('0.01'))
                        total_impostos += vr_irrf

                        if produto_obj.type == 'service':
                            lucro_servico = dados_item['value']['vr_nf'] or D('0')
                            lucro_servico *= D('32') / D('100')

                        else:
                            lucro_produto = dados_item['value']['vr_nf'] or D('0')
                            lucro_produto *= D('12') / D('100')

                        vr_csll = lucro_produto * D('9') / D('100')
                        vr_csll += lucro_servico * D('9') / D('100')
                        vr_csll = vr_csll.quantize(D('0.01'))
                        total_impostos += vr_csll

                    #if hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                    #    if pedido_item_obj.vr_total_margem_desconto:
                    #        proporcao_impostos = total_impostos / D(pedido_item_obj.vr_total_margem_desconto)
                    #    else:
                    #        proporcao_impostos = D(0)
                    #elif pedido_item_obj.price_subtotal:
                    try:
                        proporcao_impostos = total_impostos / (D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty))
                    except:
                        proporcao_impostos = D(0)

                    #
                    # Faz uma prévia para o lucro real
                    #
                    price_unit = D(pedido_item_obj.price_unit) / (D(1) - proporcao_impostos)
                    price_unit = price_unit.quantize(D('0.01'))

                    #if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL:
                        #preco_final_provisorio = price_unit * D(pedido_item_obj.product_uom_qty)
                        #lucro_produto = preco_final_provisorio - D(pedido_item_obj.vr_total_minimo or 0)
                        #lucro_produto -= preco_final_provisorio * proporcao_impostos

                        #print(price_unit, lucro_produto, preco_final_provisorio, proporcao_impostos)

                        ##
                        ## 15% de IR e 9% CSLL
                        ##
                        #vr_irrf = lucro_produto * D('15') / D('100')
                        #vr_irrf = vr_irrf.quantize(D('0.01'))
                        #total_impostos += vr_irrf

                        #vr_csll = lucro_produto * D('9') / D('100')
                        #vr_csll = vr_csll.quantize(D('0.01'))
                        #total_impostos += vr_csll

                    try:
                        proporcao_impostos = total_impostos / (D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty))
                    except:
                        proporcao_impostos = D(0)

                    print('irrf', vr_irrf, 'csll', vr_csll)

                    price_unit = D(pedido_item_obj.price_unit) / (D(1) - proporcao_impostos)
                    price_unit = price_unit.quantize(D('0.01'))
                    dados_item['value']['vr_irrf'] = vr_irrf
                    dados_item['value']['vr_csll'] = vr_csll
                    dados_item['value']['vr_unitario_venda_impostos'] = price_unit
                    dados_item['value']['porcentagem_imposto'] = proporcao_impostos * D(100)
                    dados_item['value']['proporcao_imposto'] = (D(1) - proporcao_impostos) * D(100)
                    dados_item['value']['vr_total_venda_impostos'] = price_unit * D(pedido_item_obj.product_uom_qty)
                    dados_item['value']['falha_configuracao'] = False
                    dados_item['value']['total_imposto'] = total_impostos
                    #print('atualiza nota', price_unit, price_unit * D(pedido_item_obj.product_uom_qty), pedido_item_obj.product_id.name_template, proporcao_impostos)

                #pedido_item_pool.write(cr, uid, [pedido_item_obj.id], dados_item['value'], context={'calculo_resumo': True})
                pedido_item_pool.write(cr, uid, [pedido_item_obj.id], dados_item['value'])
                #pedido_item_obj.write(dados_item['value'], context={'calculo_resumo': True})
                nota_obj.vr_icms_proprio = D(nota_obj.vr_icms_proprio or 0) + D(dados_item['value']['vr_icms_proprio'] or 0)
                nota_obj.vr_ipi = D(nota_obj.vr_ipi or 0) + D(dados_item['value']['vr_ipi'] or 0)
                nota_obj.vr_pis_proprio = D(nota_obj.vr_pis_proprio or 0) + D(dados_item['value']['vr_pis_proprio'] or 0)
                nota_obj.vr_cofins_proprio = D(nota_obj.vr_cofins_proprio or 0) + D(dados_item['value']['vr_cofins_proprio'] or 0)
                nota_obj.vr_iss = D(nota_obj.vr_iss or 0) + D(dados_item['value']['vr_iss'] or 0)
                #nota_obj.vr_irrf = D(nota_obj.vr_irrf or 0) + D(vr_irrf or 0)
                #nota_obj.vr_csll = D(nota_obj.vr_csll or 0) + D(vr_csll or 0)

                #except Exception as e:
                    #if e.message:
                        #mensagem = e.message
                    #elif len(e.args) > 1:
                        #mensagem = e.args[1]
                    #else:
                        #mensagem = unicode(e)

                    #print(mensagem)
                    #pedido_item_obj.write({'falha_configuracao': mensagem})

    def gera_notas(self, cr, uid, ids, context={}):
        res = {}
        documento_pool = self.pool.get('sped.documento')

        temporario = context.get('temporario', False)
        notas_1_N_pedidos = context.get('notas_1_N_pedidos', False)
        nota_produto_obj = context.get('nota_produto_obj', None)
        nota_servico_obj = context.get('nota_produto_obj', None)
        ajusta_valor_venda = context.get('ajusta_valor_venda', False)

        for pedido_obj in self.browse(cr, uid, ids):
            #
            # Verifica se tem produtos para a nota de produtos, e serviços
            # para a nota de serviços
            #
            produto_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '!=', 'service')])
            servico_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '=', 'service')])

            #print('produto_ids', produto_ids)
            #print('servico_ids', servico_ids)

            if produto_ids and not pedido_obj.operacao_fiscal_produto_id:
                break
                #raise osv.except_osv(u'Inválido!', u'Não foi informada nenhuma operação fiscal para o faturamento dos produtos!')

            if servico_ids and not pedido_obj.operacao_fiscal_servico_id:
                break
                #raise osv.except_osv(u'Inválido!', u'Não foi informada nenhuma operação fiscal para o faturamento dos serviços!')

            impostos = {
                'vr_icms_proprio': D('0'),
                #'vr_icms_st': D('0'),
                'vr_ipi': D('0'),
                #'vr_ii': D('0'),
                'vr_pis_proprio': D('0'),
                'vr_cofins_proprio': D('0'),
                'vr_iss': D('0'),
                #'vr_pis_retido': D('0'),
                #'vr_cofins_retido': D('0'),
                'vr_csll': D('0'),
                'vr_irrf': D('0'),
                #'vr_previdencia': D('0'),
                'total_imposto': D('0'),
            }
            total_nf_produto = D('0')
            total_nf_servico = D('0')

            if produto_ids and pedido_obj.operacao_fiscal_produto_id:
                operacao_obj = pedido_obj.operacao_fiscal_produto_id

                if temporario:
                    dados = copy(documento_pool._defaults)
                    dados.update({
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                    })

                    for chave in dados:
                        if hasattr(dados[chave], '__call__'):
                            dados[chave] = dados[chave](documento_pool, cr, uid, {'modelo': '55', 'default_modelo': '55', 'temporario': temporario})

                else:
                    dados = {
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                        #'municipio_fato_gerador_id': municipio_id,
                        #'finan_contrato_id': contrato_obj.id,
                        #'finan_lancamento_id': lancamento_obj.id,
                        'sale_order_ids': [(6, 0, [pedido_obj.id])],
                    }


                #
                # Gera o registro da NF-e
                #
                if temporario:
                    nota_obj = DicionarioBrasil()
                    nota_obj.update(dados)
                    dados_operacao = documento_pool.onchange_operacao(cr, uid, False, operacao_obj.id)
                    nota_obj.update(dados_operacao['value'])

                else:
                    nota_id = documento_pool.create(cr, uid, dados, context={'modelo': '55', 'default_modelo': '55', 'temporario': temporario})
                    nota_obj = documento_pool.browse(cr, uid, nota_id)
                    dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)
                    nota_obj.write(dados_operacao['value'])

                contexto_item = copy(dados)
                contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
                for chave in dados:
                    if 'default_' not in chave:
                        contexto_item['default_' + chave] = contexto_item[chave]

                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao

                self._gera_itens_nota(cr, uid, nota_obj, produto_ids, contexto_item, temporario)

                if not temporario:
                    nota_obj.ajusta_impostos_retidos()
                    nota_obj.write({'numero': nota_obj.numero - 1})
                    nota_obj.write({'numero': nota_obj.numero})
                    nota_obj = documento_pool.browse(cr, uid, nota_obj.id)

                impostos['vr_icms_proprio'] += D(str(nota_obj.vr_icms_proprio))
                #impostos['vr_icms_st'] += D(str(nota_obj.vr_icms_st))
                impostos['vr_ipi'] += D(str(nota_obj.vr_ipi))
                #impostos['vr_ii'] += D(str(nota_obj.vr_ii))
                impostos['vr_pis_proprio'] += D(str(nota_obj.vr_pis_proprio))
                impostos['vr_cofins_proprio'] += D(str(nota_obj.vr_cofins_proprio))
                impostos['vr_iss'] += D(str(nota_obj.vr_iss))
                #impostos['vr_pis_retido'] += D(str(nota_obj.vr_pis_retido))
                #impostos['vr_cofins_retido'] += D(str(nota_obj.vr_cofins_retido))
                #impostos['vr_csll'] += D(str(nota_obj.vr_csll))
                #impostos['vr_irrf'] += D(str(nota_obj.vr_irrf))
                #impostos['vr_previdencia'] += D(str(nota_obj.vr_previdencia))
                #impostos['vr_iss_retido'] += D(str(nota_obj.vr_iss_retido))
                total_nf_produto = D(str(nota_obj.vr_nf))

                if not temporario:
                    #
                    # Ajusta a condição de pagamento e as duplicatas
                    #
                    cond_pag_obj = None
                    #print(pedido_obj.payment_term, 'condicao de pagamento do pedido')
                    if pedido_obj.payment_term:
                        cond_pag_obj = pedido_obj.payment_term
                        nota_obj.write({'payment_term_id': cond_pag_obj.id})

                    elif operacao_obj.payment_term_id:
                        cond_pag_obj = operacao_obj.payment_term_id

                    #print(cond_pag_obj, 'condicao de pagamento')

                    if cond_pag_obj:
                        dados = nota_obj.onchange_payment_term(cond_pag_obj.id, nota_obj.vr_fatura, nota_obj.vr_nf, nota_obj.data_emissao, [])
                        nota_obj.write(dados['value'])



                #lancamento_obj.write({'sped_documento_id': nota_obj.id, 'valor_documento': nota_obj.vr_fatura, 'provisionado': False})

            servico_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '=', 'service')])
            if servico_ids and pedido_obj.operacao_fiscal_servico_id:
                operacao_obj = pedido_obj.operacao_fiscal_servico_id

                if temporario:
                    dados = copy(documento_pool._defaults)
                    dados.update({
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                    })

                    for chave in dados:
                        if hasattr(dados[chave], '__call__'):
                            dados[chave] = dados[chave](documento_pool, cr, uid, {'modelo': '55', 'default_modelo': '55', 'temporario': temporario})
                else:
                    dados = {
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                        #'municipio_fato_gerador_id': municipio_id,
                        #'finan_contrato_id': contrato_obj.id,
                        #'finan_lancamento_id': lancamento_obj.id,
                        'sale_order_ids': [(6, 0, [pedido_obj.id])],
                    }

                if pedido_obj.company_id.company_servico_id:
                    dados['company_id'] = pedido_obj.company_id.company_servico_id.id
                    dados['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                #
                # Gera o registro da NF-e
                #
                if temporario:
                    nota_obj = DicionarioBrasil()
                    nota_obj.update(dados)
                    dados_operacao = documento_pool.onchange_operacao(cr, uid, False, operacao_obj.id)

                    if pedido_obj.company_id.company_servico_id:
                        #
                        # Resgata o regime tributário da empresa
                        #
                        dados_operacao['value']['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                    nota_obj.update(dados_operacao['value'])


                else:
                    nota_id = documento_pool.create(cr, uid, dados, context={'modelo': 'SE', 'default_modelo': 'SE', 'temporario': temporario})
                    nota_obj = documento_pool.browse(cr, uid, nota_id)
                    dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)

                    if pedido_obj.company_id.company_servico_id:
                        #
                        # Resgata o regime tributário da empresa
                        #
                        dados_operacao['value']['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                    nota_obj.write(dados_operacao['value'])

                contexto_item = copy(dados)
                contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
                for chave in dados:
                    if 'default_' not in chave:
                        contexto_item['default_' + chave] = contexto_item[chave]

                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao

                #print('vai gerar itens de serviço', servico_ids)
                self._gera_itens_nota(cr, uid, nota_obj, servico_ids, contexto_item, temporario)

                if not temporario:
                    nota_obj.ajusta_impostos_retidos()
                    nota_obj.write({'numero': nota_obj.numero - 1})
                    nota_obj.write({'numero': nota_obj.numero})
                    nota_obj = documento_pool.browse(cr, uid, nota_obj.id)

                impostos['vr_icms_proprio'] += D(str(nota_obj.vr_icms_proprio))
                #impostos['vr_icms_st'] += D(str(nota_obj.vr_icms_st))
                impostos['vr_ipi'] += D(str(nota_obj.vr_ipi))
                #impostos['vr_ii'] += D(str(nota_obj.vr_ii))
                impostos['vr_pis_proprio'] += D(str(nota_obj.vr_pis_proprio))
                impostos['vr_cofins_proprio'] += D(str(nota_obj.vr_cofins_proprio))
                impostos['vr_iss'] += D(str(nota_obj.vr_iss))
                #impostos['vr_pis_retido'] += D(str(nota_obj.vr_pis_retido))
                #impostos['vr_cofins_retido'] += D(str(nota_obj.vr_cofins_retido))
                #impostos['vr_csll'] += D(str(nota_obj.vr_csll))
                #impostos['vr_irrf'] += D(str(nota_obj.vr_irrf))
                #impostos['vr_previdencia'] += D(str(nota_obj.vr_previdencia))
                #impostos['vr_iss_retido'] += D(str(nota_obj.vr_iss_retido))
                total_nf_servico = D(str(nota_obj.vr_nf))

            total_imposto = D('0')
            total_imposto += impostos['vr_icms_proprio']
            #total_imposto += impostos['vr_icms_st']
            total_imposto += impostos['vr_ipi']
            #total_imposto += impostos['vr_ii']
            total_imposto += impostos['vr_pis_proprio']
            total_imposto += impostos['vr_cofins_proprio']
            total_imposto += impostos['vr_iss']

            #
            # Abrir configuração na empresa para definir a presunção de lucro
            #  há casos de faturamento anual inferior a 120.000,00 no ano
            #  em que a presunção de lucro dos serviços cai a 16%, só pra IRPF
            #  pra CSLL é sempre 32% mesmo
            #
            # Cálculo do IRPJ e CSLL para lucro presumido:
            #
            # Para produtos, presunção de lucro de 8%
            # Para serviços, presunção de lucro de 32%
            #
            # alíquota do IRPJ:
            #     para lucro abaixo de 20.000 (faturamento * 8%) no mês corrente: 15%
            #     para lucro acima ou igual a 20.000 (faturamento * 8%) no mês corrente: 25%
            #     no caso de serviços, o lucro seria faturamento * 32%
            #
            # Para CSLL:
            #   para produtos, presunção de lucro de 12%
            #   para serviços, presunção de lucro de 32%
            # alíquota da CSLL: 9%, para produto ou serviço
            #
            if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
            #if pedido_obj.company_id.al_pis_cofins_id.al_pis == 0.65:
                lucro_produto = total_nf_produto * D('8') / D('100')
                lucro_servico = total_nf_servico * D('32') / D('100')
                impostos['vr_irrf'] = lucro_produto * D('25') / D('100')
                impostos['vr_irrf'] += lucro_servico * D('25') / D('100')
                total_imposto += impostos['vr_irrf']

                lucro_produto = total_nf_produto * D('12') / D('100')
                lucro_servico = total_nf_servico * D('32') / D('100')
                impostos['vr_csll'] = lucro_produto * D('9') / D('100')
                impostos['vr_csll'] += lucro_servico * D('9') / D('100')
                total_imposto += impostos['vr_csll']

            #elif nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
                #lucro_produto =

            #total_imposto += impostos['vr_previdencia']
            impostos['total_imposto'] = total_imposto

            if hasattr(pedido_obj, 'vr_total_margem_desconto'):
                valor_liquido = D(str(pedido_obj.vr_total_margem_desconto))
            else:
                valor_liquido = D(pedido_obj.amount_total)

            if hasattr(pedido_obj, 'vr_total_custo'):
                valor_liquido -= D(str(pedido_obj.vr_total_custo))

            valor_liquido -= total_imposto

            if hasattr(pedido_obj, 'vr_comissao'):
                valor_liquido -= D(str(pedido_obj.vr_comissao))

            impostos['vr_liquido'] = valor_liquido
            try:
                if hasattr(pedido_obj, 'vr_total_margem_desconto'):
                    impostos['margem_liquida'] = valor_liquido / D(str(pedido_obj.vr_total_margem_desconto)) * 100
                else:
                    impostos['margem_liquida'] = valor_liquido / D(pedido_obj.amount_total) * 100

            except:
                impostos['margem_liquida'] = 0

            pedido_obj.write(impostos)

        return res

    def button_dummy(self, cr, uid, ids, context={}):
        context['temporario'] = True
        context['ajusta_valor_venda'] = True
        return self.gera_notas(cr, uid, ids, context)

    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if company_obj.operacao_id:
            valores['operacao_fiscal_produto_id'] = company_obj.operacao_id.id

        if company_obj.operacao_servico_id:
            valores['operacao_fiscal_servico_id'] = company_obj.operacao_servico_id.id

        return res

    def imprime_pedido_venda(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        pedido_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'integra_pedido_venda.jrxml')
        recibo = 'pedido_venda_'+ pedido_obj.name + '.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, 1, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'sale.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

sale_order()
