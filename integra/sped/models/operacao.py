 #voip.agiltec.info-*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from fields import CampoPorcentagem, CampoDinheiro


class sped_operacao(osv.Model):
    _description = u'Operações fiscais'
    _name = 'sped.operacao'

    def _get_regime_tributario_padrao(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.operacao', context=context)
        company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        return company.regime_tributario or REGIME_TRIBUTARIO_SIMPLES

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict', select=True),
        'codigo': fields.char(u'Código', size=10, required=True, select=True),
        'nome': fields.char('Nome', size=60, required=True, select=True),
        'serie': fields.char('Série', size=3 ),
        'modelo': fields.selection(MODELO_FISCAL, u'Modelo', required=True, select=True),
        'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão', select=True),
        'entrada_saida': fields.selection(ENTRADA_SAIDA, u'Entrada/saída', required=True, select=True),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário', required=True, select=True),
        'forma_pagamento': fields.selection(FORMA_PAGAMENTO, u'Forma de pagamento'),
        'finalidade_nfe': fields.selection(FINALIDADE_NFE, u'Finalidade da NF-e'),
        'modalidade_frete': fields.selection(MODALIDADE_FRETE, u'Modalidade do frete'),
        'naturezaoperacao_id': fields.many2one('sped.naturezaoperacao', u'Natureza da operação', ondelete='restrict', select=True),
        'infadfisco': fields.text(u'Informações adicionais de interesse do fisco'),
        'infcomplementar': fields.text(u'Informações complementares'),
        'operacaoitem_ids': fields.one2many('sped.operacaoitem', 'operacao_id', u'Ítens da operação'),
        'operacaoitem_simples_ids': fields.one2many('sped.operacaoitem', 'operacao_id', u'Ítens da operação'),
        'operacaoitem_normal_ids': fields.one2many('sped.operacaoitem', 'operacao_id', u'Ítens da operação'),
        'operacaoitem_servico_ids': fields.one2many('sped.operacaoitem', 'operacao_id', u'Ítens da operação'),
        'cnae_id': fields.many2one('sped.cnae', u'CNAE'),
        'natureza_tributacao_nfse': fields.selection(NATUREZA_TRIBUTACAO_NFSE, u'Natureza da tributação'),
        'servico_id': fields.many2one('sped.servico', u'Serviço', select=True),
        'deduz_retencao': fields.boolean(u'Deduz retenção do total da NF?'),
        'pis_cofins_retido': fields.boolean(u'PIS-COFINS retidos?'),
        'al_pis_retido': CampoPorcentagem(u'Alíquota do PIS'),
        'al_cofins_retido': CampoPorcentagem(u'Alíquota da COFINS'),
        'csll_retido': fields.boolean(u'CSLL retido?'),
        'al_csll': CampoPorcentagem(u'Alíquota da CSLL'),
        'irrf_retido': fields.boolean(u'IR retido?'),
        'irrf_retido_ignora_limite': fields.boolean(u'IR retido ignora limite de R$ 10,00?'),
        'al_irrf': CampoPorcentagem(u'Alíquota do IR'),
        'previdencia_retido': fields.boolean(u'INSS retido?'),
        'prioriza_familia_ncm': fields.boolean(u'Prioriza família tributária por NCM?'),
        #'al_previdencia': CampoPorcentagem(u'Alíquota do INSS'),
        'limite_retencao_pis_cofins_csll': CampoDinheiro(u'Obedecer limite de faturamento para retenção de'),
        'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS'),
        'user_ids': fields.many2many('res.users', 'sped_operacao_usuario', 'sped_operacao_id', 'res_user_id', u'Usuários permitidos'),
        'company_ids': fields.many2many('res.company', 'sped_operacao_company', 'sped_operacao_id', 'company_id', u'Empresas permitidas'),
        'forca_recalculo_st_compra': fields.boolean(u'Força recálculo do ST na compra?'),
        'calcula_diferencial_aliquota': fields.boolean(u'Calcula diferencial de alíquota?'),
        'operacao_entrada_id': fields.many2one('sped.operacao', u'Operação de entrada equivalente'),
    }

    _rec_name = 'nome'
    _order = 'nome'

    _sql_constraints = [
        ('codigo_unique', 'unique (codigo)', u'O código não pode se repetir!'),
        ('nome_unique', 'unique (nome)', u'O nome não pode se repetir!'),
    ]

    _defaults = {
        #
        # Empresa emissora ou recebedora do documento
        #
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=c),
        'modelo': MODELO_FISCAL_NFE,
        'entrada_saida': ENTRADA_SAIDA_SAIDA,
        'regime_tributario': _get_regime_tributario_padrao,
        'forma_pagamento': FORMA_PAGAMENTO_A_VISTA,
        'finalidade_nfe': FINALIDADE_NFE_NORMAL,
        'modalidade_frete': MODALIDADE_FRETE_EMITENTE,
        'natureza_tributacao_nfse': NAT_OP_TRIBUTADA_NO_MUNICIPIO,
        'deduz_retencao': True,
        'pis_cofins_retido': False,
        'al_pis_retido': 0.65,
        'al_cofins_retido': 3,
        'csll_retido': False,
        'al_csll': 1,
        'irrf_retido': False,
        'al_irrf': 1,
        'previdencia_retido': False,
        #'al_previdencia': 0,
        'limite_retencao_pis_cofins_csll': 5000,
        'cst_iss': '',
        'emissao': '0',
        'irrf_retido_ignora_limite': False,
        'forca_recalculo_st_compra': False,
        'calcula_diferencial_aliquota': False,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        default.update({
            'codigo': '',
            'nome': '',
        })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res


