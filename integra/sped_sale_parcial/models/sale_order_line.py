# -*- encoding: utf-8 -*-


from datetime import datetime
from decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID
from tools.translate import _
from sped.models.fields import *
from sped.constante_tributaria import *


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

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', required=False, ondelete='set null', select=True),
        'company_id': fields.related('documento_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=True, select=True),
        'regime_tributario': fields.related('documento_id', 'regime_tributario', type='char', string=u'Regime tributário', store=True, select=True),
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
        'uom_id': fields.related('produto_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', select=True),
        'quantidade': CampoQuantidade(u'Quantidade'),
        # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
        'vr_unitario': CampoValorUnitario(u'Valor unitário'),

        # Quantidade de tributação
        'quantidade_tributacao': CampoQuantidade(u'Quantidade para tributação'),
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': CampoValorUnitario(u'Valor unitário para tributação'),

        # Valor total dos produtos
        'vr_produtos': CampoDinheiro(u'Valor do produto/serviço'),
        'vr_produtos_tributacao': CampoDinheiro(u'Valor do produto/serviço para tributação'),

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

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': fields.selection(ST_ICMS_SN, u'Situação tributária do ICMS - Simples Nacional', select=True),
        'al_icms_sn': CampoPorcentagem(u'Alíquota do crédito de ICMS'),
        'rd_icms_sn': CampoPorcentagem(u'% estadual de redução da alíquota de ICMS'),
        'vr_icms_sn': CampoDinheiro(u'valor do crédito de ICMS - SIMPLES Nacional'),

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

        #
        # COFINS própria
        #
        'cst_cofins': fields.selection(ST_COFINS, u'Situação tributária da COFINS', select=True),
        'md_cofins_proprio': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS própria'),
        'bc_cofins_proprio': CampoDinheiro(u'Base do COFINS próprio'),
        'al_cofins_proprio': CampoQuantidade(u'Alíquota da COFINS própria'),
        'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS próprio'),

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

        'vr_csll': CampoDinheiro(u'Valor da CSLL'),
        'vr_irrf': CampoDinheiro(u'Valor do IRRF'),
        #'vr_previdencia': CampoDinheiro(u'Base do INSS'),
        #'vr_iss_retido': CampoDinheiro(u'Valor do ISS'),
        'total_imposto': CampoDinheiro(u'Total dos impostos'),
        'porcentagem_imposto': CampoPorcentagem(u'Porcentagem dos impostos'),
        'proporcao_imposto': CampoPorcentagem(u'Proporção dos impostos'),
        'vr_unitario_venda_impostos': fields.float(u'Unitário venda'),
        'vr_total_venda_impostos': fields.float(u'Valor venda'),
        'vr_taxa_juros': fields.float(u'Taxa de Juros %'),

        'falha_configuracao': fields.text(u'Inconsistência na configuração fiscal'),
        'valor_divergente': fields.boolean(u'Valor divergente?'),
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


sale_order_line()
