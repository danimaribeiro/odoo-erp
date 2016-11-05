# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from sped.constante_tributaria import (REGIME_TRIBUTARIO_SIMPLES, ST_IPI_CALCULA, MODALIDADE_BASE_IPI_ALIQUOTA, ST_ICMS_SN_CALCULA_CREDITO, ST_ICMS_SN_ANTERIOR, ST_ICMS_SN_CALCULA_ST, MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO, ST_ICMS_CALCULA_PROPRIO, MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO, MODALIDADE_BASE_ICMS_PROPRIO_PAUTA, MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO, ST_ICMS_COM_REDUCAO, MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO, ST_ICMS_ZERA_ICMS_PROPRIO, ST_ICMS_CALCULA_ST, ST_ICMS_ANTERIOR, ST_PIS_CALCULA, ST_PIS_CALCULA_ALIQUOTA, MODALIDADE_BASE_PIS_ALIQUOTA, MODALIDADE_BASE_PIS_QUANTIDADE, ST_ISS_ISENTO, ST_PIS_CALCULA_CREDITO, ST_ICMS_SN_CALCULA_PROPRIO)


CFOP_ID_DEVOLUCAO = [283, 284, 288, 289, 290, 321, 322, 323, 324, 330, 335, 337, 338, 354, 355, 356, 379, 380, 382, 430, 425, 426, 431, 432, 463, 464, 465, 471, 476, 478, 479, 491, 492, 493, 516, 517, 519, 535, 536, 540, 541, 547, 548, 552, 466]

