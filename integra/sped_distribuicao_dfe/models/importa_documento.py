# -*- coding: utf-8 -*-

#from __future__ import (division, print_function, unicode_literals, absolute_import)

from decimal import Decimal
import random
import json
from importa_participante import localiza_municipio, processa_participante
from pybrasil.data import parse_datetime, UTC, data_hora_horario_brasilia


def processa_documento(self, cr, uid, company_id, docnfe, modelo, dd_obj):
    if modelo == '55':
        nfe = docnfe

        emitente_id = processa_participante(self, cr, uid, nfe.infNFe.emit, nfe.infNFe.emit.enderEmit)
        cnpj_emitente = nfe.infNFe.emit.CNPJ.valor
        destinatario_id = processa_participante(self, cr, uid, nfe.infNFe.dest, nfe.infNFe.dest.enderDest)
        cnpj_destinatario = nfe.infNFe.dest.CNPJ.valor

        #if destinatario_id in EMPRESAS_PARTNER_ID or cnpj_destinatario in EMPRESAS_CNPJ:
        emissao = '1'

        #if destinatario_id in EMPRESAS_PARTNER_ID:
            #company_id = EMPRESAS_PARTNER_ID[destinatario_id]['company_id']
        #else:
            #company_id = EMPRESAS_CNPJ[cnpj_destinatario]['company_id']

        participante_id = emitente_id

        #else:
            #emissao = '0'

            #if emitente_id in EMPRESAS_PARTNER_ID:
                #company_id = EMPRESAS_PARTNER_ID[emitente_id]['company_id']
            #else:
                #company_id = EMPRESAS_CNPJ[cnpj_emitente]['company_id']

            #participante_id = destinatario_id

        serie = unicode(nfe.infNFe.ide.serie.valor)
        numero = nfe.infNFe.ide.nNF.valor

        documento_id = localiza_documento(self, cr, uid, company_id, modelo, serie, numero, emissao, participante_id)

        if documento_id:
            return documento_id

        else:
            return cria_documento(self, cr, uid, nfe, company_id, modelo, serie, numero, emissao, participante_id, dd_obj)

            #if emissao = '0' and destinatario_id in EMPRESAS_PARTNER_ID:
                #emissao = '1'
                #company_id = EMPRESAS_PARTNER_ID[emitente_id]['company_id']
                #participante_id = emitente_id

                #documento_id = localiza_documento(nfe, company_id, modelo, serie, numero, emissao, participante_id)


def localiza_cfop(self, cr, uid, codigo):
    cfop_id = self.pool.get('sped.cfop').search(cr, uid, [('codigo', '=', codigo)])

    if cfop_id:
        return cfop_id[0]

    return False


def ajusta_decimais(dados):
    #
    # Converte valores Decimal para string
    #
    for chave in dados.keys():
        if isinstance(dados[chave], Decimal):
            dados[chave] = float(unicode(dados[chave]))

    return dados


def localiza_documento(self, cr, uid, company_id, modelo, serie, numero, emissao, participante_id):
    if emissao == '0':
        documento_id = self.pool.get('sped.documento').search(cr, uid, [('company_id', '=', company_id),
        ('emissao', '=', emissao), ('modelo', '=', modelo), ('serie', '=', serie),
        ('numero', '=', numero)])
    else:
        documento_id = self.pool.get('sped.documento').search(cr, uid, [('company_id', '=', company_id),
        ('emissao', '=', emissao), ('modelo', '=', modelo), ('serie', '=', serie),
        ('numero', '=', numero), ('partner_id', '=', participante_id), ('entrada_saida', '=', '0')])

    if documento_id:
        return documento_id[0]

    return False