sped_operacao()


class res_users(osv.Model):
    _inherit = 'res.users'

    _columns = {
        'sped_operacao_ids': fields.many2many('sped.operacao', 'sped_operacao_usuario', 'res_user_id', 'sped_operacao_id', u'Operações Fiscais permitidas'),
    }


res_users()


class res_company(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'sped_operacao_ids': fields.many2many('sped.operacao', 'sped_operacao_company', 'company_id', 'sped_operacao_id', u'Operações Fiscais permitidas'),
    }


res_company()


class sped_operacaoitem(osv.Model):
    _description = u'Item da operação fiscal'
    _name = 'sped.operacaoitem'
    _columns = {
        'operacao_id': fields.many2one('sped.operacao', u'Operação', required=True, ondelete='cascade', select=True),
        'regime_tributario': fields.related('operacao_id', 'regime_tributario', type='char', string=u'Regime tributário'),
        'entrada_saida': fields.related('operacao_id', 'entrada_saida', type='char', string=u'Entrada/Saída'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família Tributária', required=False, ondelete='restrict', select=True),
        'cfop_id': fields.many2one('sped.cfop', u'CFOP', required=True, ondelete='restrict', select=True),
        'compoe_total': fields.boolean(u'Compõe o valor total da NF-e?'),
        'movimentacao_fisica': fields.boolean(u'Há movimentação física do produto?'),
        'bc_icms_proprio_com_ipi': fields.boolean('IPI integra a base do ICMS próprio?'),
        'bc_icms_st_com_ipi': fields.boolean(u'IPI integra a base do ICMS ST?'),
        'contribuinte': fields.selection(IE_DESTINATARIO, u'Contribuinte', select=True),
        'org_icms': fields.selection(ORIGEM_MERCADORIA, u'Origem da mercadoria', select=True),
        'cst_icms': fields.selection(ST_ICMS, u'Situação tributária do ICMS'),
        'cst_icms_sn': fields.selection(ST_ICMS_SN, u'Situação tributária do ICMS - Simples Nacional'),
        'cst_ipi': fields.selection(ST_IPI, u'Situação tributária do IPI'),
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota e CST do PIS-COFINS'),
        #'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS'),
        'cst_iss': fields.related('operacao_id', 'cst_iss', type='char', string=u'Situação tributária do ISS'),
        'familiatributaria_alternativa_id': fields.many2one('sped.familiatributaria', u'Família Tributária alternativa'),
        #'pis_retido': fields.boolean(u'PIS retido?'),
        #'al_pis_retido': CampoPorcentagem('Alíquota do PIS'),
        #'cofins_retido': fields.boolean(u'COFINS retido?'),
        #'al_cofins_retido': CampoPorcentagem('Alíquota da COFINS'),
        #'csll_retido': fields.boolean(u'CSLL retido?'),
        #'al_csll': CampoPorcentagem('Alíquota da CSLL'),
        #'irrf_retido': fields.boolean(u'IR retido?'),
        #'al_irrf': CampoPorcentagem(u'Alíquota do IR'),
        #'previdencia_retido': fields.boolean(u'INSS retido?'),
        #'al_previdencia': CampoPorcentagem(u'Alíquota do INSS'),
        #'iss_retido': fields.boolean(u'ISS retido?'),
        #'item_descontado': fields.boolean(u'Item descontado?'),
        'previdencia_retido': fields.related('operacao_id', 'previdencia_retido', type='boolean', string=u'ISS retido?'),
        'al_previdencia': fields.related('familiatributaria_id', 'al_previdencia', type='float', string=u'Alíquota do INSS'),
    }

    _rec_name = 'operacao_id'
    #_order = 'descricao'

    _sql_constraints = [
        ('familiatributaria_cfop', 'unique (operacao_id, familiatributaria_id, contribuinte, cfop_id)', u'O item não pode se repetir!'),
    ]

    _defaults = {
        #'contribuinte': '1',
        #'org_icms': ORIGEM_MERCADORIA_NACIONAL,
        'compoe_total': True,
        'movimentacao_fisica': True,
        'cst_icms': ST_ICMS_INTEGRAL,
        'bc_icms_proprio_com_ipi': False,
        'cst_icms_sn': ST_ICMS_SN_TRIB_SEM_CREDITO,
        'bc_icms_st_com_ipi': False,
        'cst_ipi': '',
        #'cst_iss': '',
        #'al_pis_cofins_id': False,
        #'pis_retido': False,
        #'cofins_retido': False,
        #'csll_retido': False,
        #'irrf_retido': False,
        'previdencia_retido': False,
        'al_previdencia': 0,
        #'iss_retido': False,
    }


sped_operacaoitem()