class ITEM_OBJ(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self


def calcula_item(self, cr, uid, item_obj):
    if isinstance(item_obj, dict):
        item_dict = ITEM_OBJ()
        item_dict.update(item_obj)

    else:
        item_dict = ITEM_OBJ()
        item_dict.update({
            'regime_tributario': item_obj.regime_tributario,
            'emissao': item_obj.emissao,
            'operacao_id': item_obj.operacao_id,
            'partner_id': item_obj.partner_id,
            'data_emissao': item_obj.data_emissao,
            'modelo': item_obj.modelo,
            'cfop_id': item_obj.cfop_id,
            'compoe_total': item_obj.compoe_total,
            'movimentacao_fisica': item_obj.movimentacao_fisica,
            'produto_id': item_obj.produto_id,
            'quantidade': item_obj.quantidade,
            'vr_unitario': item_obj.vr_unitario,
            'quantidade_tributacao': item_obj.quantidade_tributacao,
            'vr_unitario_tributacao': item_obj.vr_unitario_tributacao,
            'vr_produtos': item_obj.vr_produtos,
            'vr_produtos_tributacao': item_obj.vr_produtos_tributacao,
            'vr_frete': item_obj.vr_frete,
            'vr_seguro': item_obj.vr_seguro,
            'vr_desconto': item_obj.vr_desconto,
            'vr_outras': item_obj.vr_outras,
            'vr_operacao': item_obj.vr_operacao,
            'vr_operacao_tributacao': item_obj.vr_operacao_tributacao,
            'contribuinte': item_obj.contribuinte,
            'org_icms': item_obj.org_icms,
            'cst_icms': item_obj.cst_icms,
            'partilha': item_obj.partilha,
            'al_bc_icms_proprio_partilha': item_obj.al_bc_icms_proprio_partilha,
            'uf_partilha_id': item_obj.uf_partilha_id,
            'repasse': item_obj.repasse,
            'md_icms_proprio': item_obj.md_icms_proprio,
            'pr_icms_proprio': item_obj.pr_icms_proprio,
            'rd_icms_proprio': item_obj.rd_icms_proprio,
            'bc_icms_proprio_com_ipi': item_obj.bc_icms_proprio_com_ipi,
            'bc_icms_proprio': item_obj.bc_icms_proprio,
            'al_icms_proprio': item_obj.al_icms_proprio,
            'vr_icms_proprio': item_obj.vr_icms_proprio,
            'cst_icms_sn': item_obj.cst_icms_sn,
            'al_icms_sn': item_obj.al_icms_sn,
            'rd_icms_sn': item_obj.rd_icms_sn,
            'vr_icms_sn': item_obj.vr_icms_sn,
            'al_simples': item_obj.al_simples,
            'vr_simples': item_obj.vr_simples,
            'md_icms_st': item_obj.md_icms_st,
            'pr_icms_st': item_obj.pr_icms_st,
            'rd_icms_st': item_obj.rd_icms_st,
            'bc_icms_st_com_ipi': item_obj.bc_icms_st_com_ipi,
            'bc_icms_st': item_obj.bc_icms_st,
            'al_icms_st': item_obj.al_icms_st,
            'vr_icms_st': item_obj.vr_icms_st,
            'md_icms_st_retido': item_obj.md_icms_st_retido,
            'pr_icms_st_retido': item_obj.pr_icms_st_retido,
            'rd_icms_st_retido': item_obj.rd_icms_st_retido,
            'bc_icms_st_retido': item_obj.bc_icms_st_retido,
            'al_icms_st_retido': item_obj.al_icms_st_retido,
            'vr_icms_st_retido': item_obj.vr_icms_st_retido,
            'apuracao_ipi': item_obj.apuracao_ipi,
            'cst_ipi': item_obj.cst_ipi,
            'md_ipi': item_obj.md_ipi,
            'bc_ipi': item_obj.bc_ipi,
            'al_ipi': item_obj.al_ipi,
            'vr_ipi': item_obj.vr_ipi,
            'bc_ii': item_obj.bc_ii,
            'vr_despesas_aduaneiras': item_obj.vr_despesas_aduaneiras,
            'vr_ii': item_obj.vr_ii,
            'vr_iof': item_obj.vr_iof,
            'al_pis_cofins_id': item_obj.al_pis_cofins_id,
            'cst_pis': item_obj.cst_pis,
            'md_pis_proprio': item_obj.md_pis_proprio,
            'bc_pis_proprio': item_obj.bc_pis_proprio,
            'al_pis_proprio': item_obj.al_pis_proprio,
            'vr_pis_proprio': item_obj.vr_pis_proprio,
            'cst_cofins': item_obj.cst_cofins,
            'md_cofins_proprio': item_obj.md_cofins_proprio,
            'bc_cofins_proprio': item_obj.bc_cofins_proprio,
            'al_cofins_proprio': item_obj.al_cofins_proprio,
            'vr_cofins_proprio': item_obj.vr_cofins_proprio,
            'md_pis_st': item_obj.md_pis_st,
            'bc_pis_st': item_obj.bc_pis_st,
            'al_pis_st': item_obj.al_pis_st,
            'vr_pis_st': item_obj.vr_pis_st,
            'md_cofins_st': item_obj.md_cofins_st,
            'bc_cofins_st': item_obj.bc_cofins_st,
            'al_cofins_st': item_obj.al_cofins_st,
            'vr_cofins_st': item_obj.vr_cofins_st,
            'vr_servicos': item_obj.vr_servicos,
            'cst_iss': item_obj.cst_iss,
            'bc_iss': item_obj.bc_iss,
            'al_iss': item_obj.al_iss,
            'vr_iss': item_obj.vr_iss,
            'vr_pis_servico': item_obj.vr_pis_servico,
            'vr_cofins_servico': item_obj.vr_cofins_servico,
            'vr_nf': item_obj.vr_nf,
            'vr_fatura': item_obj.vr_fatura,
            'al_ibpt': item_obj.al_ibpt,
            'vr_ibpt': item_obj.vr_ibpt,
            'previdencia_retido': item_obj.previdencia_retido,
            'bc_previdencia': item_obj.bc_previdencia,
            'al_previdencia': item_obj.al_previdencia,
            'vr_previdencia': item_obj.vr_previdencia,
            'forca_recalculo_st_compra': item_obj.forca_recalculo_st_compra,
            'md_icms_st_compra': item_obj.md_icms_st_compra,
            'pr_icms_st_compra': item_obj.pr_icms_st_compra,
            'rd_icms_st_compra': item_obj.rd_icms_st_compra,
            'bc_icms_st_compra': item_obj.bc_icms_st_compra,
            'al_icms_st_compra': item_obj.al_icms_st_compra,
            'vr_icms_st_compra': item_obj.vr_icms_st_compra,
            'calcula_diferencial_aliquota': item_obj.calcula_diferencial_aliquota,
            'al_diferencial_aliquota': item_obj.al_diferencial_aliquota,
            'vr_diferencial_aliquota': item_obj.vr_diferencial_aliquota,
        })

    #
    # Emissão de cupom fiscal só aceita 3 casas decimais nos itens
    #
    if item_dict.modelo == '2D' and item_dict.emissao == '0':
        item_dict.vr_unitario = D(item_dict.vr_unitario).quantize(D('0.001'))
        item_dict.vr_unitario_tributacao = D(item_dict.vr_unitario_tributacao).quantize(D('0.001'))

    vr_operacao = calcula_valor_operacao(item_dict)
    item_dict.update(vr_operacao)

    vr_ipi = calcula_ipi(item_dict)
    item_dict.update(vr_ipi)

    vr_icms_sn = calcula_icms_sn(item_dict)
    item_dict.update(vr_icms_sn)

    vr_icms = calcula_icms_proprio(item_dict)
    item_dict.update(vr_icms)

    vr_icms_diferencial = calcula_icms_diferencial(item_dict)
    item_dict.update(vr_icms_diferencial)

    #
    # O ST de compra precisa ser calculado antes, pois usa
    # a base do próprio, que pode ser zerada no calculo do ST
    # normal
    #
    vr_icms_st_compra = calcula_icms_st_compra(item_dict)
    item_dict.update(vr_icms_st_compra)

    vr_icms_st = calcula_icms_st(item_dict)
    item_dict.update(vr_icms_st)

    vr_icms_st_retido = calcula_icms_st_retido(item_dict)
    item_dict.update(vr_icms_st_retido)

    vr_iss = calcula_iss(item_dict)
    item_dict.update(vr_iss)

    vr_pis_cofins = calcula_pis_cofins(self, cr, uid, item_dict)
    item_dict.update(vr_pis_cofins)

    vr_nf = calcula_total_nf(item_dict)
    item_dict.update(vr_nf)

    vr_ibpt = calcula_ibpt(item_dict)
    vr_previdencia = calcula_previdencia(item_dict)

    vr_simples = calcula_simples(item_dict)

    retorno = {}
    retorno.update(vr_operacao)
    retorno.update(vr_ipi)
    retorno.update(vr_icms_sn)
    retorno.update(vr_icms)
    retorno.update(vr_icms_diferencial)
    retorno.update(vr_icms_st_compra)
    retorno.update(vr_icms_st)
    retorno.update(vr_icms_st_retido)
    retorno.update(vr_iss)
    retorno.update(vr_pis_cofins)
    retorno.update(vr_nf)
    retorno.update(vr_ibpt)
    retorno.update(vr_previdencia)
    retorno.update(vr_simples)

    return retorno


def calcula_valor_operacao(item_dict):
    #
    # Converte todos os campos para Decimal
    #
    quantidade = D('%.4f' % (item_dict.quantidade or 0))
    vr_unitario = D('%.10f' % (item_dict.vr_unitario or 0))
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_unitario_tributacao = D('%.10f' % (item_dict.vr_unitario_tributacao or 0))
    vr_frete = D('%.2f' % (item_dict.vr_frete or 0))
    vr_seguro = D('%.2f' % (item_dict.vr_seguro or 0))
    vr_desconto = D('%.2f' % (item_dict.vr_desconto or 0))
    vr_outras = D('%.2f' % (item_dict.vr_outras or 0))

    #
    # Calcula o valor dos produtos
    #
    vr_produtos = quantidade * vr_unitario
    vr_produtos = vr_produtos.quantize(D('0.01'))
    quantidade_tributacao = quantidade
    vr_unitario_tributacao = vr_unitario
    vr_produtos_tributacao = quantidade_tributacao * vr_unitario_tributacao
    vr_produtos_tributacao = vr_produtos_tributacao.quantize(D('0.01'))

    vr_operacao = vr_produtos + vr_frete + vr_seguro + vr_outras - vr_desconto
    vr_operacao_tributacao = vr_produtos_tributacao + vr_frete + vr_seguro + vr_outras - vr_desconto

    retorno = {
        'quantidade': quantidade,
        'vr_unitario': vr_unitario,
        'vr_produtos': vr_produtos,
        'quantidade_tributacao': quantidade_tributacao,
        'vr_unitario_tributacao': vr_unitario_tributacao,
        'vr_produtos_tributacao': vr_produtos_tributacao,
        'vr_frete': vr_frete,
        'vr_seguro': vr_seguro,
        'vr_desconto': vr_desconto,
        'vr_outras': vr_outras,
        'vr_operacao': vr_operacao,
        'vr_operacao_tributacao': vr_operacao_tributacao,
    }

    return retorno


def calcula_ipi(item_dict):
    if item_dict is None:
        item_dict = {}

    regime_tributario = (item_dict.regime_tributario or REGIME_TRIBUTARIO_SIMPLES)
    cst_ipi = (item_dict.cst_ipi or '')
    md_ipi = (item_dict.md_ipi or MODALIDADE_BASE_IPI_ALIQUOTA)
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    al_ipi = D('%.4f' % (item_dict.al_ipi or 0))

    #
    # Primeiro, calculamos o IPI, pra depois somar na base do ICMS se for o
    # caso
    #
    bc_ipi = D('0')
    vr_ipi = D('0')

    if regime_tributario != REGIME_TRIBUTARIO_SIMPLES and cst_ipi in ST_IPI_CALCULA:
        if 'cfop' in item_dict and item_dict['cfop'] and item_dict['cfop'][0] == '3':
            bc_ipi = D('%.4f' % (item_dict.bc_ipi or 0))
            if bc_ipi == 0:
                bc_ipi = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
            vr_ipi = bc_ipi * (al_ipi / D('100.0000000000'))

        elif md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
            bc_ipi = vr_operacao_tributacao
            vr_ipi = bc_ipi * (al_ipi / D('100.0000000000'))
        else:
            vr_ipi = quantidade_tributacao * al_ipi

        bc_ipi = bc_ipi.quantize(D('0.01'))
        vr_ipi = vr_ipi.quantize(D('0.01'))

    retorno = {
        'bc_ipi': bc_ipi,
        'vr_ipi': vr_ipi,
    }

    return retorno


def calcula_icms_sn(item_dict):
    if item_dict is None:
        item_dict = {}

    regime_tributario = (item_dict.regime_tributario or REGIME_TRIBUTARIO_SIMPLES)
    cst_icms_sn = (item_dict.cst_icms_sn or '')
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    al_icms_sn = D('%.2f' % ((item_dict.al_icms_sn or 0) or 0))
    rd_icms_sn = D('%.2f' % ((item_dict.rd_icms_sn or 0) or 0))

    vr_icms_sn = D('0')

    if regime_tributario == REGIME_TRIBUTARIO_SIMPLES and cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
        bc_icms_sn = vr_operacao_tributacao

        #
        # Aplica a redução da alíquota
        #
        al_credito_sn = al_icms_sn - (al_icms_sn * rd_icms_sn / D('100.0000000000'))

        vr_icms_sn = bc_icms_sn * (al_credito_sn / D('100.0000000000'))
        vr_icms_sn = vr_icms_sn.quantize(D('0.01'))

    retorno = {
        'vr_icms_sn': vr_icms_sn,
    }

    return retorno


def calcula_icms_proprio(item_dict, forca_recalculo_st_compra=False):
    if item_dict is None:
        item_dict = {}

    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    cst_icms = (item_dict.cst_icms or '')
    cst_icms_sn = (item_dict.cst_icms_sn or '')
    md_icms_proprio = (item_dict.md_icms_proprio or MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO)
    pr_icms_proprio = D('%.4f' % (item_dict.pr_icms_proprio or 0))
    rd_icms_proprio = D('%.4f' % (item_dict.rd_icms_proprio or 0))
    al_icms_proprio = D('%.4f' % (item_dict.al_icms_proprio or 0))
    bc_icms_proprio_com_ipi = (item_dict.bc_icms_proprio_com_ipi or False)
    vr_ipi = D('%.2f' % (item_dict.vr_ipi or 0))
    vr_outras = D('%.2f' % (item_dict.vr_outras or 0))

    #
    # Agora, calculamos o ICMS próprio
    #
    bc_icms_proprio = D('0')
    vr_icms_proprio = D('0')

    #
    # Baseado no valor da situação tributária, calcular o ICMS próprio
    #
    if cst_icms in ST_ICMS_CALCULA_PROPRIO or cst_icms_sn in ST_ICMS_SN_CALCULA_ST or cst_icms_sn in ST_ICMS_SN_CALCULA_PROPRIO or cst_icms_sn == ST_ICMS_SN_ANTERIOR or forca_recalculo_st_compra:
        if  'cfop' in item_dict and item_dict['cfop'] and item_dict['cfop'][0] == '3':
            bc_icms_proprio = D('%.2f' % (item_dict.bc_icms_proprio or 0))

        elif md_icms_proprio == MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO:
            bc_icms_proprio = vr_operacao_tributacao * (1 + (pr_icms_proprio / D('100.0000000000')))

        elif md_icms_proprio in (MODALIDADE_BASE_ICMS_PROPRIO_PAUTA, MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO):
            bc_icms_proprio = quantidade_tributacao * pr_icms_proprio

        else:  # MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
            bc_icms_proprio = vr_operacao_tributacao

        #
        # Nas devoluções, o valor do IPI é informado em outras depesas acessórias;
        # nesses casos, inverter a consideração da soma do valor do IPI, pelo valor
        # das despesas acessórias
        #
        if item_dict.cfop_id in CFOP_ID_DEVOLUCAO:
            if not bc_icms_proprio_com_ipi:
                bc_icms_proprio -= vr_outras

        elif bc_icms_proprio_com_ipi:
            bc_icms_proprio += vr_ipi

        bc_icms_proprio = bc_icms_proprio.quantize(D('0.01'))

        #
        # Vai haver redução da base de cálculo?
        # Aqui também, no caso da situação 30 e 60, calculamos a redução, quando houver
        #
        if cst_icms in ST_ICMS_COM_REDUCAO or cst_icms_sn in ST_ICMS_SN_CALCULA_ST:
            bc_icms_proprio = bc_icms_proprio * (1 - (rd_icms_proprio / D('100.0000000000')))

        bc_icms_proprio = bc_icms_proprio.quantize(D('0.01'))
        vr_icms_proprio = bc_icms_proprio * (al_icms_proprio / D('100.0000000000'))
        vr_icms_proprio = vr_icms_proprio.quantize(D('0.01'))

    retorno = {
        'bc_icms_proprio': bc_icms_proprio,
        'vr_icms_proprio': vr_icms_proprio,
    }

    return retorno

def calcula_icms_diferencial(item_dict):
    if item_dict is None:
        item_dict = {}

    bc_icms_proprio = D('%.2f' % (item_dict.bc_icms_proprio or 0))
    al_diferencial_aliquota = D('%.2f' % (item_dict.al_diferencial_aliquota or 0))

    #
    # Agora, calculamos o ICMS diferencial
    #
    vr_diferencial_aliquota = D('0')

    #
    # Baseado no valor da situação tributária, calcular o ICMS próprio
    #
    if item_dict.calcula_diferencial_aliquota:
        vr_diferencial_aliquota = bc_icms_proprio
        vr_diferencial_aliquota *= al_diferencial_aliquota / D('100.0000000000')
        vr_diferencial_aliquota = vr_diferencial_aliquota.quantize(D('0.01'))


    retorno = {
        'al_diferencial_aliquota': al_diferencial_aliquota,
        'vr_diferencial_aliquota': vr_diferencial_aliquota,
    }

    return retorno


def calcula_icms_st(item_dict):
    if item_dict is None:
        item_dict = {}

    regime_tributario = (item_dict.regime_tributario or REGIME_TRIBUTARIO_SIMPLES)
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    cst_icms = (item_dict.cst_icms or '')
    cst_icms_sn = (item_dict.cst_icms_sn or '')
    md_icms_st = (item_dict.md_icms_st or '')
    pr_icms_st = D('%.4f' % (item_dict.pr_icms_st or 0))
    rd_icms_st = D('%.4f' % (item_dict.rd_icms_st or 0))
    al_icms_st = D('%.4f' % (item_dict.al_icms_st or 0))
    bc_icms_st_com_ipi = (item_dict.bc_icms_st_com_ipi or False)
    vr_ipi = D('%.2f' % (item_dict.vr_ipi or 0))
    vr_outras = D('%.2f' % (item_dict.vr_outras or 0))
    bc_icms_proprio = D('%.2f' % (item_dict.bc_icms_proprio or 0))
    al_icms_proprio = D('%.2f' % (item_dict.al_icms_proprio or 0))
    vr_icms_proprio = D('%.2f' % (item_dict.vr_icms_proprio or 0))

    #
    # Agora, calculamos o ICMS ST
    #
    bc_icms_st = D('0')
    vr_icms_st = D('0')

    if cst_icms in ST_ICMS_CALCULA_ST or cst_icms_sn in ST_ICMS_SN_CALCULA_ST:
        if md_icms_st == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st = vr_operacao_tributacao

            #
            # Nas devoluções, o valor do IPI é informado em outras depesas acessórias;
            # nesses casos, inverter a consideração da soma do valor do IPI, pelo valor
            # das despesas acessórias
            #
            if item_dict.cfop_id in CFOP_ID_DEVOLUCAO:
                if not bc_icms_st_com_ipi:
                    bc_icms_st -= vr_outras

            elif bc_icms_st_com_ipi:
                bc_icms_st += vr_ipi

            bc_icms_st = bc_icms_st * (1 + (pr_icms_st / D('100.0000000000')))

        else:  # md_icms_st in MODALIDADE_BASE_ICMS_ST_PRECO_FIXO
            bc_icms_st = quantidade_tributacao * pr_icms_st

            if bc_icms_st_com_ipi:
                bc_icms_st += vr_ipi

        bc_icms_st = bc_icms_st.quantize(D('0.01'))

        #
        # Vai haver redução da base de cálculo?
        #
        if rd_icms_st > 0:
            bc_icms_st = bc_icms_st * (1 - (rd_icms_st / D('100.0000000000')))

        bc_icms_st = bc_icms_st.quantize(D('0.01'))
        vr_icms_st = bc_icms_st * (al_icms_st / D('100.0000000000'))
        vr_icms_st = vr_icms_st.quantize(D('0.01'))

        if vr_icms_st > 0:
            vr_icms_st -= vr_icms_proprio

        vr_icms_st = vr_icms_st.quantize(D('0.01'))

    if (regime_tributario == REGIME_TRIBUTARIO_SIMPLES and cst_icms_sn not in ST_ICMS_SN_CALCULA_PROPRIO) or cst_icms in ST_ICMS_ZERA_ICMS_PROPRIO:
        bc_icms_proprio = D('0')
        al_icms_proprio = D('0')
        vr_icms_proprio = D('0')

    retorno = {
        'bc_icms_st': bc_icms_st,
        'vr_icms_st': vr_icms_st,
        'bc_icms_proprio': bc_icms_proprio,
        'al_icms_proprio': al_icms_proprio,
        'vr_icms_proprio': vr_icms_proprio,
    }

    return retorno


def calcula_icms_st_retido(item_dict):
    if item_dict is None:
        item_dict = {}

    #regime_tributario = (item_dict.regime_tributario', REGIME_TRIBUTARIO_SIMPLES)
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    cst_icms = (item_dict.cst_icms or '')
    cst_icms_sn = (item_dict.cst_icms_sn or '')
    md_icms_st_retido = (item_dict.md_icms_st_retido or '')
    pr_icms_st_retido = D('%.4f' % (item_dict.pr_icms_st_retido or 0))
    rd_icms_st_retido = D('%.4f' % (item_dict.rd_icms_st_retido or 0))
    al_icms_st_retido = D('%.4f' % (item_dict.al_icms_st_retido or 0))
    bc_icms_st_retido_com_ipi = (item_dict.bc_icms_st_com_ipi or False)
    vr_ipi = D('%.2f' % (item_dict.vr_ipi or 0))
    bc_icms_proprio = D('%.2f' % (item_dict.bc_icms_proprio or 0))
    al_icms_proprio = D('%.2f' % (item_dict.al_icms_proprio or 0))
    vr_icms_proprio = D('%.2f' % (item_dict.vr_icms_proprio or 0))

    bc_icms_st_retido = D('0')
    vr_icms_st_retido = D('0')

    #
    # Agora, o ICMS retido na operação anterior
    #
    if cst_icms == ST_ICMS_ANTERIOR or cst_icms_sn == ST_ICMS_SN_ANTERIOR:
        if md_icms_st_retido == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st_retido = vr_operacao_tributacao

            if bc_icms_st_retido_com_ipi:
                bc_icms_st_retido += vr_ipi

            bc_icms_st_retido = bc_icms_st_retido * (1 + (pr_icms_st_retido / D('100.0000000000')))

        else:  # md_icms_st_retido in MODALIDADE_BASE_ICMS_ST_PRECO_FIXO
            bc_icms_st_retido = quantidade_tributacao * pr_icms_st_retido

            if bc_icms_st_retido_com_ipi:
                bc_icms_st_retido += vr_ipi

        bc_icms_st_retido = bc_icms_st_retido.quantize(D('0.01'))

        #
        # Vai haver redução da base de cálculo?
        #
        if rd_icms_st_retido > 0:
            bc_icms_st_retido = bc_icms_st_retido * (1 - (rd_icms_st_retido / D('100.0000000000')))

        bc_icms_st_retido = bc_icms_st_retido.quantize(D('0.01'))
        vr_icms_st_retido = bc_icms_st_retido * (al_icms_st_retido / D('100.0000000000'))
        vr_icms_st_retido = vr_icms_st_retido.quantize(D('0.01'))
        vr_icms_st_retido -= vr_icms_proprio

        #
        # Zera o ICMS próprio que foi usado no cálculo
        #
        bc_icms_proprio = D('0')
        al_icms_proprio = D('0')
        vr_icms_proprio = D('0')

    retorno = {
        'bc_icms_st_retido': bc_icms_st_retido,
        'vr_icms_st_retido': vr_icms_st_retido,
        'bc_icms_proprio': bc_icms_proprio,
        'al_icms_proprio': al_icms_proprio,
        'vr_icms_proprio': vr_icms_proprio,
    }

    return retorno


def calcula_icms_st_compra(item_dict):
    if item_dict is None:
        item_dict = {}


    #regime_tributario = (item_dict.regime_tributario', REGIME_TRIBUTARIO_SIMPLES)
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    md_icms_st_compra = (item_dict.md_icms_st_compra or '')
    pr_icms_st_compra = D('%.4f' % (item_dict.pr_icms_st_compra or 0))
    rd_icms_st_compra = D('%.4f' % (item_dict.rd_icms_st_compra or 0))
    al_icms_st_compra = D('%.4f' % (item_dict.al_icms_st_compra or 0))
    bc_icms_st_compra_com_ipi = (item_dict.bc_icms_st_com_ipi or False)
    vr_ipi = D('%.2f' % (item_dict.vr_ipi or 0))
    bc_icms_proprio = D('%.2f' % (item_dict.bc_icms_proprio or 0))
    al_icms_proprio = D('%.2f' % (item_dict.al_icms_proprio or 0))
    vr_icms_proprio = D('%.2f' % (item_dict.vr_icms_proprio or 0))

    bc_icms_st_compra = D('0')
    vr_icms_st_compra = D('0')

    #
    # Agora, o ICMS da compra
    #
    if item_dict.forca_recalculo_st_compra and md_icms_st_compra and pr_icms_st_compra and al_icms_st_compra:
        proprio = calcula_icms_proprio(item_dict, forca_recalculo_st_compra=True)
        vr_icms_proprio = proprio['vr_icms_proprio']

        if md_icms_st_compra == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st_compra = vr_operacao_tributacao
            bc_icms_st_compra = bc_icms_st_compra * (1 + (pr_icms_st_compra / D('100.0000000000')))

        else:  # md_icms_st_compra in MODALIDADE_BASE_ICMS_ST_PRECO_FIXO
            bc_icms_st_compra = quantidade_tributacao * pr_icms_st_compra

        bc_icms_st_compra = bc_icms_st_compra.quantize(D('0.01'))

        #
        # Vai haver redução da base de cálculo?
        #
        if rd_icms_st_compra > 0:
            bc_icms_st_compra = bc_icms_st_compra * (1 - (rd_icms_st_compra / D('100.0000000000')))

        bc_icms_st_compra = bc_icms_st_compra.quantize(D('0.01'))
        vr_icms_st_compra = bc_icms_st_compra * (al_icms_st_compra / D('100.0000000000'))
        vr_icms_st_compra = vr_icms_st_compra.quantize(D('0.01'))
        vr_icms_st_compra -= vr_icms_proprio

    retorno = {
        'bc_icms_st_compra': bc_icms_st_compra,
        'vr_icms_st_compra': vr_icms_st_compra,
    }

    return retorno


def calcula_iss(item_dict):
    if item_dict is None:
        item_dict = {}

    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    cst_iss = (item_dict.cst_iss or '')
    al_iss = D('%.4f' % (item_dict.al_iss or 0))

    bc_iss = D('0')
    vr_iss = D('0')

    #
    # Agora, o ICMS retido na operação anterior
    #
    if cst_iss != ST_ISS_ISENTO:
        bc_iss = vr_operacao_tributacao
        vr_iss = bc_iss * (al_iss / D('100.0000000000'))
        vr_iss = vr_iss.quantize(D('0.01'))

    retorno = {
        'bc_iss': bc_iss,
        'vr_iss': vr_iss,
    }

    return retorno


def calcula_pis_cofins(self, cr, uid, item_dict):
    if item_dict is None:
        item_dict = {}

    regime_tributario = (item_dict.regime_tributario or REGIME_TRIBUTARIO_SIMPLES)
    cst_pis = (item_dict.cst_pis or '')
    quantidade_tributacao = D('%.4f' % (item_dict.quantidade_tributacao or 0))
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    al_pis_proprio = D('%.4f' % (item_dict.al_pis_proprio or 0))
    al_cofins_proprio = D('%.4f' % (item_dict.al_cofins_proprio or 0))

    md_pis_proprio = MODALIDADE_BASE_PIS_ALIQUOTA
    #bc_pis_proprio = D('0')
    if  'cfop' in item_dict and item_dict['cfop'] and item_dict['cfop'][0] == '3':
        bc_pis_proprio = D('%.2f' % (item_dict.bc_pis_proprio or 0))
    else:
        bc_pis_proprio = vr_operacao_tributacao
    vr_pis_proprio = D('0')
    md_cofins_proprio = md_pis_proprio
    #bc_cofins_proprio = D('0')
    bc_cofins_proprio = bc_pis_proprio
    vr_cofins_proprio = D('0')

    if regime_tributario != REGIME_TRIBUTARIO_SIMPLES and (cst_pis in ST_PIS_CALCULA or cst_pis in ST_PIS_CALCULA_CREDITO):
        if cst_pis in ST_PIS_CALCULA_ALIQUOTA:
            md_pis_proprio = MODALIDADE_BASE_PIS_ALIQUOTA
            #bc_pis_proprio = vr_operacao_tributacao
            vr_pis_proprio = bc_pis_proprio * (al_pis_proprio / D('100.0000000000'))

            md_cofins_proprio = md_pis_proprio
            bc_cofins_proprio = bc_pis_proprio
            vr_cofins_proprio = bc_cofins_proprio * (al_cofins_proprio / D('100.0000000000'))
        else:
            md_pis_proprio = MODALIDADE_BASE_PIS_QUANTIDADE
            vr_pis_proprio = quantidade_tributacao * al_pis_proprio

            md_cofins_proprio = md_pis_proprio
            vr_cofins_proprio = quantidade_tributacao * al_cofins_proprio

        bc_pis_proprio = bc_pis_proprio.quantize(D('0.01'))
        vr_pis_proprio = vr_pis_proprio.quantize(D('0.01'))
        bc_cofins_proprio = bc_cofins_proprio.quantize(D('0.01'))
        vr_cofins_proprio = vr_cofins_proprio.quantize(D('0.01'))

    retorno = {
        'cst_pis': cst_pis,
        'md_pis_proprio': md_pis_proprio,
        'bc_pis_proprio': bc_pis_proprio,
        'vr_pis_proprio': vr_pis_proprio,
        'cst_cofins': cst_pis,
        'md_cofins_proprio': md_cofins_proprio,
        'bc_cofins_proprio': bc_cofins_proprio,
        'vr_cofins_proprio': vr_cofins_proprio,
    }

    return retorno


def calcula_total_nf(item_dict):
    #
    # Calcula o total da nota (parcial correspondente ao item)
    #
    #compoe_total = (item_dict.compoe_total or True)
    vr_operacao = D('%.2f' % (item_dict.vr_operacao or 0))
    vr_ipi = D('%.2f' % (item_dict.vr_ipi or 0))
    vr_icms_st = D('%.2f' % (item_dict.vr_icms_st or 0))
    vr_ii = D('%.2f' % (item_dict.vr_ii or 0))

    vr_nf = D('0')
    vr_fatura = D('0')

    #if compoe_total:

    vr_nf = vr_operacao + vr_ipi + vr_icms_st + vr_ii
    vr_nf = vr_nf.quantize(D('0.01'))
    vr_fatura = vr_nf

    retorno = {
        'vr_nf': vr_nf,
        'vr_fatura': vr_fatura,
    }

    return retorno


def calcula_ibpt(item_dict):
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    al_ibpt = D('%.4f' % (item_dict.al_ibpt or 0))

    vr_ibpt = vr_operacao_tributacao * (al_ibpt / D('100.0000000000'))
    vr_ibpt = vr_ibpt.quantize(D('0.01'))

    retorno = {
        'vr_ibpt': vr_ibpt
    }

    return retorno


def calcula_previdencia(item_dict):
    vr_operacao_tributacao = D('%.2f' % (item_dict.vr_operacao_tributacao or 0))
    al_previdencia = D('%.4f' % (item_dict.al_previdencia or 0))

    bc_previdencia = D('0')
    vr_previdencia = D('0')

    if item_dict.previdencia_retido and al_previdencia > 0:
        bc_previdencia = vr_operacao_tributacao
        vr_previdencia = bc_previdencia * (al_previdencia / D('100.0000000000'))
        vr_previdencia = vr_previdencia.quantize(D('0.01'))

    retorno = {
        'bc_previdencia': bc_previdencia,
        'vr_previdencia': vr_previdencia,
    }

    return retorno

def calcula_simples(item_dict):
    al_simples = D('%.2f' % (item_dict.al_simples or 0))

    bc_simples = D('%.2f' % (item_dict.vr_operacao or 0))
    vr_simples = bc_simples * (al_simples / D('100.0000000000'))
    vr_simples = vr_simples.quantize(D('0.01'))

    retorno = {
        'vr_simples': vr_simples
    }

    return retorno