def cria_documento(self, cr, uid, docnfe, company_id, modelo, serie, numero, emissao, participante_id, dd_obj):
    if modelo == '55':
        nfe = docnfe
        nfe.monta_chave()

    if nfe.infNFe.versao.valor == '3.10':
        data_emissao = parse_datetime(nfe.infNFe.ide.dhEmi.valor)

        #
        # Não importa a data de emissão, assume o momento da inclusão da nota
        #
        #if nfe.infNFe.ide.dhSaiEnt.valor:
            #data_entrada_saida = parse_datetime(nfe.infNFe.ide.dhSaiEnt.valor)
        #else:
            #data_entrada_saida = data_emissao

    else:
        data_emissao = str(nfe.infNFe.ide.dEmi.valor) + ' 12:00:00'

        #
        # Não importa a data de emissão, assume o momento da inclusão da nota
        #
        #if nfe.infNFe.ide.dSaiEnt.valor:
            #data_entrada_saida = str(nfe.infNFe.ide.dSaiEnt.valor) + ' 12:00:00'
        #else:
            #data_entrada_saida = data_emissao

        data_emissao = parse_datetime(data_emissao)
        #data_entrada_saida = parse_datetime(data_entrada_saida)

    data_emissao = data_hora_horario_brasilia(data_emissao)
    #data_entrada_saida = data_hora_horario_brasilia(data_entrada_saida)
    data_emissao = UTC.normalize(data_emissao)
    #data_entrada_saida = UTC.normalize(data_entrada_saida)

    #
    # Vamos incluir o documento e todos os itens
    #
    dados_documento = {
        'company_id': company_id,
        'state': 'autorizada',

        #
        # Cabeçalho do documento
        #
        'emissao': emissao,
        'modelo': modelo,
        'serie': serie,
        'subserie': '',
        'numero': numero,
        'situacao': '00',
        'entrada_saida': unicode(nfe.infNFe.ide.tpNF.valor),
        'data_emissao': str(data_emissao)[:19],
        #'data_entrada_saida': str(data_entrada_saida)[:19],
        #'hora_entrada_saida': ,
        'regime_tributario': unicode(nfe.infNFe.emit.CRT.valor),
        'ambiente_nfe': unicode(nfe.infNFe.ide.tpAmb.valor),
        'tipo_emissao_nfe': unicode(nfe.infNFe.ide.tpEmis.valor),
        'finalidade_nfe': unicode(nfe.infNFe.ide.finNFe.valor),
        'forma_pagamento': unicode(nfe.infNFe.ide.indPag.valor),
        'ie_st': nfe.infNFe.emit.IEST.valor,
        'municipio_fato_gerador_id': localiza_municipio(self, cr, uid, unicode(nfe.infNFe.ide.cMunFG.valor)),

        #'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal'),
        #'naturezaoperacao_id': fields.many2one('sped.naturezaoperacao', u'Natureza da operação'),

        'partner_id': participante_id,

        # 'endereco_entrega': fields.many2one(),
        # 'endereco_retirada': fields.many2one(),

        #'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        # 'endereco_cobranca': fields.many2one(),

        #
        # Totais dos itens
        #

        # Valor total dos produtos
        'vr_produtos': nfe.infNFe.total.ICMSTot.vProd.valor,
        'vr_produtos_tributacao': nfe.infNFe.total.ICMSTot.vProd.valor,

        # Outros valores acessórios
        'vr_frete': nfe.infNFe.total.ICMSTot.vFrete.valor,
        'vr_seguro': nfe.infNFe.total.ICMSTot.vSeg.valor,
        'vr_desconto': nfe.infNFe.total.ICMSTot.vDesc.valor,
        'vr_outras': nfe.infNFe.total.ICMSTot.vOutro.valor,
        #'vr_operacao': 0,
        #'vr_operacao_tributacao': 0,

        # ICMS próprio
        'bc_icms_proprio': nfe.infNFe.total.ICMSTot.vBC.valor,
        'vr_icms_proprio': nfe.infNFe.total.ICMSTot.vICMS.valor,
        # ICMS SIMPLES
        #'vr_icms_sn': 0,
        # ICMS ST
        'bc_icms_st': nfe.infNFe.total.ICMSTot.vBCST.valor,
        'vr_icms_st': nfe.infNFe.total.ICMSTot.vST.valor,
        # ICMS ST retido
        #'bc_icms_st_retido': CampoDinheiro(u'Base do ICMS retido anteriormente por substituição tributária'),
        #'vr_icms_st_retido': CampoDinheiro(u'Valor do ICMS retido anteriormente por substituição tributária'),

        # IPI
        #'bc_ipi': CampoDinheiro(u'Base do IPI'),
        'vr_ipi': nfe.infNFe.total.ICMSTot.vIPI.valor,

        # Imposto de importação
        #'bc_ii': CampoDinheiro(u'Base do imposto de importação'),
        'vr_ii': nfe.infNFe.total.ICMSTot.vII.valor,

        # PIS e COFINS
        #'bc_pis_proprio': CampoDinheiro(u'Base do PIS próprio'),
        'vr_pis_proprio': nfe.infNFe.total.ICMSTot.vPIS.valor,
        #'bc_cofins_proprio': CampoDinheiro(u'Base da COFINS própria'),
        'vr_cofins_proprio': nfe.infNFe.total.ICMSTot.vCOFINS.valor,
        #'bc_pis_st': CampoDinheiro(u'Base do PIS ST'),
        #'vr_pis_st': CampoDinheiro(u'Valor do PIS ST'),
        #'bc_cofins_st': CampoDinheiro(u'Base da COFINS ST'),
        #'vr_cofins_st': CampoDinheiro(u'Valor do COFINS ST'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': nfe.infNFe.total.ISSQNTot.vServ.valor,

        # ISS
        'bc_iss': nfe.infNFe.total.ISSQNTot.vBC.valor,
        'vr_iss': nfe.infNFe.total.ISSQNTot.vISS.valor,

        # PIS e COFINS
        'vr_pis_servico': nfe.infNFe.total.ISSQNTot.vPIS.valor,
        'vr_cofins_servico': nfe.infNFe.total.ISSQNTot.vCOFINS.valor,

        #
        # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
        #

        # PIS e COFINS
        'vr_pis_retido': nfe.infNFe.total.retTrib.vRetPIS.valor,
        'vr_cofins_retido': nfe.infNFe.total.retTrib.vRetCOFINS.valor,

        # Contribuição social sobre lucro líquido
        'vr_csll': nfe.infNFe.total.retTrib.vRetCSLL.valor,

        # IRRF
        'bc_irrf': nfe.infNFe.total.retTrib.vBCIRRF.valor,
        'vr_irrf': nfe.infNFe.total.retTrib.vIRRF.valor,

        # Previdência social
        'bc_previdencia': nfe.infNFe.total.retTrib.vBCRetPrev.valor,
        'vr_previdencia': nfe.infNFe.total.retTrib.vRetPrev.valor,

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': nfe.infNFe.total.ICMSTot.vNF.valor,
        'vr_fatura': nfe.infNFe.total.ICMSTot.vNF.valor,

        #
        # Transporte e frete
        #
        'modalidade_frete': unicode(nfe.infNFe.transp.modFrete.valor),
        #'transportadora_id': localiza_participante(),
        #'motorista_id': fields.many2one('sped.participante', u'Motorista'),
        #'veiculo_id': fields.many2one('sped.veiculo', u'Veículo'),
        #'reboque1_id': fields.many2one('sped.veiculo', u'1º reboque'),
        #'reboque2_id': fields.many2one('sped.veiculo', u'2º reboque'),
        #'reboque3_id': fields.many2one('sped.veiculo', u'3º reboque'),
        #'reboque4_id': fields.many2one('sped.veiculo', u'4º reboque'),
        #'reboque5_id': fields.many2one('sped.veiculo', u'5º reboque'),

        # Impostos retidos sobre o transporte
        'vr_servico_frete': nfe.infNFe.transp.retTransp.vServ.valor,
        'bc_icms_frete': nfe.infNFe.transp.retTransp.vBCRet.valor,
        'al_icms_frete': nfe.infNFe.transp.retTransp.pICMSRet.valor,
        'vr_icms_frete': nfe.infNFe.transp.retTransp.vICMSRet.valor,
        'cfop_frete_id': localiza_cfop(self, cr, uid, unicode(nfe.infNFe.transp.retTransp.CFOP.valor)),
        'municipio_frete_id': localiza_municipio(self, cr, uid, unicode(nfe.infNFe.transp.retTransp.cMunFG.valor)),

        # Informações adicionais
        'infadfisco': nfe.infNFe.infAdic.infAdFisco.valor,
        'infcomplementar': nfe.infNFe.infAdic.infCpl.valor,

        # Exportação
        'exportacao_estado_embarque': nfe.infNFe.exporta.UFEmbarq.valor,
        'exportacao_local_embarque': nfe.infNFe.exporta.xLocEmbarq.valor,

        # Compras públicas
        'compra_nota_empenho': nfe.infNFe.compra.xNEmp.valor,
        'compra_pedido': nfe.infNFe.compra.xPed.valor,
        'compra_contrato': nfe.infNFe.compra.xCont.valor,

        #
        # Chave de acesso em documentos eletrônicos
        #
        'chave': nfe.chave,

        #
        # Valores originais em documentos de entrada
        #
        'natureza_operacao_original': nfe.infNFe.ide.natOp.valor,
        'itens_originais_processados': False,
        'mercadoria_recebida': False,
    }

    #
    # Emissão por terceiros é sempre entrada
    #
    if emissao == '1':
        dados_documento['entrada_saida'] = '0'

    dados_documento = ajusta_decimais(dados_documento)

    documento_pool = self.pool.get('sped.documento')
    documento_id = documento_pool.create(cr, uid, dados_documento)

    if documento_id:
        itens_importados = []
        duplicatas_importadas = []
        dados_documento['itens'] = []
        dados_documento['duplicatas'] = []

        for det in nfe.infNFe.det:
            item_id, dados_item = cria_item_documento(self, cr, uid, documento_id, det, nfe)

            if item_id:
                itens_importados += [item_id]
                dados_documento['itens'] += [dados_item]

        for dup in nfe.infNFe.cobr.dup:
            dup_id, dados_dup = cria_duplicata_documento(self, cr, uid, documento_id, dup, nfe)

            if dup_id:
                duplicatas_importadas += [dup_id]
                dados_documento['duplicatas'] += [dados_dup]

        if len(itens_importados) != len(nfe.infNFe.det) or len(duplicatas_importadas) != len(nfe.infNFe.cobr.dup):
            documento_pool.unlink(cr, uid, [documento_id])
            documento_id = False

        else:
            documento_pool.write(cr, uid, [documento_id], {'dados_originais': json.dumps(dados_documento)})

    #
    # Tratamos a entrada automática das transferências
    # Usamos o admin para isso, para evitar que os bloqueios por usuário impeçam de localizar a NF
    #
    saida_ids = documento_pool.search(cr, 1, [('emissao', '=', '0'), ('entrada_saida', '=', '1'), ('chave', '=', nfe.chave)])

    if len(saida_ids) or dd_obj.documento_original_id:
        #
        # Usamos o admin para isso, para evitar que os bloqueios por usuário impeçam de localizar a NF
        #
        if dd_obj.documento_original_id:
            saida_obj = dd_obj.documento_original_id
        else:
            saida_obj = documento_pool.browse(cr, 1, saida_ids[0])

        if getattr(saida_obj.operacao_id, 'operacao_entrada_id', False):
            documento_pool.write(cr, uid, [documento_id], {'operacao_id': saida_obj.operacao_id.operacao_entrada_id.id})
            entrada_obj = documento_pool.browse(cr, uid, documento_id)
            dados = documento_pool.onchange_operacao(cr, uid, [documento_id], saida_obj.operacao_id.operacao_entrada_id.id)
            documento_pool.write(cr, uid, [documento_id], dados['value'])
            entrada_obj = documento_pool.browse(cr, uid, documento_id)

            item_pool = self.pool.get('sped.documentoitem')
            for item_obj in entrada_obj.documentoitem_ids:
                produto_ids = item_pool.search(cr, uid, [('documento_id', '=', saida_obj.id), ('produto_id.default_code', '=', item_obj.produto_codigo)])

                if len(produto_ids):
                    item_saida_obj = item_pool.browse(cr, 1, produto_ids[0])

                    produto_id = item_saida_obj.produto_id.id

                    contexto_item = {
                        'default_company_id': entrada_obj.company_id.id,
                        'default_partner_id': entrada_obj.partner_id.id,
                        'default_operacao_id': entrada_obj.operacao_id.id,
                        'default_entrada_saida': entrada_obj.entrada_saida,
                        'default_regime_tributario': entrada_obj.regime_tributario,
                        'default_emissao': entrada_obj.emissao,
                        'default_data_emissao': entrada_obj.data_emissao_brasilia,
                    }
                    dados = item_pool.onchange_produto_entrada(cr, uid, [item_obj.id], produto_id, item_obj.cfop_original_id.id, False, contexto_item)

                    if 'value' in dados:
                        dados['value']['produto_id'] = produto_id
                        item_pool.write(cr, uid, [item_obj.id], dados['value'])

            #
            # Por fim, ajusta retenções e itens processados
            #
            documento_pool.write(cr, uid, [documento_id], {'recalculo': int(random.random() * 100000000)})
            documento_pool.trata_itens_entrada_terceiros(cr, uid, [documento_id])

    return documento_id


