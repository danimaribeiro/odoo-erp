# -*- encoding: utf-8 -*-


from datetime import datetime
from osv import osv, fields
from openerp import SUPERUSER_ID
from tools.translate import _
from sped.models.fields import *
from sped.constante_tributaria import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from pybrasil.data import hoje
from copy import copy


STORE_CUSTO = True


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    def _get_calcula_custo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            vr_custo = D(str(item_obj.vr_produtos))
            vr_custo += D(str(item_obj.vr_frete))
            vr_custo += D(str(item_obj.vr_seguro))
            vr_custo += D(str(item_obj.vr_outras))
            vr_custo -= D(str(item_obj.vr_desconto))
            vr_custo += D(str(item_obj.vr_ipi))
            vr_custo += D(str(item_obj.vr_icms_st))
            vr_custo += D(str(item_obj.vr_ii))
            vr_custo += D(str(item_obj.vr_diferencial_aliquota))
            vr_custo += D(str(item_obj.vr_simples))

            #
            # Crédito de ICMS para compra do ativo imobilizado é recebido em 48 ×
            # por isso, como a empresa pode não receber esse crédito de fato,
            # não considera o abatimento do crédito na formação do custo
            #
            if item_obj.credita_icms_proprio and item_obj.cfop_id.codigo not in ['1551', '2551']:
                vr_custo -= D(str(item_obj.vr_icms_proprio))

            if item_obj.credita_icms_st:
                vr_custo -= D(str(item_obj.vr_icms_st))
            if item_obj.credita_ipi:
                vr_custo -= D(str(item_obj.vr_ipi))
            if item_obj.credita_pis_cofins:
                vr_custo -= D(str(item_obj.vr_ipi))
                vr_custo -= D(str(item_obj.vr_cofins))

            #if item_obj.documento_id.vr_produtos:
                #proporcao_item = D(str(item_obj.vr_produtos)) / D(str(item_obj.documento_id.vr_produtos))
            #else:
                #proporcao_item = D('0')
            proporcao_item = D('1')

            vr_frete_rateio = D('0')
            vr_seguro_rateio = D('0')
            vr_outras_rateio = D('0')
            vr_desconto_rateio = D('0')

            #
            # Ajusta o rateio dos valores avulsos
            #
            #if item_obj.documento_id.vr_frete_rateio:
                #vr_frete_rateio = D(str(item_obj.documento_id.vr_frete_rateio)) * proporcao_item
                #vr_custo += vr_frete_rateio
            #if item_obj.documento_id.vr_seguro_rateio:
                #vr_seguro_rateio = D(str(item_obj.documento_id.vr_seguro_rateio)) * proporcao_item
                #vr_custo += vr_seguro_rateio
            #if item_obj.documento_id.vr_desconto_rateio:
                #vr_desconto_rateio = D(str(item_obj.documento_id.vr_desconto_rateio)) * proporcao_item
                #vr_custo -= vr_desconto_rateio
            #if item_obj.documento_id.vr_outras_rateio:
                #vr_outras_rateio = D(str(item_obj.documento_id.vr_outras_rateio)) * proporcao_item
                #vr_custo += vr_outras_rateio

            vr_custo = vr_custo.quantize(D('0.01'))

            if item_obj.quantidade_estoque is not None and item_obj.quantidade_estoque > 0:
                vr_unitario_custo = vr_custo / D(str(item_obj.quantidade_estoque))
            else:
                vr_unitario_custo = D('0')

            vr_unitario_custo = vr_unitario_custo.quantize(D('0.0000000001'))

            if nome_campo == 'vr_custo':
                res[item_obj.id] = vr_custo
            elif nome_campo == 'vr_unitario_custo':
                res[item_obj.id] = vr_unitario_custo
            elif nome_campo == 'vr_frete_rateio':
                res[item_obj.id] = vr_frete_rateio
            elif nome_campo == 'vr_seguro_rateio':
                res[item_obj.id] = vr_seguro_rateio
            elif nome_campo == 'vr_outras_rateio':
                res[item_obj.id] = vr_outras_rateio
            elif nome_campo == 'vr_desconto_rateio':
                res[item_obj.id] = vr_desconto_rateio

        return res

    def _field_readonly(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        nome_campo = nome_campo.replace('_readonly', '')

        for obj in self.browse(cr, uid, ids, context=context):
            if nome_campo[-3:] == '_id':
                campo = getattr(obj, nome_campo, False)

                if campo:
                    res[obj.id] = campo.id
                else:
                    res[obj.id] = False

            else:
                res[obj.id] = getattr(obj, nome_campo, False)

        return res

    _columns = {
        'tipo_item': fields.selection((('P', u'Produto'), ('S', u'Serviço'), ('M', u'Mensalidade')), u'Tipo'),
        'documento_id': fields.many2one('sped.documento', u'Documento', required=False, ondelete='set null', select=True),
        'company_id': fields.related('documento_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=True, select=True),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário', select=True),
        'emissao': fields.related('documento_id', 'emissao', type='char', string=u'Tipo de emissão', store=True, select=True),
        'numero': fields.related('documento_id', 'numero', type='integer', string=u'Número'),
        'operacao_id': fields.related('documento_id', 'operacao_id', type='many2one', string=u'Operação fiscal', relation='sped.operacao', store=True, select=True),
        #'participante_id': fields.related('documento_id', 'participante_id', type='many2one', string=u'Participante', relation='sped.participante'),
        'partner_id': fields.related('documento_id', 'partner_id', type='many2one', string=u'Destinatário/remetente', relation='res.partner', store=True, select=True),
        'data_emissao': fields.related('documento_id', 'data_emissao', type='date', string=u'Data de emissão', store=True, select=True),
        'modelo': fields.related('documento_id', 'modelo', type='char', string=u'Modelo', store=True, select=True),

        'cfop_id': fields.many2one('sped.cfop', u'CFOP', ondelete='restrict', select=True),
        'compoe_total': fields.boolean(u'Compõe o valor total da NF-e?', select=True),
        'movimentacao_fisica': fields.boolean(u'Há movimentação física do produto?'),

        # Dados do produto/serviço
        'produto_id': fields.many2one('product.product', u'Produto/Serviço', ondelete='restrict', select=True),
        'uom_id': fields.related('produto_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', select=True, readonly=True),
        'quantidade': CampoQuantidade(u'Quantidade'),
        # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
        'vr_unitario': CampoValorUnitario(u'Preço unitário'),
        'vr_unitario_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor unitário', store=False),
        'price_unit_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Preço unitário', store=False),

        'price_unit_original': CampoValorUnitario(u'Valor unitário original'),
        'price_unit_original_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor unitário original', store=False),
        'vr_unitario_base': CampoValorUnitario(u'Valor unitário base para a venda'),
        'vr_unitario_base_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor unitário base para a venda', store=False),

        # Quantidade de tributação
        'quantidade_tributacao': CampoQuantidade(u'Quantidade para tributação'),
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': CampoValorUnitario(u'Valor unitário para tributação'),

        # Valor total dos produtos
        'vr_produtos': CampoDinheiro(u'Valor do produto/serviço'),
        'vr_produtos_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do produto/serviço', store=False),
        'vr_produtos_tributacao': CampoDinheiro(u'Valor do produto/serviço para tributação'),
        'vr_produto_original': CampoDinheiro(u'Valor original do produto/serviço'),
        'vr_produto_original_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor original do produto/serviço', store=False),
        'vr_produto_base': CampoDinheiro(u'Valor base do produto/serviço original'),
        'vr_produto_base_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor base do produto/serviço original', store=False),

        # Outros valores acessórios
        'vr_frete': CampoDinheiro(u'Valor do frete'),
        'vr_seguro': CampoDinheiro(u'Valor do seguro'),
        'vr_desconto': CampoDinheiro(u'Valor do desconto'),
        'vr_outras': CampoDinheiro(u'Outras despesas acessórias'),
        'vr_operacao': CampoDinheiro(u'Valor da operação'),
        'vr_operacao_tributacao': CampoDinheiro(u'Valor da operação para tributação'),

        #
        # ICMS próprio
        #
        'contribuinte': fields.related('partner_id', 'contribuinte', type='char', string=u'Contribuinte', store=False, select=True),
        'org_icms': fields.selection(ORIGEM_MERCADORIA, u'Origem da mercadoria', select=True),
        'cst_icms': fields.selection(ST_ICMS, u'Situação tributária do ICMS', select=True),
        'partilha': fields.boolean(u'Partilha de ICMS entre estados (CST 10 ou 90)?'),
        'al_bc_icms_proprio_partilha': CampoPorcentagem(u'% da base de cálculo da operação própria'),
        'uf_partilha_id': fields.many2one('sped.estado', u'Estado para o qual é devido o ICMS ST', select=True),
        'repasse': fields.boolean(u'Repasse de ICMS retido anteriosvente entre estados (CST 41)?', select=True),
        'md_icms_proprio': fields.selection(MODALIDADE_BASE_ICMS_PROPRIO, u'Modalidade da base de cálculo do ICMS próprio'),
        'pr_icms_proprio': CampoQuantidade(u'Parâmetro do ICMS próprio'),
        'rd_icms_proprio': CampoPorcentagem(u'% de redução da base de cálculo do ICMS próprio'),
        'bc_icms_proprio_com_ipi': fields.boolean('IPI integra a base do ICMS próprio?'),
        'bc_icms_proprio': CampoDinheiro(u'Base do ICMS próprio'),
        'al_icms_proprio': CampoPorcentagem(u'alíquota do ICMS próprio'),
        'vr_icms_proprio': CampoDinheiro(u'valor do ICMS próprio'),
        'vr_icms_proprio_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'valor do ICMS próprio', store=False),

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': fields.selection(ST_ICMS_SN, u'Situação tributária do ICMS - Simples Nacional', select=True),
        'al_icms_sn': CampoPorcentagem(u'Alíquota do crédito de ICMS'),
        'rd_icms_sn': CampoPorcentagem(u'% estadual de redução da alíquota de ICMS'),
        'vr_icms_sn': CampoDinheiro(u'valor do crédito de ICMS - SIMPLES Nacional'),
        'vr_icms_sn': CampoDinheiro(u'valor do crédito de ICMS - SIMPLES Nacional'),
        'al_simples': CampoDinheiro(u'Alíquota do SIMPLES Nacional'),
        'vr_simples': CampoDinheiro(u'Valor do SIMPLES Nacional'),
        'vr_simples_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do SIMPLES Nacional', store=False),

        #
        # ICMS ST
        #
        'md_icms_st': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo do ICMS ST'),
        'pr_icms_st': CampoQuantidade(u'Parâmetro do ICMS ST'),
        'rd_icms_st': CampoPorcentagem(u'% de redução da base de cálculo do ICMS ST'),
        'bc_icms_st_com_ipi': fields.boolean(u'IPI integra a base do ICMS ST?'),
        'bc_icms_st': CampoDinheiro(u'Base do ICMS ST'),
        'al_icms_st': CampoPorcentagem(u'Alíquota do ICMS ST'),
        'vr_icms_st': CampoDinheiro(u'Valor do ICMS ST'),
        'vr_icms_st_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do ICMS ST', store=False),

        #
        # Parâmetros relativos ao ICMS retido anteriosvente por substituição tributária
        # na origem
        #
        'md_icms_st_retido': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo'),
        'pr_icms_st_retido': CampoQuantidade(u'Parâmetro da base de cáculo'),
        'rd_icms_st_retido': CampoPorcentagem(u'% de redução da base de cálculo do ICMS retido'),
        'bc_icms_st_retido': CampoDinheiro(u'Base do ICMS ST retido na origem'),
        'al_icms_st_retido': CampoPorcentagem(u'Alíquota do ICMS ST retido na origem'),
        'vr_icms_st_retido': CampoDinheiro(u'Valor do ICMS ST retido na origem'),

        #
        # IPI padrão
        #
        'apuracao_ipi': fields.selection(APURACAO_IPI, u'Período de apuração do IPI', select=True),
        'cst_ipi': fields.selection(ST_IPI, u'Situação tributária do IPI', select=True),
        'md_ipi': fields.selection(MODALIDADE_BASE_IPI, u'Modalidade de cálculo do IPI'),
        'bc_ipi': CampoDinheiro(u'Base do IPI'),
        'al_ipi': CampoQuantidade(u'Alíquota do IPI'),
        'vr_ipi': CampoDinheiro(u'Valor do IPI'),
        'vr_ipi_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do IPI', store=False),

        #
        # Imposto de importação
        #
        'bc_ii': CampoDinheiro(u'Base do imposto de importação'),
        'vr_despesas_aduaneiras': CampoDinheiro(u'Despesas aduaneiras'),
        'vr_ii': CampoDinheiro(u'Valor do imposto de importação'),
        'vr_iof': CampoDinheiro(u'Valor do IOF'),

        #
        # PIS próprio
        #
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota e CST do PIS-COFINS', select=True),
        'cst_pis': fields.selection(ST_PIS, u'Situação tributária do PIS', select=True),
        'md_pis_proprio': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS próprio'),
        'bc_pis_proprio': CampoDinheiro(u'Base do PIS próprio'),
        'al_pis_proprio': CampoQuantidade(u'Alíquota do PIS próprio'),
        'vr_pis_proprio': CampoDinheiro(u'Valor do PIS próprio'),
        'vr_pis_proprio_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do PIS próprio', store=False),

        #
        # COFINS própria
        #
        'cst_cofins': fields.selection(ST_COFINS, u'Situação tributária da COFINS', select=True),
        'md_cofins_proprio': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS própria'),
        'bc_cofins_proprio': CampoDinheiro(u'Base do COFINS próprio'),
        'al_cofins_proprio': CampoQuantidade(u'Alíquota da COFINS própria'),
        'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS próprio'),
        'vr_cofins_proprio_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do COFINS próprio', store=False),

        #
        # PIS ST
        #
        'md_pis_st': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS ST'),
        'bc_pis_st': CampoDinheiro(u'Base do PIS ST'),
        'al_pis_st': CampoQuantidade(u'Alíquota do PIS ST'),
        'vr_pis_st': CampoDinheiro(u'Valor do PIS ST'),

        #
        # COFINS ST
        #
        'md_cofins_st': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS ST'),
        'bc_cofins_st': CampoDinheiro(u'Base do COFINS ST'),
        'al_cofins_st': CampoQuantidade(u'Alíquota da COFINS ST'),
        'vr_cofins_st': CampoDinheiro(u'Valor do COFINS ST'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': CampoDinheiro(u'Valor dos serviços'),

        # ISS
        'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS', select=True),
        'bc_iss': CampoDinheiro(u'Base do ISS'),
        'al_iss': CampoDinheiro(u'Alíquota do ISS'),
        'vr_iss': CampoDinheiro(u'Valor do ISS'),
        'vr_iss_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do ISS', store=False),

        # PIS e COFINS
        'vr_pis_servico': CampoDinheiro(u'PIS sobre serviços'),
        'vr_cofins_servico': CampoDinheiro(u'COFINS sobre serviços'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': CampoDinheiro(u'Valor da NF', required=False),
        'vr_fatura': CampoDinheiro(u'Valor da fatura'),
        'al_ibpt': CampoPorcentagem(u'Alíquota IBPT'),
        'vr_ibpt': CampoDinheiro(u'Valor IBPT'),

        # Previdência social
        'previdencia_retido': fields.boolean(u'INSS retido?', select=True),
        'bc_previdencia': CampoDinheiro(u'Base do INSS'),
        'al_previdencia': CampoPorcentagem(u'Alíquota do INSS'),
        'vr_previdencia': CampoDinheiro(u'Valor do INSS'),

        # Informações adicionais
        'infcomplementar': fields.text(u'Informações complementares'),

        #
        # Dados especiais para troca de informações entre empresas
        #
        'numero_pedido': fields.char(u'Número do pedido', size=15),
        'numero_item_pedido': fields.integer(u'Número do item pedido'),

        #
        # Campos para a validação das entradas
        #
        'produto_codigo': fields.char(u'Código do produto original', size=60, select=True),
        'produto_descricao': fields.char(u'Descrição do produto original', size=60, select=True),
        'produto_ncm': fields.char(u'NCM do produto original', size=60, select=True),
        'produto_codigo_barras': fields.char(u'Código de barras do produto original', size=60, select=True),
        'unidade': fields.char(u'Unidade do produto original', size=6, select=True),
        'unidade_tributacao': fields.char(u'Unidade de tributação do produto original', size=6, select=True),
        'fator_quantidade': fields.float(u'Fator de conversão da quantidade'),
        'quantidade_original': CampoQuantidade(u'Quantidade'),
        'quantidade_estoque': CampoQuantidade(u'Quantidade'),
        'cfop_original_id': fields.many2one('sped.cfop', u'CFOP original', select=True),

        'credita_icms_proprio': fields.boolean(u'Credita ICMS próprio?', select=True),
        'credita_icms_st': fields.boolean(u'Credita ICMS ST?', select=True),
        'informa_icms_st': fields.boolean(u'Informa ICMS ST?', select=True),
        'credita_ipi': fields.boolean(u'Credita IPI?', select=True),
        'credita_pis_cofins': fields.boolean(u'Credita PIS-COFINS?', select=True),

        #
        # Campos para rateio de custo
        #
        'vr_frete_rateio': CampoDinheiro(u'Valor do frete'),
        'vr_seguro_rateio': CampoDinheiro(u'Valor do seguro'),
        'vr_outras_rateio': CampoDinheiro(u'Outras despesas acessórias'),
        'vr_desconto_rateio': CampoDinheiro(u'Valor do desconto'),
        'vr_unitario_custo': CampoDinheiro(u'Custo unitário'),
        'vr_custo': CampoDinheiro(u'Custo'),

        #
        # Parâmetros relativos ao ICMS ST compra
        # na origem
        #
        'forca_recalculo_st_compra': fields.boolean(u'Força recálculo do ST na compra?'),
        'md_icms_st_compra': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo'),
        'pr_icms_st_compra': CampoQuantidade(u'Parâmetro da base de cáculo'),
        'rd_icms_st_compra': CampoPorcentagem(u'% de redução da base de cálculo do ICMS compra'),
        'bc_icms_st_compra': CampoDinheiro(u'Base do ICMS ST compra'),
        'al_icms_st_compra': CampoPorcentagem(u'Alíquota do ICMS ST compra'),
        'vr_icms_st_compra': CampoDinheiro(u'Valor do ICMS ST compra'),
        'calcula_diferencial_aliquota': fields.boolean(u'Calcula diferencial de alíquota?'),
        'al_diferencial_aliquota': CampoPorcentagem(u'Alíquota diferencial'),
        'vr_diferencial_aliquota': CampoDinheiro(u'Valor do diferencial de alíquota'),
        'vr_diferencial_aliquota_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do diferencial de alíquota', store=False),

        'vr_csll': CampoDinheiro(u'Valor da CSLL'),
        'vr_csll_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor da CSLL', store=False),
        'vr_irrf': CampoDinheiro(u'Valor do IRPJ'),
        'vr_irrf_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor do IRPJ', store=False),
        #'vr_previdencia': CampoDinheiro(u'Base do INSS'),
        #'vr_iss_retido': CampoDinheiro(u'Valor do ISS'),
        'total_imposto': CampoDinheiro(u'Total dos impostos'),
        'total_imposto_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Total dos impostos', store=False),
        'porcentagem_imposto': fields.float(u'Porcentagem dos impostos', digits=(30,20)),
        'proporcao_imposto': fields.float(u'Proporção dos impostos', digits=(30,20)),
        'vr_unitario_venda_impostos': CampoDinheiro(u'Unitário venda'),
        'vr_unitario_venda_impostos_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Unitário venda', store=False),
        'vr_total_venda_impostos': CampoDinheiro(u'Valor venda'),
        'vr_total_venda_impostos_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Valor venda', store=False),
        'vr_taxa_juros': fields.float(u'Taxa de Juros %'),

        'falha_configuracao': fields.text(u'Inconsistência na configuração fiscal'),
        'valor_divergente': fields.boolean(u'Valor divergente?'),

        'vr_comissao': CampoDinheiro(u'Comissão'),
        'vr_comissao_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Comissão', store=False),
        'vr_margem_contribuicao': CampoDinheiro(u'Margem de contribuição'),
        'vr_margem_contribuicao_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Margem de contribuição', store=False),
        'al_margem_contribuicao': CampoPorcentagem(u'Margem de contribuição'),
        'al_margem_contribuicao_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Margem de contribuição', store=False),

        'abaixo_minimo': fields.boolean(u'Preço abaixo do mínimo?'),
        'mensagem_minimo': fields.char(u'Mensagem preço mínimo', size=255),
    }

    _defaults = {
        #
        # Campos replicados do documento, para o cálculo na emissão própria
        #
        # 'company_id': _get_company_id_padrao,
        #'regime_tributario': _get_regime_tributario_padrao,
        # 'emissao': _get_emissao_padrao,
        # 'operacao_id': _get_operacao_id_padrao,
        # 'participante_id': _get_participante_id_padrao,
        # 'data_emissao': _get_data_emissao_padrao,
        'valor_divergente': False,

        'compoe_total': True,
        'movimentacao_fisica': True,

        # Dados do produto/serviço
        # 'produto': fields.many2one('sped.participante', u'Participante', required=True),
        'quantidade': D('0'),
        # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
        'vr_unitario': D('0'),

        # Quantidade de tributação
        'quantidade_tributacao': D('0'),
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': D('0'),

        # Valor total dos produtos
        'vr_produtos': D('0'),

        # Outros valores acessórios
        'vr_frete': D('0'),
        'vr_seguro': D('0'),
        'vr_desconto': D('0'),
        'vr_outras': D('0'),

        #
        # ICMS próprio
        #
        'org_icms': ORIGEM_MERCADORIA_NACIONAL,
        'cst_icms': ST_ICMS_ISENTA,
        'partilha': False,
        'al_bc_icms_proprio_partilha': D('0'),
        # 'uf_partilha': ,
        'repasse': False,
        'md_icms_proprio': MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO,
        'pr_icms_proprio': D('0'),
        'rd_icms_proprio': D('0'),
        'bc_icms_proprio_com_ipi': False,
        'bc_icms_proprio': D('0'),
        'al_icms_proprio': D('0'),
        'vr_icms_proprio': D('0'),

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': ST_ICMS_SN_NAO_TRIBUTADA,
        'al_icms_sn': D('0'),
        'rd_icms_sn': D('0'),
        'vr_icms_sn': D('0'),

        #
        # ICMS ST
        #
        'md_icms_st': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms_st': D('0'),
        'rd_icms_st': D('0'),
        'bc_icms_st_com_ipi': False,
        'bc_icms_st': D('0'),
        'al_icms_st': D('0'),
        'vr_icms_st': D('0'),

        #
        # Parâmetros relativos ao ICMS retido anteriosvente por substituição tributária
        # na origem
        #
        'md_icms_st_retido': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms_st_retido': D('0'),
        'rd_icms_st_retido': D('0'),
        'bc_icms_st_retido': D('0'),
        'al_icms_st_retido': D('0'),
        'vr_icms_st_retido': D('0'),

        #
        # IPI padrão
        #
        'apuracao_ipi': APURACAO_IPI_MENSAL,
        'cst_ipi': ST_IPI_SAIDA_NAO_TRIBUTADA,
        'md_ipi': MODALIDADE_BASE_IPI_ALIQUOTA,
        'bc_ipi': D('0'),
        'al_ipi': D('0'),
        'vr_ipi': D('0'),

        #
        # Imposto de importação
        #
        'bc_ii': D('0'),
        'vr_despesas_aduaneiras': D('0'),
        'vr_ii': D('0'),
        'vr_iof': D('0'),

        #
        # PIS próprio
        #
        'cst_pis': ST_PIS_SEM_INCIDENCIA,
        'md_pis_proprio': MODALIDADE_BASE_PIS_ALIQUOTA,
        'bc_pis_proprio': D('0'),
        'al_pis_proprio': D('0'),
        'vr_pis_proprio': D('0'),

        #
        # PIS ST
        #
        'md_pis_st': MODALIDADE_BASE_PIS_ALIQUOTA,
        'bc_pis_st': D('0'),
        'al_pis_st': D('0'),
        'vr_pis_st': D('0'),

        #
        # COFINS própria
        #
        'cst_cofins': ST_COFINS_SEM_INCIDENCIA,
        'md_cofins_proprio': MODALIDADE_BASE_COFINS_ALIQUOTA,
        'bc_cofins_proprio': D('0'),
        'al_cofins_proprio': D('0'),
        'vr_cofins_proprio': D('0'),

        #
        # COFINS ST
        #
        'md_cofins_st': MODALIDADE_BASE_COFINS_ALIQUOTA,
        'bc_cofins_st': D('0'),
        'al_cofins_st': D('0'),
        'vr_cofins_st': D('0'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': D('0'),

        # ISS
        # 'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS'),
        'bc_iss': D('0'),
        'al_iss': D('0'),
        'vr_iss': D('0'),

        # PIS e COFINS
        'vr_pis_servico': D('0'),
        'vr_cofins_servico': D('0'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': D('0'),
        'vr_fatura': D('0'),

        # Informações adicionais
        'infcomplementar': u'',

        #
        # Dados especiais para troca de informações entre empresas
        #
        'numero_pedido': u'',
        'numero_item_pedido': D('0'),

        'produto_codigo': u'',
        'produto_descricao': u'',
        'produto_ncm': u'',
        'produto_codigo_barras': u'',
        'unidade': u'',
        'unidade_tributacao': u'',
        'fator_quantidade': 1,
        'quantidade_original': D('0'),
        'quantidade_estoque': D('0'),
        'cfop_original_id': False,

        'credita_icms_proprio': False,
        'credita_icms_st': False,
        'informa_icms_st': False,
        'credita_ipi': False,
        'credita_pis_cofins': False,

        'vr_frete_rateio': D('0'),
        'vr_seguro_rateio': D('0'),
        'vr_desconto_rateio': D('0'),
        'vr_outras_rateio': D('0'),
        'vr_unitario_custo': D('0'),
        'vr_custo': D('0'),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        res = {'value': {}}

        if 'price_unit' not in context:
            res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        readonlys = {}
        for campo in res['value']:
            if '_readonly' in campo:
                continue
            readonlys[campo + '_readonly'] = res['value'][campo]
        res['value'].update(readonlys)

        if not isinstance(res, dict):
            return res

        if not context:
            return res

        if not product_id:
            return res

        valores = res['value']

        #if 'price_unit_original' in valores and 'price_unit' in valores and valores['price_unit_original']:
            #price_unit_teste = D(valores['price_unit'] or 0).quantize(D('0.01'))
            #price_unit_original_teste = D(valores['price_unit_original'] or 0).quantize(D('0.01'))
            #if (not price_unit_teste) or (price_unit_teste < price_unit_original_teste):
                #raise osv.except_osv(u'Aviso!', u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit_teste), preco_estabelecido=formata_valor(price_unit_original_teste)))

        #elif 'price_unit_original' in context and 'price_unit' in context and context['price_unit_original']:
            #price_unit_teste = D(context['price_unit'] or 0).quantize(D('0.01'))
            #price_unit_original_teste = D(context['price_unit_original'] or 0).quantize(D('0.01'))
            #if (not price_unit_teste) or (price_unit_teste < price_unit_original_teste):
                #raise osv.except_osv(u'Aviso!', u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit_teste), preco_estabelecido=formata_valor(price_unit_original_teste)))

        produto_pool = self.pool.get('product.product')
        documento_pool = self.pool.get('sped.documento')
        documento_item_pool = self.pool.get('sped.documentoitem')

        nota_obj = DicionarioBrasil()
        #nota_obj.update(documento_pool._defaults)
        nota_obj.update({
            'emissao': '0',
            'data_emissao': str(hoje()),
            'company_id': context['company_id'],
            'partner_id': partner_id,
            'entrada_saida': '1',
        })

        produto_obj = produto_pool.browse(cr, uid, product_id)

        if produto_obj.type != 'service':
            nota_obj['operacao_id'] = context['operacao_fiscal_produto_id']
            nota_obj['modelo'] = '55'
        else:
            nota_obj['operacao_id'] = context['operacao_fiscal_servico_id']
            nota_obj['modelo'] = 'SE'

        #print('nota_obj')
        #print(produto_obj.type)
        #print(dict(nota_obj))
        dados_operacao = documento_pool.onchange_operacao(cr, uid, False, nota_obj.operacao_id)
        nota_obj.update(dados_operacao['value'])

        contexto_item = copy(nota_obj)
        contexto_item['sale_order_line'] = ids

        for chave in nota_obj:
            if 'default_' not in chave:
                contexto_item['default_' + chave] = contexto_item[chave]

        contexto_item['entrada_saida'] = nota_obj.entrada_saida

        if hasattr(nota_obj, 'regime_tributario'):
            contexto_item['regime_tributario'] = nota_obj.regime_tributario
        else:
            contexto_item['regime_tributario'] = '3'

        contexto_item['emissao'] = nota_obj.emissao
        contexto_item['data_emissao'] = nota_obj.data_emissao
        contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
        contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
        contexto_item['default_emissao'] = nota_obj.emissao
        contexto_item['default_data_emissao'] = nota_obj.data_emissao

        if 'price_unit' in context:
            price_unit = D(context.get('price_unit', 0))
            vr_unitario = D(context.get('price_unit', 0))
        else:
            price_unit = D(valores.get('price_unit', 0))
            vr_unitario = D(valores.get('price_unit', 0))

        quantidade = D(qty or 1)
        vr_desconto = D(0)
        vr_frete = D(0)
        vr_outras = D(0)

        if 'vr_desconto' in context:
            vr_desconto = D(context['vr_desconto'] or 0)

        if 'vr_frete' in context:
            vr_frete = D(context['vr_frete'] or 0)

        if 'vr_outras' in context:
            vr_outras = D(context['vr_outras'] or 0)

        item_obj = DicionarioBrasil()
        item_obj.update(valores)
        item_obj.update(documento_item_pool._defaults)
        item_obj.update(contexto_item)

        item_obj.update({
            'documento_id': nota_obj,
            'produto_id': produto_obj.id,
            'quantidade': quantidade,
            'quantidade_tributacao': quantidade,
            'vr_unitario': vr_unitario.quantize(D('0.0001')),
            'vr_unitario_tributacao': vr_unitario.quantize(D('0.0001')),
            'modelo': nota_obj.modelo,
            'vr_produtos': D(0),
            'vr_produtos_tributacao': D(0),
            'vr_operacao': D(0),
            'vr_operacao_tributacao': D(0),
            'bc_previdencia': D(0),
            'vr_previdencia': D(0),
        })

        item_obj['uf_partilha_id'] = False
        item_obj['vr_ibpt'] = D(0)

        for chave in item_obj:
            if 'default_' in chave and chave.replace('default_', '') not in item_obj:
                item_obj[chave.replace('default_')] = item_obj[chave]

        dados_item = documento_item_pool.onchange_produto(cr, uid, False, produto_obj.id, context=contexto_item)

        if not 'value' in dados_item:
            raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % produto_obj.name)

        item_obj.update(dados_item['value'])
        item_obj['vr_desconto'] = vr_desconto
        item_obj['vr_frete'] = vr_frete
        item_obj['vr_outras'] = vr_outras

        dados_item = documento_item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
        item_obj.update(dados_item['value'])

        #
        # Calcula os valores originais para apuração da margem de contribuição
        #
        price_unit_original = D(0)
        if 'price_unit_original' in valores:
            price_unit_original = D(valores['price_unit_original'] or 0)
        elif 'price_unit_original' in context:
            price_unit_original = D(context['price_unit_original'] or 0)

        vr_produto_original = D(item_obj.quantidade or 0) * price_unit_original
        vr_produto_original = vr_produto_original.quantize(D('0.01'))
        item_obj['vr_produto_original'] = vr_produto_original

        vr_unitario_base = D(0)
        if 'vr_unitario_base' in valores:
            vr_unitario_base = D(valores['vr_unitario_base'] or 0)
        elif 'vr_unitario_base' in context:
            vr_unitario_base = D(context['vr_unitario_base'] or 0)

        vr_produto_base = D(item_obj.quantidade or 0) * vr_unitario_base
        vr_produto_base = vr_produto_base.quantize(D('0.01'))
        item_obj['vr_produto_base'] = vr_produto_base

        vr_irrf = D('0')
        vr_csll = D('0')

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
        total_impostos += dados_item['value']['vr_diferencial_aliquota'] or D('0')
        total_impostos += dados_item['value']['vr_simples'] or D('0')

        if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
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

        pricelist_obj = self.pool.get('product.pricelist').browse(cr, uid, pricelist)
        if not getattr(pricelist_obj, 'ignora_impostos', False):
            try:
                proporcao_impostos = total_impostos / (price_unit * quantidade)
            except:
                proporcao_impostos = D(0)
        else:
            proporcao_impostos = D(0)

        proporcao_impostos = proporcao_impostos.quantize(D('0.0001'))
        vr_unitario_venda = price_unit / (D(1) - proporcao_impostos)
        vr_unitario_venda = vr_unitario_venda.quantize(D('0.0001'))
        vr_total_venda = vr_unitario_venda * quantidade
        vr_total_venda = vr_total_venda.quantize(D('0.01'))
        price_subtotal = price_unit * quantidade
        price_subtotal = price_subtotal.quantize(D('01'))

        item_obj['price_unit'] = price_unit
        item_obj['vr_unitario_venda'] = price_unit
        item_obj['price_subtotal'] = price_subtotal
        item_obj['vr_total_venda'] = vr_total_venda
        item_obj['vr_irrf'] = vr_irrf
        item_obj['vr_csll'] = vr_csll
        item_obj['vr_unitario_venda_impostos'] = vr_unitario_venda
        item_obj['porcentagem_imposto'] = proporcao_impostos * D(100)
        item_obj['proporcao_imposto'] = (D(1) - proporcao_impostos) * D(100)
        item_obj['vr_total_venda_impostos'] = vr_unitario_venda * quantidade
        item_obj['vr_total_venda_impostos'] = item_obj['vr_total_venda_impostos'].quantize(D('0.01'))
        item_obj['vr_total_venda_impostos'] += vr_frete + vr_outras
        item_obj['falha_configuracao'] = False
        item_obj['total_imposto'] = total_impostos

        #
        # Agora, injeta a proporção dos impostos nos próprios impostos já calculados
        #
        item_obj['vr_simples'] /= (D(1) - proporcao_impostos)
        item_obj['vr_produtos'] /= (D(1) - proporcao_impostos)
        item_obj['vr_icms_proprio'] /= (D(1) - proporcao_impostos)
        item_obj['vr_diferencial_aliquota'] /= (D(1) - proporcao_impostos)
        item_obj['vr_icms_st'] /= (D(1) - proporcao_impostos)
        item_obj['vr_icms_sn'] /= (D(1) - proporcao_impostos)
        item_obj['vr_pis_proprio'] /= (D(1) - proporcao_impostos)
        item_obj['vr_cofins_proprio'] /= (D(1) - proporcao_impostos)
        item_obj['vr_irrf'] /= (D(1) - proporcao_impostos)
        item_obj['vr_csll'] /= (D(1) - proporcao_impostos)
        item_obj['total_imposto'] /= (D(1) - proporcao_impostos)

        #del item_obj['documento_id']

        #
        # Cálculo da margem de contribuição
        #
        vr_margem_contribuicao = 0
        al_margem_contribuicao = 0

        if 'vr_produtos' in item_obj and item_obj['vr_produtos'] and 'vr_produto_base' in item_obj:
            vr_margem_contribuicao = item_obj['vr_produtos']
            vr_margem_contribuicao -= item_obj['total_imposto']
            #vr_margem_contribuicao -= item_obj['vr_comissao']
            vr_margem_contribuicao -= item_obj['vr_produto_base']

            al_margem_contribuicao = vr_margem_contribuicao / item_obj['vr_produtos']
            al_margem_contribuicao *= 100

        item_obj['vr_margem_contribuicao'] = vr_margem_contribuicao
        item_obj['al_margem_contribuicao'] = al_margem_contribuicao

        res['value'] = item_obj
        res['value']['product_uom_qty'] = qty
        #print('quantidade que está voltando e a que veio')
        #print(res['value'], qty)

        #
        # Verifica o desconto máximo permitido
        #
        if hasattr(pricelist_obj, 'desconto_maximo') and 'valida_desconto_maximo' in context:
            vr_desconto_maximo = vr_produto_original * D(pricelist_obj.desconto_maximo or 0) / 100
            vr_desconto_maximo = vr_desconto_maximo.quantize(D('0.01'))
            vr_com_desconto = vr_produto_original - vr_desconto_maximo
            vr_minimo = vr_com_desconto / quantidade
            vr_minimo = vr_minimo.quantize(D('0.01'))


            if vr_minimo > vr_unitario_venda:
                res['value']['abaixo_minimo'] = True
                res['value']['mensagem_minimo'] = u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit), preco_estabelecido=formata_valor(vr_minimo))
                res['value']['mensagem_minimo_readonly'] = u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit), preco_estabelecido=formata_valor(vr_minimo))

            else:
                res['value']['abaixo_minimo'] = False
                res['value']['mensagem_minimo'] = u''
                res['value']['mensagem_minimo_readonly'] = u''

        readonlys = {}
        for campo in res['value']:
            if '_readonly' in campo:
                continue
            readonlys[campo + '_readonly'] = res['value'][campo]
        res['value'].update(readonlys)

        return res

    def create(self, cr, uid, dados, context={}):
        #if 'price_unit_original' in dados and 'price_unit' in dados and dados['price_unit_original']:
            #price_unit = D(dados['price_unit'] or 0).quantize(D('0.01'))
            #price_unit_original = D(dados['price_unit_original'] or 0).quantize(D('0.01'))
            #if (not price_unit) or (price_unit < price_unit_original):
                #raise osv.except_osv(u'Aviso!', u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit), preco_estabelecido=formata_valor(price_unit_original)))

        return super(sale_order_line, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'uom_id' in dados:
            del dados['uom_id']
        #if 'price_unit' in dados or 'price_unit_original' in dados:
            #for item_obj in self.browse(cr, uid, ids, context=context):
                #if 'price_unit_original' in dados:
                    #price_unit_original = dados['price_unit_original']
                #else:
                    #price_unit_original = item_obj.price_unit_original

                #if 'price_unit' in dados:
                    #price_unit = dados['price_unit']
                #else:
                    #price_unit = item_obj.price_unit

                #price_unit = D(price_unit or 0).quantize(D('0.01'))
                #price_unit_original = D(price_unit_original or 0).quantize(D('0.01'))
                #print(price_unit, price_unit_original)

                #if (not price_unit) or (price_unit < price_unit_original):
                    #raise osv.except_osv(u'Aviso!', u'O preço informado de R$ {preco_informado} é menor do que o mínimo estabelecido, que é de R$ {preco_estabelecido}'.format(preco_informado=formata_valor(price_unit), preco_estabelecido=formata_valor(price_unit_original)))

        return super(sale_order_line, self).write(cr, uid, ids, dados, context=context)


sale_order_line()