def cria_item_documento(self, cr, uid, documento_id, det, nfe):
    dados_item = {
        'documento_id': documento_id,

        #
        # Campos replicados do documento, para o cálculo na emissão própria
        #
        # 'company_id': fields.many2one('res.company', u'Empresa'),
        'regime_tributario':  unicode(nfe.infNFe.emit.CRT.valor),
        # 'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão'),
        # 'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal'),
        # 'participante_id': fields.many2one('sped.participante', u'Participante'),
        # 'data_emissao': fields.date(u'Data de emissão'),

        'cfop_id': False,
        'cfop_original_id': localiza_cfop(self, cr, uid, det.prod.CFOP.valor),
        'compoe_total': unicode(det.prod.indTot.valor) == '1',
        #'movimentacao_fisica': fields.boolean(u'Há movimentação física do produto?'),

        # Dados do produto/serviço
        #'produto_id': fields.many2one('sped.produto', u'Produto'),
        #
        # Campos para a validação das entradas
        #
        'produto_codigo': det.prod.cProd.valor.strip(),
        'produto_descricao': det.prod.xProd.valor.strip(),
        'produto_ncm': unicode(det.prod.NCM.valor).strip(),
        'produto_codigo_barras': unicode(det.prod.cEAN.valor).strip(),
        'unidade': det.prod.uCom.valor.strip(),
        'unidade_tributacao': det.prod.uTrib.valor.strip(),
        'fator_quantitade': 1,
        'quantidade_original': det.prod.qCom.valor,

        #'credita_icms_proprio': fields.boolean(u'Credita ICMS próprio?'),
        #'credita_icms_st': fields.boolean(u'Credita ICMS ST?'),
        #'informa_icms_st': fields.boolean(u'Informa ICMS ST?'),
        #'credita_pis_cofins': fields.boolean(u'Credita PIS-COFINS?'),

        'quantidade': det.prod.qCom.valor,
        'vr_unitario': det.prod.vUnCom.valor,

        # Quantidade de tributação
        'quantidade_tributacao': det.prod.qTrib.valor,
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': det.prod.vUnTrib.valor,

        # Valor total dos produtos
        'vr_produtos': det.prod.vProd.valor,
        'vr_produtos_tributacao': det.prod.qTrib.valor * det.prod.vUnTrib.valor,

        # Outros valores acessórios
        'vr_frete': det.prod.vFrete.valor,
        'vr_seguro': det.prod.vSeg.valor,
        'vr_desconto': det.prod.vDesc.valor,
        'vr_outras': det.prod.vOutro.valor,
        'vr_operacao': det.prod.vProd.valor + det.prod.vFrete.valor + det.prod.vSeg.valor + det.prod.vOutro.valor - det.prod.vDesc.valor,
        'vr_operacao_tributacao': (det.prod.qTrib.valor * det.prod.vUnTrib.valor) + det.prod.vFrete.valor + det.prod.vSeg.valor + det.prod.vOutro.valor - det.prod.vDesc.valor,

        #
        # ICMS próprio
        #
        'org_icms': unicode(det.imposto.ICMS.orig.valor),
        'cst_icms': unicode(det.imposto.ICMS.CST.valor),
        'partilha': det.imposto.ICMS.partilha,
        'al_bc_icms_proprio_partilha': det.imposto.ICMS.pBCOp.valor,
        'uf_partilha': det.imposto.ICMS.UFST.valor,
        'repasse': det.imposto.ICMS.repasse,
        'md_icms_proprio': unicode(det.imposto.ICMS.modBC.valor),
        #'pr_icms_proprio': CampoQuantidade(u'Parâmetro do ICMS próprio'),
        'rd_icms_proprio': det.imposto.ICMS.pRedBC.valor,
        #'bc_icms_proprio_com_ipi': fields.boolean('IPI integra a base do ICMS próprio?'),
        'bc_icms_proprio': det.imposto.ICMS.vBC.valor,
        'al_icms_proprio': det.imposto.ICMS.pICMS.valor,
        'vr_icms_proprio': det.imposto.ICMS.vICMS.valor,

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': unicode(det.imposto.ICMS.CSOSN.valor),
        'al_icms_sn': det.imposto.ICMS.pCredSN.valor,
        #'rd_icms_sn': CampoPorcentagem(u'% estadual de redução da alíquota de ICMS'),
        'vr_icms_sn': det.imposto.ICMS.vCredICMSSN.valor,

        #
        # ICMS ST
        #
        'md_icms_st': unicode(det.imposto.ICMS.modBCST.valor),
        'pr_icms_st': det.imposto.ICMS.pMVAST.valor,
        'rd_icms_st': det.imposto.ICMS.pRedBCST.valor,
        #'bc_icms_st_com_ipi': fields.boolean(u'IPI integra a base do ICMS ST?'),
        'bc_icms_st': det.imposto.ICMS.vBCST.valor,
        'al_icms_st': det.imposto.ICMS.pICMSST.valor,
        'vr_icms_st': det.imposto.ICMS.vICMSST.valor,

        #
        # Parâmetros relativos ao ICMS retido anteriormente por substituição tributária
        # na origem
        #
        #'md_icms_st_retido': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo'),
        #'pr_icms_st_retido': CampoQuantidade(u'Parâmetro da base de cáculo'),
        #'rd_icms_st_retido': CampoPorcentagem(u'% de redução da base de cálculo do ICMS retido'),
        'bc_icms_st_retido': det.imposto.ICMS.vBCSTRet.valor,
        #'al_icms_st_retido': CampoPorcentagem(u'Alíquota do ICMS ST retido na origem'),
        'vr_icms_st_retido': det.imposto.ICMS.vICMSSTRet.valor,

        #
        # IPI padrão
        #
        #'apuracao_ipi': fields.selection(APURACAO_IPI, u'Período de apuração do IPI'),
        'cst_ipi': det.imposto.IPI.CST.valor,
        #'md_ipi': fields.selection(MODALIDADE_BASE_IPI, u'Modalidade de cálculo do IPI'),
        'bc_ipi': det.imposto.IPI.vBC.valor,
        'al_ipi': det.imposto.IPI.pIPI.valor,
        'vr_ipi': det.imposto.IPI.vIPI.valor,

        #
        # Imposto de importação
        #
        'bc_ii': det.imposto.II.vBC.valor,
        'vr_despesas_aduaneiras': det.imposto.II.vDespAdu.valor,
        'vr_ii': det.imposto.II.vII.valor,
        'vr_iof': det.imposto.II.vIOF.valor,

        #
        # PIS próprio
        #
        'cst_pis': det.imposto.PIS.CST.valor,
        #'md_pis_proprio': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS próprio'),
        'bc_pis_proprio': det.imposto.PIS.vBC.valor,
        'al_pis_proprio': det.imposto.PIS.pPIS.valor,
        'vr_pis_proprio': det.imposto.PIS.vPIS.valor,

        #
        # PIS ST
        #
        #'md_pis_st': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS ST'),
        'bc_pis_st': det.imposto.PISST.vBC.valor,
        'al_pis_st': det.imposto.PISST.pPIS.valor,
        'vr_pis_st': det.imposto.PISST.vPIS.valor,

        #
        # COFINS própria
        #
        'cst_cofins': det.imposto.COFINS.CST.valor,
        #'md_cofins_proprio': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS própria'),
        'bc_cofins_proprio': det.imposto.COFINS.vBC.valor,
        'al_cofins_proprio': det.imposto.COFINS.pCOFINS.valor,
        'vr_cofins_proprio': det.imposto.COFINS.vCOFINS.valor,

        #
        # COFINS ST
        #
        #'md_cofins_st': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS ST'),
        'bc_cofins_st': det.imposto.COFINSST.vBC.valor,
        'al_cofins_st': det.imposto.COFINSST.pCOFINS.valor,
        'vr_cofins_st': det.imposto.COFINSST.vCOFINS.valor,

        #
        # Totais dos itens (grupo ISS)
        #

        ## Valor total dos serviços
        #'vr_servicos': CampoDinheiro(u'Valor dos serviços'),

        ## ISS
        'cst_iss': det.imposto.ISSQN.cSitTrib.valor,
        'bc_iss': det.imposto.ISSQN.vBC.valor,
        'al_iss': det.imposto.ISSQN.vAliq.valor,
        'vr_iss': det.imposto.ISSQN.vISSQN.valor,

        ## PIS e COFINS
        #'vr_pis_servico': CampoDinheiro(u'PIS sobre serviços'),
        #'vr_cofins_servico': CampoDinheiro(u'COFINS sobre serviços'),

        ##
        ## Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        ##
        'vr_nf': det.prod.vProd.valor + det.prod.vFrete.valor + det.prod.vSeg.valor + det.prod.vOutro.valor - det.prod.vDesc.valor + det.imposto.IPI.vIPI.valor + det.imposto.ICMS.vICMSST.valor + det.imposto.II.vII.valor,
        'vr_fatura': det.prod.vProd.valor + det.prod.vFrete.valor + det.prod.vSeg.valor + det.prod.vOutro.valor - det.prod.vDesc.valor + det.imposto.IPI.vIPI.valor + det.imposto.ICMS.vICMSST.valor + det.imposto.II.vII.valor,

        # Informações adicionais
        'infcomplementar': det.infAdProd.valor,

        #
        # Dados especiais para troca de informações entre empresas
        #
        #'numero_pedido': fields.char(u'Número do pedido', size=15),
        #'numero_item_pedido': fields.integer(u'Número do item pedido'),
    }

    #
    # Se for serviço
    #
    if det.imposto.ISSQN.cSitTrib.valor:
        dados_item['cst_icms'] = '41'

    dados_item = ajusta_decimais(dados_item)

    item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados_item)

    return item_id, dados_item


def cria_duplicata_documento(self, cr, uid, documento_id, dup, nfe):

    if not dup.dVenc._valor_string:
        return False, False

    dados_dup = {
        'documento_id': documento_id,
        'numero': dup.nDup.valor,
        'data_vencimento': dup.dVenc._valor_string[:10],
        'valor': dup.vDup.valor,
    }

    dados_dup = ajusta_decimais(dados_dup)

    dup_id = self.pool.get('sped.documentoduplicata').create(cr, uid, dados_dup)

    return dup_id, dados_dup
