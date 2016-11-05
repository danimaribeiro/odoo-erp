# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import os
import base64
from osv import osv
from pysped.nfe.processador_nfe import ProcessadorNFe
from pysped.nfe.webservices_flags import *
from pysped.nfe.leiaute import (NFe_310, Det_310, Dup_310, ProcNFe_310, Reboque_310, Vol_310, DI_310, Adi_310)
from pysped.nfe.leiaute import (ProcNFe_200)
from pysped.nfe.leiaute import (EventoCancNFe_100, ProcEventoCancNFe_100)
from pysped.nfe.leiaute import (EventoCCe_100, ProcEventoCCe_100)
from pysped.nfe.leiaute import NFRef_310
from pybrasil.inscricao import limpa_formatacao, valida_inscricao_estadual
from mako.template import Template
from sped.constante_tributaria import *
from decimal import Decimal as D
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime, agora, data_hora_horario_brasilia, UTC, formata_data

#
#
#
processador = ProcessadorNFe()
processador.danfe.nome_sistema = 'Integra 6.2'
#processador.danfe.site = 'http://www.ERPIntegra.com.br'


def prepara_certificado(self, cr, uid, doc_obj):
    empresa = doc_obj.company_id.partner_id
    caminho_empresa = os.path.expanduser('~/sped')

    if not empresa.cnpj_cpf:
        #
        # Pega a empresa ativa no momento
        #
        empresa_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento')
        empresa = self.pool.get('res.company').browse(cr, uid, empresa_id)
        empresa = empresa.partner_id

    caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf))

    processador.caminho = os.path.join(caminho_empresa, 'nfe')
    processador.estado  = empresa.municipio_id.estado_id.uf
    processador.ambiente = int(getattr(doc_obj, 'ambiente_nfe', '2'))
    #processador.contingencia_SCAN = doc_obj.tipo_emissao_nfe != '1'

    processador.certificado.arquivo = open(os.path.join(caminho_empresa, 'certificado_caminho.txt')).read().strip()
    processador.certificado.senha   = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip()

    if os.path.exists(os.path.join(caminho_empresa, 'logo_caminho.txt')):
        processador.danfe.logo = open(os.path.join(caminho_empresa, 'logo_caminho.txt')).read().strip()

    return processador

def monta_nfe(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)
    empresa = doc_obj.company_id.partner_id

    #
    # Bibliotecas importadas para serem usadas nos templates
    #
    template_imports = [
        'import pybrasil',
        'import math',
        'from pybrasil.base import (tira_acentos, primeira_maiuscula)',
        'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
        'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade, formata_valor)',
        'from pybrasil.valor.decimal import Decimal as D',
    ]

    #
    # Instancia uma NF-e
    #
    nfe = NFe_310()

    #
    # Identificação da NF-e
    #
    nfe.infNFe.ide.tpAmb.valor   = int(doc_obj.ambiente_nfe)
    nfe.infNFe.ide.tpNF.valor    = int(doc_obj.entrada_saida)
    nfe.infNFe.ide.cUF.valor     = UF_CODIGO[processador.estado]
    nfe.infNFe.ide.natOp.valor   = doc_obj.naturezaoperacao_id.nome
    nfe.infNFe.ide.indPag.valor  = int(doc_obj.forma_pagamento)
    nfe.infNFe.ide.serie.valor   = doc_obj.serie
    nfe.infNFe.ide.nNF.valor     = doc_obj.numero
    nfe.infNFe.ide.dhEmi.valor   = data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao + ' GMT'))
    nfe.infNFe.ide.dEmi.valor = nfe.infNFe.ide.dhEmi.valor
    #print(nfe.infNFe.ide.dhEmi.xml, doc_obj.data_emissao, data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao + ' GMT')), parse_datetime(doc_obj.data_emissao + ' GMT'))
    if doc_obj.data_entrada_saida:
        nfe.infNFe.ide.dhSaiEnt.valor = data_hora_horario_brasilia(parse_datetime(doc_obj.data_entrada_saida + ' GMT'))

    else:
        nfe.infNFe.ide.dhSaiEnt.valor = data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao + ' GMT'))

    nfe.infNFe.ide.dSaiEnt.valor = nfe.infNFe.ide.dhSaiEnt.valor
    nfe.infNFe.ide.hSaiEnt.valor = nfe.infNFe.ide.dhSaiEnt.valor

    nfe.infNFe.ide.tpAmb.valor   = int(doc_obj.ambiente_nfe)
    nfe.infNFe.ide.cMunFG.valor  = empresa.municipio_id.codigo_ibge[:7]
    nfe.infNFe.ide.tpImp.valor   = 1 # DANFE em retrato
    nfe.infNFe.ide.tpEmis.valor  = doc_obj.tipo_emissao_nfe
    nfe.infNFe.ide.finNFe.valor  = doc_obj.finalidade_nfe
    nfe.infNFe.ide.procEmi.valor = 0 # Emissão por aplicativo próprio
    nfe.infNFe.ide.verProc.valor = processador.danfe.nome_sistema

    #
    # Notas referenciadas
    #
    obs_ref = u''
    for docref_obj in doc_obj.documentoreferenciado_ids:
        docref = NFRef_310()
        if docref_obj.modelo == '55':
            if docref_obj.documentoreferenciado_id:
                docref.refNFe.valor = docref_obj.documentoreferenciado_id.chave or ''
                obs_ref += 'Referente à NF-e nº '
                obs_ref += formata_valor(docref_obj.documentoreferenciado_id.numero, casas_decimais=0)
                obs_ref += ' do dia '
                obs_ref += formata_data(docref_obj.documentoreferenciado_id.data_emissao)
                obs_ref += ', chave '
                obs_ref += docref_obj.documentoreferenciado_id.chave
                obs_ref += '\n'

            else:
                docref.refNFe.valor = docref_obj.chave or ''
                obs_ref += 'Referente a NF-e chave '
                obs_ref += docref_obj.chave
                obs_ref += '\n'

        elif docref_obj.modelo == '57':
            if docref_obj.documentoreferenciado_id:
                docref.refCTe.valor = docref_obj.documentoreferenciado_id.chave or ''
            else:
                docref.refCTe.valor = docref_obj.chave or ''

        elif docref_obj.modelo in ['01', '1B']:
            # nf avulsa
            pass

        elif docref_obj.modelo == '04':
            # nf de produtor rural
            pass

        else:
            docref.refECF.mod.valor = docref_obj.modelo or '2D'
            docref.refECF.nECF.valor = docref_obj.numero_ecf or ''
            docref.refECF.nCOO.valor = docref_obj.numero_coo or 0

        nfe.infNFe.ide.NFref.append(docref)

    #
    # Emitente
    #
    nfe.infNFe.emit.CNPJ.valor  = limpa_formatacao(empresa.cnpj_cpf)
    nfe.infNFe.emit.xNome.valor = empresa.razao_social
    nfe.infNFe.emit.xFant.valor = empresa.fantasia
    nfe.infNFe.emit.enderEmit.xLgr.valor    = empresa.endereco
    nfe.infNFe.emit.enderEmit.nro.valor     = empresa.numero
    nfe.infNFe.emit.enderEmit.xCpl.valor    = empresa.complemento or ''
    nfe.infNFe.emit.enderEmit.xBairro.valor = empresa.bairro
    nfe.infNFe.emit.enderEmit.cMun.valor    = empresa.municipio_id.codigo_ibge[:7]
    nfe.infNFe.emit.enderEmit.xMun.valor    = empresa.municipio_id.nome
    nfe.infNFe.emit.enderEmit.UF.valor      = empresa.municipio_id.estado_id.uf
    nfe.infNFe.emit.enderEmit.CEP.valor     = limpa_formatacao(empresa.cep)
    #nfe.infNFe.emit.enderEmit.cPais.valor   = '1058'
    #nfe.infNFe.emit.enderEmit.xPais.valor   = 'Brasil'
    nfe.infNFe.emit.enderEmit.fone.valor    = limpa_formatacao(empresa.fone or '')
    nfe.infNFe.emit.IE.valor = limpa_formatacao(empresa.ie)
    nfe.infNFe.emit.CRT.valor = doc_obj.regime_tributario[0]  # Trata o código interno 3.1 para lucro real

    #
    # Destinatário
    #
    if doc_obj.partner_id.municipio_id.estado_id.uf == 'EX':
        #print('estrangeiro')
        nfe.infNFe.ide.idDest.valor = '3'
        #
        # Participantes estrangeiros não se preenche o CNPJ
        #
        nfe.infNFe.dest.idEstrangeiro.valor = limpa_formatacao(doc_obj.partner_id.cnpj_cpf)

    elif len(doc_obj.partner_id.cnpj_cpf) == 14:
        nfe.infNFe.dest.CPF.valor = limpa_formatacao(doc_obj.partner_id.cnpj_cpf)

    else:
        nfe.infNFe.dest.CNPJ.valor = limpa_formatacao(doc_obj.partner_id.cnpj_cpf)

    if processador.ambiente == 2:
        nfe.infNFe.dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
    else:
        nfe.infNFe.dest.xNome.valor = doc_obj.partner_id.razao_social

    nfe.infNFe.dest.enderDest.xLgr.valor    = doc_obj.partner_id.endereco

    if not doc_obj.partner_id.numero:
        raise osv.except_osv(u'Erro!', u'Endereço do cliente sem número!')

    nfe.infNFe.dest.enderDest.nro.valor     = doc_obj.partner_id.numero
    nfe.infNFe.dest.enderDest.xCpl.valor    = doc_obj.partner_id.complemento or ''
    nfe.infNFe.dest.enderDest.xBairro.valor = doc_obj.partner_id.bairro

    if doc_obj.partner_id.municipio_id.estado_id.uf == 'EX':
        nfe.infNFe.dest.enderDest.cMun.valor  = doc_obj.partner_id.municipio_id.codigo_ibge[:7]
        nfe.infNFe.dest.enderDest.xMun.valor  = doc_obj.partner_id.municipio_id.nome
        nfe.infNFe.dest.enderDest.UF.valor    = doc_obj.partner_id.municipio_id.estado_id.uf
        nfe.infNFe.dest.enderDest.CEP.valor   = '99999999'
        nfe.infNFe.dest.enderDest.cPais.valor = doc_obj.partner_id.municipio_id.pais_id.codigo_bacen
        nfe.infNFe.dest.enderDest.xPais.valor = doc_obj.partner_id.municipio_id.pais_id.nome
    else:
        nfe.infNFe.dest.enderDest.cMun.valor  = doc_obj.partner_id.municipio_id.codigo_ibge[:7]
        nfe.infNFe.dest.enderDest.xMun.valor  = doc_obj.partner_id.municipio_id.nome
        nfe.infNFe.dest.enderDest.UF.valor    = doc_obj.partner_id.municipio_id.estado_id.uf
        nfe.infNFe.dest.enderDest.CEP.valor   = limpa_formatacao(doc_obj.partner_id.cep)

        if nfe.infNFe.dest.enderDest.UF.valor == nfe.infNFe.emit.enderEmit.UF.valor:
            nfe.infNFe.ide.idDest.valor = '1'
        else:
            nfe.infNFe.ide.idDest.valor = '2'

    nfe.infNFe.dest.enderDest.fone.valor    = limpa_formatacao(doc_obj.partner_id.fone or '')
    email_dest = doc_obj.partner_id.email_nfe or ''
    nfe.infNFe.dest.email.valor = email_dest[:60]

    nfe.infNFe.dest.indIEDest.valor = doc_obj.partner_id.contribuinte or '9'

    if doc_obj.partner_id.municipio_id.estado_id.uf == 'EX':
        pass
    elif doc_obj.partner_id.contribuinte and doc_obj.partner_id.contribuinte == '1':
        if not valida_inscricao_estadual(doc_obj.partner_id.ie or '', nfe.infNFe.dest.enderDest.UF.valor):
            raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

        nfe.infNFe.dest.IE.valor = limpa_formatacao(doc_obj.partner_id.ie or '')

    #
    # Zera os valores para somar ao preencher os itens
    #
    nfe.infNFe.total.ICMSTot.vBC.valor     = '0.00'
    nfe.infNFe.total.ICMSTot.vICMS.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vICMSDeson.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vFCPUFDest.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vICMSUFDest.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vICMSUFRemet.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vBCST.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vST.valor     = '0.00'
    nfe.infNFe.total.ICMSTot.vProd.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vFrete.valor  = '0.00'
    nfe.infNFe.total.ICMSTot.vSeg.valor    = '0.00'
    nfe.infNFe.total.ICMSTot.vDesc.valor   = '0.00'
    nfe.infNFe.total.ICMSTot.vII.valor     = '0.00'
    nfe.infNFe.total.ICMSTot.vIPI.valor    = '0.00'
    nfe.infNFe.total.ICMSTot.vPIS.valor    = '0.00'
    nfe.infNFe.total.ICMSTot.vCOFINS.valor = '0.00'
    nfe.infNFe.total.ICMSTot.vOutro.valor  = '0.00'
    nfe.infNFe.total.ICMSTot.vNF.valor     = '0.00'

    #
    # Detalhe
    #
    i = 0
    item = None
    al_diferencial_aliquota = 0
    for item in doc_obj.documentoitem_ids:
        d = Det_310()

        if item.al_diferencial_aliquota and (al_diferencial_aliquota == 0):
            al_diferencial_aliquota = item.al_diferencial_aliquota

        i += 1
        d.nItem.valor = i
        d.prod.cProd.valor    = item.produto_id.code or str(item.produto_id.id)
        d.prod.cEAN.valor     = item.produto_id.ean13 or ''

        if item.produto_descricao:
            d.prod.xProd.valor    = item.produto_descricao.strip()
        else:
            d.prod.xProd.valor    = item.produto_id.name

        d.prod.NCM.valor      = item.produto_id.ncm_id.codigo
        d.prod.EXTIPI.valor   = item.produto_id.ncm_id.ex or ''
        d.prod.CFOP.valor     = item.cfop_id.codigo
        d.prod.uCom.valor     = item.produto_id.uom_id.name[0:4] # O nome da unidade de medida no open tem mais de 4 caracteres
        d.prod.qCom.valor     = D('%.4f' % item.quantidade)
        d.prod.vUnCom.valor   = D('%.10f' % item.vr_unitario)
        d.prod.vProd.valor    = D('%.2f' % item.vr_produtos)
        d.prod.cEANTrib.valor = ''
        d.prod.uTrib.valor    = d.prod.uCom.valor
        d.prod.qTrib.valor    = d.prod.qCom.valor
        d.prod.vUnTrib.valor  = d.prod.vUnCom.valor
        d.prod.vFrete.valor   = D('%.2f' % item.vr_frete)
        d.prod.vSeg.valor     = D('%.2f' % item.vr_seguro)
        d.prod.vOutro.valor   = D('%.2f' % item.vr_outras)
        d.prod.vDesc.valor    = D('%.2f' % item.vr_desconto)
        d.prod.xPed.valor     = item.numero_pedido or ''
        d.prod.nItemPed.valor = item.numero_item_pedido or ''

        if item.compoe_total:
            d.prod.indTot.valor = '1'

            nfe.infNFe.total.ICMSTot.vBC.valor          += D('%.2f' % item.bc_icms_proprio)
            nfe.infNFe.total.ICMSTot.vICMS.valor        += D('%.2f' % item.vr_icms_proprio)
            #nfe.infNFe.total.ICMSTot.vICMSDeson.valor   += D('1.00')
            #nfe.infNFe.total.ICMSTot.vFCPUFDest.valor   += D('1.00')
            #nfe.infNFe.total.ICMSTot.vICMSUFDest.valor  += D('1.00')
            #nfe.infNFe.total.ICMSTot.vICMSUFRemet.valor += D('1.00')
            nfe.infNFe.total.ICMSTot.vBCST.valor        += D('%.2f' % item.bc_icms_st)
            nfe.infNFe.total.ICMSTot.vST.valor          += D('%.2f' % item.vr_icms_st)
            nfe.infNFe.total.ICMSTot.vProd.valor        += D('%.2f' % item.vr_produtos)
            nfe.infNFe.total.ICMSTot.vFrete.valor       += D('%.2f' % item.vr_frete)
            nfe.infNFe.total.ICMSTot.vSeg.valor         += D('%.2f' % item.vr_seguro)
            nfe.infNFe.total.ICMSTot.vDesc.valor        += D('%.2f' % item.vr_desconto)
            nfe.infNFe.total.ICMSTot.vII.valor          += D('%.2f' % item.vr_ii)
            nfe.infNFe.total.ICMSTot.vIPI.valor         += D('%.2f' % item.vr_ipi)
            nfe.infNFe.total.ICMSTot.vPIS.valor         += D('%.2f' % item.vr_pis_proprio)
            nfe.infNFe.total.ICMSTot.vCOFINS.valor      += D('%.2f' % item.vr_cofins_proprio)
            nfe.infNFe.total.ICMSTot.vOutro.valor       += D('%.2f' % item.vr_outras)
            nfe.infNFe.total.ICMSTot.vNF.valor          += D('%.2f' % item.vr_nf)

        else:
            d.prod.indTot.valor = '0'

        #
        # Declaração de Importação
        #

        if getattr(item, 'declaracao_ids', False):
            for di_obj in item.declaracao_ids:
                di = DI_310()
                di.nDI.valor = di_obj.numero_documento
                di.dDI.valor = di_obj.data_registro[:10]
                di.xLocDesemb.valor = di_obj.local_desembaraco
                di.UFDesemb.valor = di_obj.uf_desembaraco.uf
                di.dDesemb.valor = di_obj.data_desembaraco[:10]
                di.tpViaTransp.valor = di_obj.via_trans_internacional
                di.vAFRMM.valor = D('%.2f' % di_obj.vr_afrmm) or '0.00'
                di.tpIntermedio.valor = di_obj.forma_importacao

                if di_obj.partner_id:
                    di.CNPJ.valor = limpa_formatacao(di_obj.partner_id.cnpj_cpf)
                    di.UFTerceiro.valor = di_obj.partner_id.estado
                    di.cExportador.valor = limpa_formatacao(di_obj.partner_id.cnpj_cpf)

                for adi_obf in di_obj.declaracao_adicao_ids:
                    adi = Adi_310()
                    adi.nAdicao.valor = adi_obf.numero_adicao
                    adi.nSeqAdic.valor = adi_obf.sequencial

                    if di_obj.partner_id:
                        adi.cFabricante.valor = limpa_formatacao(di_obj.partner_id.cnpj_cpf)

                    adi.vDescDI.valor = D('%.2f' % adi_obf.vr_desconto) or '0.00'
                    adi.nDraw.valor = adi_obf.numero_drawback

                    di.adi.append(adi)


                d.prod.DI.append(di)
        #
        # Impostos
        #

        #
        # ICMS comum
        #
        d.imposto.ICMS.regime_tributario = nfe.infNFe.emit.CRT.valor
        d.imposto.ICMS.orig.valor     = item.org_icms
        d.imposto.ICMS.CST.valor      = item.cst_icms

        #
        # ICMS SIMPLES
        #
        if doc_obj.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            d.imposto.ICMS.CSOSN.valor = item.cst_icms_sn
            d.imposto.ICMS.pCredSN.valor = D('%.2f' % item.al_icms_sn)
            d.imposto.ICMS.vCredICMSSN.valor = D('%.2f' % item.vr_icms_sn)

        d.imposto.ICMS.modBC.valor    = item.md_icms_proprio
        d.imposto.ICMS.pRedBC.valor   = D('%.2f' % item.rd_icms_proprio)
        d.imposto.ICMS.vBC.valor      = D('%.2f' % item.bc_icms_proprio)
        d.imposto.ICMS.pICMS.valor    = D('%.2f' % item.al_icms_proprio)
        d.imposto.ICMS.vICMS.valor    = D('%.2f' % item.vr_icms_proprio)
        d.imposto.ICMS.modBCST.valor  = item.md_icms_st
        d.imposto.ICMS.pMVAST.valor   = D('%.2f' % item.pr_icms_st)
        d.imposto.ICMS.pRedBCST.valor = D('%.2f' % item.rd_icms_st)
        d.imposto.ICMS.vBCST.valor    = D('%.2f' % item.bc_icms_st)
        d.imposto.ICMS.pICMSST.valor  = D('%.2f' % item.al_icms_st)
        d.imposto.ICMS.vICMSST.valor  = D('%.2f' % item.vr_icms_st)
        #d.imposto.ICMS.motDesICMS.valor =
        #d.imposto.ICMS.vBCSTRet.valor   = D('%.2f' % item.bc_icms_st_retido)
        #d.imposto.ICMS.vICMSSTRet.valor = D('%.2f' % item.vr_icms_st_retido)
        #d.imposto.ICMS.vBCSTDest.valor =
        #d.imposto.ICMS.vICMSSTDest.valor =
        #d.imposto.ICMS.UFST.valor =
        #d.imposto.ICMS.pBCOp.valor =

        if item.cst_icms not in ST_ICMS_CALCULA_PROPRIO and item.cst_icms_sn not in ST_ICMS_SN_CALCULA_PROPRIO:
            d.imposto.ICMS.pICMS.valor = D(0)

        if doc_obj.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if item.cst_icms_sn in ST_ICMS_CODIGO_CEST:
                if item.produto_id.cest_id:
                    d.prod.CEST.valor = item.produto_id.cest_id.codigo or ''

                elif item.produto_id.ncm_id and item.produto_id.ncm_id.cest_ids:
                    d.prod.CEST.valor = item.produto_id.ncm_id.cest_ids[0].codigo or ''

        else:
            if item.cst_icms in ST_ICMS_CODIGO_CEST:
                if item.produto_id.cest_id:
                    d.prod.CEST.valor = item.produto_id.cest_id.codigo or ''

                elif item.produto_id.ncm_id and item.produto_id.ncm_id.cest_ids:
                    d.prod.CEST.valor = item.produto_id.ncm_id.cest_ids[0].codigo or ''

        #
        # IPI
        #
        if (doc_obj.regime_tributario != REGIME_TRIBUTARIO_SIMPLES) and item.cst_ipi:
            d.imposto.IPI.CST.valor    = item.cst_ipi or ''
            d.imposto.IPI.vBC.valor    = D('%.2f' % item.bc_ipi)
            #d.imposto.IPI.qUnid.valor  = D('%.4f' % item.quantidade_tributacao)
            #d.imposto.IPI.vUnid.valor  = D('%.4f' % item.al_ipi)
            d.imposto.IPI.pIPI.valor   = D('%.2f' % item.al_ipi)
            d.imposto.IPI.vIPI.valor   = D('%.2f' % item.vr_ipi)
        else:
            d.imposto.IPI.CST.valor    = ''

        #
        # PIS e COFINS
        #
        d.imposto.PIS.CST.valor        = item.cst_pis
        d.imposto.PIS.vBC.valor        = D('%.2f' % item.bc_pis_proprio)
        d.imposto.PIS.pPIS.valor       = D('%.2f' % item.al_pis_proprio)
        d.imposto.PIS.vPIS.valor       = D('%.2f' % item.vr_pis_proprio)
        d.imposto.COFINS.CST.valor     = item.cst_cofins
        d.imposto.COFINS.vBC.valor     = D('%.2f' % item.bc_cofins_proprio)
        d.imposto.COFINS.pCOFINS.valor = D('%.2f' % item.al_cofins_proprio)
        d.imposto.COFINS.vCOFINS.valor = D('%.2f' % item.vr_cofins_proprio)

        #
        # Imposto de importação
        #
        d.imposto.II.vBC.valor = D('%.2f' % item.bc_ii)
        d.imposto.II.vII.valor = D('%.2f' % item.vr_ii)
        d.imposto.II.vDespAdu.valor = D('%.2f' % item.vr_despesas_aduaneiras)
        d.imposto.II.vIOF.valor = D('%.2f' % item.vr_iof)

        #
        # Aplica um template na observação do item
        #
        infcomplementar = item.infcomplementar or ''

        dados = {
            'nf': doc_obj,
            'doc_obj': doc_obj,
            'item': item,
            'item_obj': item,
            'al_diferencial_aliquota': al_diferencial_aliquota
        }
        template = Template(infcomplementar.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
        infcomplementar = template.render(**dados)
        d.infAdProd.valor = infcomplementar.decode('utf-8')

        #
        # Inclui o detalhe na NF-e
        #
        nfe.infNFe.det.append(d)

    #
    # Transporte e frete
    #
    nfe.infNFe.transp.modFrete.valor = doc_obj.modalidade_frete or 9

    if doc_obj.transportadora_id:
        if len(doc_obj.transportadora_id.cnpj_cpf) == 14:
            nfe.infNFe.transp.transporta.CPF.valor = limpa_formatacao(doc_obj.transportadora_id.cnpj_cpf)
        else:
            nfe.infNFe.transp.transporta.CNPJ.valor = limpa_formatacao(doc_obj.transportadora_id.cnpj_cpf)

        nfe.infNFe.transp.transporta.xNome.valor = doc_obj.transportadora_id.razao_social or doc_obj.transportadora_id.name or ''
        nfe.infNFe.transp.transporta.IE.valor = limpa_formatacao(doc_obj.transportadora_id.ie or 'ISENTO')
        ender = doc_obj.transportadora_id.endereco or ''
        ender += ' '
        ender += doc_obj.transportadora_id.numero or ''
        ender += ' '
        ender += doc_obj.transportadora_id.complemento or ''
        nfe.infNFe.transp.transporta.xEnder.valor = ender.strip()
        nfe.infNFe.transp.transporta.xMun.valor = doc_obj.transportadora_id.cidade or ''
        nfe.infNFe.transp.transporta.UF.valor = doc_obj.transportadora_id.estado or ''

    if doc_obj.veiculo_id:
        nfe.infNFe.transp.veicTransp.placa.valor = doc_obj.veiculo_id.placa or ''
        nfe.infNFe.transp.veicTransp.UF.valor = doc_obj.veiculo_id.estado_id.uf or ''
        nfe.infNFe.transp.veicTransp.RNTC.valor = doc_obj.veiculo_id.rntrc or ''

    nfe.infNFe.transp.reboque = []
    if doc_obj.reboque1_id:
        reb = Reboque_310()
        reb.placa.valor = doc_obj.reboque1_id.placa or ''
        reb.UF.valor = doc_obj.reboque1_id.estado_id.uf or ''
        reb.RNTC.valor = doc_obj.reboque1_id.rntrc or ''
        nfe.infNFe.transp.reboque.append(reb)
    if doc_obj.reboque2_id:
        reb = Reboque_310()
        reb.placa.valor = doc_obj.reboque2_id.placa or ''
        reb.UF.valor = doc_obj.reboque2_id.estado_id.uf or ''
        reb.RNTC.valor = doc_obj.reboque2_id.rntrc or ''
        nfe.infNFe.transp.reboque.append(reb)
    if doc_obj.reboque3_id:
        reb = Reboque_310()
        reb.placa.valor = doc_obj.reboque3_id.placa or ''
        reb.UF.valor = doc_obj.reboque3_id.estado_id.uf or ''
        reb.RNTC.valor = doc_obj.reboque3_id.rntrc or ''
        nfe.infNFe.transp.reboque.append(reb)
    if doc_obj.reboque4_id:
        reb = Reboque_310()
        reb.placa.valor = doc_obj.reboque4_id.placa or ''
        reb.UF.valor = doc_obj.reboque4_id.estado_id.uf or ''
        reb.RNTC.valor = doc_obj.reboque4_id.rntrc or ''
        nfe.infNFe.transp.reboque.append(reb)
    if doc_obj.reboque5_id:
        reb = Reboque_310()
        reb.placa.valor = doc_obj.reboque5_id.placa or ''
        reb.UF.valor = doc_obj.reboque5_id.estado_id.uf or ''
        reb.RNTC.valor = doc_obj.reboque5_id.rntrc or ''
        nfe.infNFe.transp.reboque.append(reb)

    #
    # Volumes
    #
    nfe.infNFe.transp.vol = []
    for volume_obj in doc_obj.volume_ids:
        vol = Vol_310()
        vol.qVol.valor = D(volume_obj.quantidade or 0)
        vol.esp.valor = volume_obj.especie or ''
        vol.marca.valor = volume_obj.marca or ''
        vol.nVol.valor = volume_obj.numero or ''
        vol.pesoL.valor = D(volume_obj.peso_liquido or 0).quantize(D('0.001'))
        vol.pesoB.valor = D(volume_obj.peso_bruto or 0).quantize(D('0.001'))
        nfe.infNFe.transp.vol.append(vol)

    #
    # Duplicatas
    #
    if doc_obj.forma_pagamento in [FORMA_PAGAMENTO_A_VISTA, FORMA_PAGAMENTO_A_PRAZO]:
        nfe.infNFe.cobr.fat.nFat.valor = formata_valor(doc_obj.numero, casas_decimais=0)
        nfe.infNFe.cobr.fat.vOrig.valor = D('%.2f' % doc_obj.vr_operacao)
        nfe.infNFe.cobr.fat.vDesc.valor = D('%.2f' % doc_obj.vr_desconto)
        nfe.infNFe.cobr.fat.vLiq.valor = D('%.2f' % doc_obj.vr_fatura)

        for dup_obj in doc_obj.duplicata_ids:
            dup = Dup_310()
            dup.nDup.valor = dup_obj.numero
            dup.dVenc.valor = parse_datetime(dup_obj.data_vencimento).date()
            dup.vDup.valor = D('%.2f' % dup_obj.valor)
            nfe.infNFe.cobr.dup.append(dup)

    #
    # Informação complementar
    #
    infcomplementar = doc_obj.infcomplementar or ''
    dados = {
        'nf': doc_obj,
        'doc_obj': doc_obj,
        'item': item,
        'item_obj': item,
        'al_diferencial_aliquota': al_diferencial_aliquota,
        'uf_origem': empresa.municipio_id.estado_id.uf,
        'uf_destino': doc_obj.partner_id.municipio_id.estado_id.uf,
    }


    #
    # Diferencial de alíquota
    #
    vr_diferencial_aliquota = doc_obj.vr_diferencial_aliquota or 0
    if nfe.infNFe.ide.dhEmi.valor.year == 2016:
        dados['vr_diferencial_aliquota_uf_origem'] = D(str(vr_diferencial_aliquota)) * D('0.6')
        dados['vr_diferencial_aliquota_uf_destino'] = D(str(vr_diferencial_aliquota)) * D('0.4')
    elif nfe.infNFe.ide.dhEmi.valor.year == 2017:
        dados['vr_diferencial_aliquota_uf_origem'] = D(str(vr_diferencial_aliquota)) * D('0.4')
        dados['vr_diferencial_aliquota_uf_destino'] = D(str(vr_diferencial_aliquota)) * D('0.6')
    elif nfe.infNFe.ide.dhEmi.valor.year == 2018:
        dados['vr_diferencial_aliquota_uf_origem'] = D(str(vr_diferencial_aliquota)) * D('0.2')
        dados['vr_diferencial_aliquota_uf_destino'] = D(str(vr_diferencial_aliquota)) * D('0.8')
    elif nfe.infNFe.ide.dhEmi.valor.year >= 2019:
        dados['vr_diferencial_aliquota_uf_origem'] = 0
        dados['vr_diferencial_aliquota_uf_destino'] = D(str(vr_diferencial_aliquota))

    #
    # Acresenta a observação do diferencial de alíquota
    #
    if (doc_obj.partner_id.municipio_id.estado_id.uf != empresa.municipio_id.estado_id.uf) \
        and al_diferencial_aliquota and doc_obj.operacao_id.calcula_diferencial_aliquota:
        infcomplementar += u'\nVenda a consumidor final conf. emenda constitucional 87/2015; valor DIFAL para ${ uf_origem } = R$ ${ formata_valor(vr_diferencial_aliquota_uf_origem) }; valor DIFAL para ${ uf_destino } = R$ ${ formata_valor(vr_diferencial_aliquota_uf_destino) }'

    template = Template(infcomplementar.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
    infcomplementar = template.render(**dados)
    nfe.infNFe.infAdic.infCpl.valor = infcomplementar.decode('utf-8')

    if obs_ref:
        nfe.infNFe.infAdic.infCpl.valor += u'\n' + obs_ref

    #
    # Informação adicional para o fisco
    #
    infadfisco = doc_obj.infadfisco or ''
    dados = {
        'nf': doc_obj,
        'doc_obj': doc_obj,
        'item': item,
        'item_obj': item,
    }
    template = Template(infadfisco.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
    infadfisco = template.render(**dados)
    nfe.infNFe.infAdic.infAdFisco.valor = infadfisco.decode('utf-8')

    nfe.gera_nova_chave()

    doc_obj.write({'chave': nfe.chave})

    #
    # Gera o DANFE da nota
    #
    processador.danfe.NFe = nfe
    processador.danfe.salvar_arquivo = False
    processador.danfe.gerar_danfe()
    nfe.pdf = processador.danfe.conteudo_pdf

    return nfe


def envia_nfe(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)
    nfe = monta_nfe(self, cr, uid, doc_obj)

    processador.danfe.NFe = nfe
    processador.danfe.salvar_arquivo = False
    processador.danfe.gerar_danfe()
    grava_nfe(self, cr, uid, doc_obj, nfe)
    grava_danfe(self, cr, uid, doc_obj, nfe, processador.danfe.conteudo_pdf)

    #
    # Envia a nota
    #
    processo = None
    for p in processador.processar_notas([nfe]):
        processo = p
        #print(processo, processo.webservice)
        #print(processo.envio.xml)
        #print(processo.resposta.xml)

    grava_nfe(self, cr, uid, doc_obj, nfe)

    #
    # Se o último processo foi a consulta do status do serviço, significa que
    # ele não está online...
    #
    if processo.webservice == WS_NFE_SITUACAO:
        res = doc_obj.write({'state': 'em_digitacao'})
        return res

    #
    # Se o último processo foi a consulta da nota, significa que ela já está
    # emitida
    #
    elif processo.webservice == WS_NFE_CONSULTA:
        if processo.resposta.cStat.valor in ('100', '150'):
            res = doc_obj.write({'state': 'autorizada'})
            return res

        elif processo.resposta.cStat.valor in ('110', '301', '302'):
            res = doc_obj.write({'state': 'denegada'})
            return res

        else:
            res = doc_obj.write({'state': 'em_digitacao'})
            return res

    #
    # Se o último processo foi o envio do lote, significa que a consulta falhou
    # mas o envio não
    #
    elif processo.webservice == WS_NFE_ENVIO_LOTE:
        res = doc_obj.write({'state': 'em_digitacao'})
        return res

    #
    # Se o último processo foi o retorno do recibo, a nota foi rejeitada,
    # denegada, autorizada, ou ainda não tem resposta
    #
    elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
        #
        # Consulta ainda sem resposta, a nota ainda não foi processada
        #
        if processo.resposta.cStat.valor == '105':
            res = doc_obj.write({'state': 'enviada'})
            return res

        #
        # Lote processado
        #
        elif processo.resposta.cStat.valor == '104':
            if processo.resposta.dic_protNFe[nfe.chave].infProt.cStat.valor in ('100', '150'):
                grava_procnfe(self, cr, uid, doc_obj, nfe, processo.resposta.dic_procNFe[nfe.chave])
                grava_danfe(self, cr, uid, doc_obj, nfe, processo.resposta.dic_procNFe[nfe.chave].danfe_pdf)

                data_autorizacao = processo.resposta.dic_protNFe[nfe.chave].infProt.dhRecbto.valor
                #print(data_autorizacao)
                data_autorizacao = UTC.normalize(data_autorizacao)
                #print(data_autorizacao)

                res = doc_obj.write({'state': 'autorizada', 'data_autorizacao': data_autorizacao})
                return res

            elif processo.resposta.dic_protNFe[nfe.chave].infProt.cStat.valor in ('110', '301', '302'):
                grava_procnfe(self, cr, uid, doc_obj, nfe, processo.resposta.dic_procNFe[nfe.chave])
                grava_danfe(self, cr, uid, doc_obj, nfe, processo.resposta.dic_procNFe[nfe.chave].danfe_pdf)
                res = doc_obj.write({'state': 'denegada'})
                return res

            else:
                #grava_nfe(self, cr, uid, doc_obj, processo.resposta.dic_NFe[nfe.chave])
                #grava_danfe(self, cr, uid, doc_obj, nfe, processador.danfe.conteudo_pdf)
                mensagem = u'Código de retorno: ' + processo.resposta.protNFe[0].infProt.cStat.valor
                mensagem += '\nMensagem: ' + processo.resposta.protNFe[0].infProt.xMotivo.valor
                res = doc_obj.write({'resposta_nfse': mensagem, 'state': 'rejeitada'})
                return res

        else:
            #
            # Rejeitada por outros motivos, falha no schema etc. etc.
            #
            #grava_nfe(self, cr, uid, doc_obj, processo.resposta.dic_NFe[nfe.chave])
            #grava_danfe(self, cr, uid, doc_obj, nfe, processador.danfe.conteudo_pdf)
            mensagem = u'Código de retorno: ' + processo.resposta.cStat.valor
            mensagem += '\nMensagem: ' + processo.resposta.xMotivo.valor
            res = doc_obj.write({'resposta_nfse': mensagem, 'state': 'rejeitada'})
            return res


def grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo='application/xml', tabela='sped.documento'):
    dados = {
        b'datas': base64.encodestring(conteudo_arquivo),
        b'name': nome_arquivo,
        b'datas_fname': nome_arquivo,
        b'res_model': tabela,
        b'res_id': doc_obj.id,
        b'file_type': tipo_arquivo,
        #'lock': True,
        }

    lista_documentos_id = self.pool.get('ir.attachment').search(cr, uid, args=[
        (b'res_model', '=', tabela),
        (b'res_id', '=', doc_obj.id),
        (b'name', '=', nome_arquivo),
        ])

    #
    # Se um arquivo com o mesmo nome já existia, sobrepoe
    #
    if lista_documentos_id:
        self.pool.get('ir.attachment').write(cr, uid, lista_documentos_id, dados)
        anexo = lista_documentos_id

    else:
        anexo = self.pool.get('ir.attachment').create(cr, uid, dados)

    cr.commit()
    return anexo


def le_arquivo(self, cr, uid, doc_nfe, nome_arquivo, tabela='sped.documento'):
    lista_documentos_id = self.pool.get('ir.attachment').search(cr, uid, args=[
        ('res_model', '=', tabela),
        ('res_id', '=', doc_nfe.id),
        ('name', '=', nome_arquivo),
        ])

    arq = None
    if lista_documentos_id:
        anexo = self.pool.get('ir.attachment').browse(cr, uid, lista_documentos_id[0])
        arq = base64.decodestring(anexo.datas).decode('utf-8')

    return arq

def grava_nfe(self, cr, uid, doc_obj, nfe, tabela='sped.documento'):
    nome_arquivo = nfe.chave + '-nfe.xml'
    conteudo_arquivo = nfe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo, tabela=tabela)
    return anexo

def grava_procnfe(self, cr, uid, doc_obj, nfe, procNFe, tabela='sped.documento'):
    nome_arquivo = nfe.chave + '-proc-nfe.xml'
    conteudo_arquivo = procNFe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo, tabela=tabela)
    return anexo

def grava_protnfe(self, cr, uid, doc_obj, nfe, protNFe, tabela='sped.documento'):
    nome_arquivo = nfe.chave + '-prot-nfe.xml'
    conteudo_arquivo = protNFe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo, tabela=tabela)
    return anexo

def grava_danfe(self, cr, uid, doc_obj, nfe, danfe_pdf, tabela='sped.documento'):
    nome_arquivo = nfe.chave + '.pdf'
    conteudo_arquivo = danfe_pdf
    tipo_arquivo = 'application/pdf'

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo, tabela=tabela)
    return anexo

def grava_daede(self, cr, uid, doc_obj, nfe, daede_pdf, tabela='sped.documento'):
    nome_arquivo = 'eventos-' + nfe.chave + '.pdf'
    conteudo_arquivo = daede_pdf
    tipo_arquivo = 'application/pdf'

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo, tabela=tabela)
    return anexo

def cancela_nfe(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)
    xml = le_arquivo(self, cr, uid, doc_obj, doc_obj.chave + '-proc-nfe.xml')

    if 'versao="2.00"' in xml:
        procNFe = ProcNFe_200()
    else:
        procNFe = ProcNFe_310()

    procNFe.xml = xml
    procNFe.NFe.monta_chave()

    evento = EventoCancNFe_100()
    evento.infEvento.tpAmb.valor = procNFe.NFe.infNFe.ide.tpAmb.valor
    evento.infEvento.cOrgao.valor = procNFe.NFe.chave[:2]
    evento.infEvento.CNPJ.valor = procNFe.NFe.infNFe.emit.CNPJ.valor
    evento.infEvento.chNFe.valor = procNFe.NFe.chave
    evento.infEvento.dhEvento.valor = agora()
    evento.infEvento.detEvento.nProt.valor = procNFe.protNFe.infProt.nProt.valor
    evento.infEvento.detEvento.xJust.valor = doc_obj.motivo_cancelamento or ''

    processador.salvar_arquivo = True
    processo = processador.enviar_lote_cancelamento(lista_eventos=[evento])

    #print(processo)
    #print(processo.envio.xml)
    #print(processo.resposta.xml)

    #procevento = ProcEventoCancNFe_100()
    #procevento.xml = '/home/integra/sped/comercio/nfe/producao/2014-09/001-000009688/42140901729489000108550010000096881416778827-01-proc-can.xml'

    #
    # O cancelamento foi aceito e vinculado à NF-e
    #
    if doc_obj.chave in processo.resposta.dic_procEvento:
        procevento = processo.resposta.dic_procEvento[doc_obj.chave]
        #
        # Grava o protocolo de cancelamento
        #
        nome_arquivo = doc_obj.chave + '-01-proc-can.xml'
        conteudo_arquivo = procevento.xml.encode('utf-8')
        tipo_arquivo = 'application/xml'

        anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo)

        #
        # Regera o DANFE com a tarja de cancelamento
        #
        processador.danfe.NFe = procNFe.NFe
        processador.danfe.protNFe = procNFe.protNFe
        processador.danfe.procEventoCancNFe = procevento
        processador.danfe.salvar_arquivo = False
        processador.danfe.gerar_danfe()
        grava_danfe(self, cr, uid, doc_obj, procNFe.NFe, processador.danfe.conteudo_pdf)
        processador.danfe.NFe = NFe_310()
        processador.danfe.protNFe = None
        processador.danfe.procEventoCancNFe = None

        #
        # Cancelamento extemporâneo
        #
        if procevento.retEvento.infEvento.cStat.valor == '155':
            doc_obj.write({'state': 'cancelada', 'situacao': SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO})
        else:
            doc_obj.write({'state': 'cancelada', 'situacao': SITUACAO_FISCAL_CANCELADO})

def corrige_nfe(self, cr, uid, cce_obj, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)

    xml = le_arquivo(self, cr, uid, doc_obj, doc_obj.chave + '-proc-nfe.xml')

    if 'versao="2.00"' in xml:
        procNFe = ProcNFe_200()
    else:
        procNFe = ProcNFe_310()

    procNFe.xml = le_arquivo(self, cr, uid, doc_obj, doc_obj.chave + '-proc-nfe.xml')
    procNFe.NFe.monta_chave()

    evento = EventoCCe_100()
    evento.infEvento.tpAmb.valor = procNFe.NFe.infNFe.ide.tpAmb.valor
    evento.infEvento.cOrgao.valor = procNFe.NFe.chave[:2]
    evento.infEvento.CNPJ.valor = procNFe.NFe.infNFe.emit.CNPJ.valor
    evento.infEvento.chNFe.valor = procNFe.NFe.chave
    evento.infEvento.dhEvento.valor = agora()
    #
    # Correção ASP - Cláudia copiou e colou e veio esse caracter esquisito
    #
    if cce_obj.correcao:
        cce_obj.correcao = cce_obj.correcao.replace(u'\u200b', ' ')

    evento.infEvento.detEvento.xCorrecao.valor = cce_obj.correcao or ''
    evento.infEvento.nSeqEvento.valor = cce_obj.sequencia or 1

    processador.salvar_arquivo = True
    processo = processador.enviar_lote_cce(lista_eventos=[evento])
    #print(processo)
    #print(processo.envio.xml)
    #print(processo.resposta.xml)

    #
    # A CC-e foi aceita e vinculada à NF-e
    #
    if doc_obj.chave in processo.resposta.dic_procEvento:
        procevento = processo.resposta.dic_procEvento[doc_obj.chave]
        #
        # Grava o protocolo de cancelamento
        #
        nome_arquivo = doc_obj.chave + '-' + str(cce_obj.sequencia).zfill(2) + '-proc-cce.xml'
        conteudo_arquivo = procevento.xml.encode('utf-8')
        tipo_arquivo = 'application/xml'

        anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo)

        #
        # Regera o DAEDE com a nova CC-e
        #
        processador.daede.NFe = procNFe.NFe
        processador.daede.protNFe = procNFe.protNFe
        processador.daede.procEventos = [procevento]
        processador.daede.salvar_arquivo = False
        processador.daede.gerar_daede()
        grava_daede(self, cr, uid, doc_obj, procNFe.NFe, processador.daede.conteudo_pdf)
        processador.daede.NFe = NFe_310()
        processador.daede.protNFe = None
        processador.daede.procEventos = []

def gera_danfe(self, cr, uid, doc_obj):
    #
    # Verifica os xmls anexos
    #
    chave = doc_obj.chave or ''
    nome_nfe = chave + '-nfe.xml'
    nome_procnfe = chave + '-proc-nfe.xml'
    nome_proccan = chave + '-01-proc-can.xml'

    nfe_xml = le_arquivo(self, cr, uid, doc_obj, nome_nfe)

    if nfe_xml is None:
        nfe = monta_nfe(self, cr, uid, doc_obj)
    else:
        nfe = NFe_310()
        nfe.xml = nfe_xml

    procnfe_xml = le_arquivo(self, cr, uid, doc_obj, nome_procnfe)
    proccanc_xml = le_arquivo(self, cr, uid, doc_obj, nome_proccan)

    #
    # Regera o DANFE, com a tarja de cancelamento se for o caso
    #
    if nfe:
        processador.danfe.NFe = nfe
    else:
        processador.danfe.NFe = NFe_310()

    if procnfe_xml:
        procnfe = ProcNFe_310()
        procnfe.xml = procnfe_xml
        processador.danfe.protNFe = procnfe.protNFe
    else:
        processador.danfe.protNFe = None

    if proccanc_xml:
        proccanc = ProcEventoCancNFe_100()
        proccanc.xml = proccanc_xml
        processador.danfe.procEventoCancNFe = proccanc
    else:
        processador.danfe.procEventoCancNFe = None

    processador.danfe.salvar_arquivo = False

    empresa = doc_obj.company_id.partner_id
    caminho_empresa = os.path.expanduser('~/sped')

    if not empresa.cnpj_cpf:
        #
        # Pega a empresa ativa no momento
        #
        empresa_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento')
        empresa = self.pool.get('res.company').browse(cr, uid, empresa_id)
        empresa = empresa.partner_id

    caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf))

    if os.path.exists(os.path.join(caminho_empresa, 'logo_caminho.txt')):
        processador.danfe.logo = open(os.path.join(caminho_empresa, 'logo_caminho.txt')).read().strip()

    processador.danfe.gerar_danfe()
    grava_danfe(self, cr, uid, doc_obj, nfe, processador.danfe.conteudo_pdf)

regs = []

def consulta_cadastro_empresa(self, cr, uid, partner_obj):
    if not partner_obj.cnpj_cpf:
        return

    if 'EX' in partner_obj.cnpj_cpf:
        return

    if partner_obj.estado and partner_obj.estado == 'EX':
        return

    processador = prepara_certificado(self, cr, uid, partner_obj)
    processador.ambiente = 1  # consultas devem ser feitas em produção

    #
    # A consulta deve ser feita no estado do cliente, e não da empresa
    #
    estado = processador.estado
    if partner_obj.estado and partner_obj.estado != processador.estado:
        estado = partner_obj.estado

    processador.estado = estado
    processo = processador.consultar_cadastro(estado=estado, cnpj_cpf=limpa_formatacao(partner_obj.cnpj_cpf))
    #print(processo)
    #print(processo.envio.xml)
    #print(processo.resposta.xml)
    #print(processo.resposta.original)

    if not '<cStat>111</cStat>' in processo.resposta.original:
        raise osv.except_osv(u'Erro!', u"Cadastro não encontrado no estado %s! A empresa pode não ser contribuinte do ICMS. Se for, tente informar ou trocar a cidade do cadastro, e refaça a consulta." % estado)

    cad = processo.resposta.infCons.infCad[0]
    dados = {
        'razao_social': cad.xNome.valor,
        'ie': cad.IE.valor,
        'contribuinte': '1',
        'endereco': cad.ender.xLgr.valor,
        'numero': cad.ender.nro.valor,
        'complemento': cad.ender.xCpl.valor,
        'bairro': cad.ender.xBairro.valor,
        'cep': str(cad.ender.CEP.valor).zfill(8),
    }

    cnae_ids = self.pool.get('sped.cnae').search(cr, uid, [('codigo', '=', cad.CNAE.valor)])
    if len(cnae_ids):
        dados['cnae_id'] = cnae_ids[0]

    municipio_ids = self.pool.get('sped.municipio').search(cr, uid, [('codigo_ibge', '=', str(cad.ender.cMun.valor) + '0000')])
    if len(municipio_ids):
        dados['municipio_id'] = municipio_ids[0]

    if cad.xRegApur.valor not in regs:
        regs.append(cad.xRegApur.valor)

    if 'SIMPLES' in cad.xRegApur.valor.upper() or 'SIMEI' in cad.xRegApur.valor.upper():
        dados['regime_tributario'] = REGIME_TRIBUTARIO_SIMPLES
    else:
        dados['regime_tributario'] = REGIME_TRIBUTARIO_NORMAL

    #print(dados)
    partner_obj.write(dados)
    cr.commit()
    #print(cad.xNome.valor, cad.xRegApur.valor, regs)


def inutiliza_numeracao(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)

    cnpj = limpa_formatacao(doc_obj.company_id.partner_id.cnpj_cpf)
    serie = str(doc_obj.serie or '')
    numero = doc_obj.numero
    motivo = doc_obj.motivo_cancelamento or u'AVANÇO NÃO PREVISTO NO CONTROLE DE NUMERAÇÃO DE NOTAS NO SISTEMA INFORMATIZADO'

    processo = processador.inutilizar_nota(cnpj=cnpj, serie=serie, numero_inicial=numero, justificativa=motivo)
    #print(processo)
    #print(processo.envio.xml)
    #print(processo.resposta.xml)
    #print(processo.resposta.original)

    #
    # A CC-e foi aceita e vinculada à NF-e
    #
    if '<cStat>102</cStat>' in processo.resposta.original:
        procinut = processo.processo_inutilizacao_nfe

        chave = processo.envio.chave

        dados = {
            'chave': chave,
            'state': 'inutilizada',
        }

        doc_obj.write(dados)

        #
        # Grava o protocolo de cancelamento
        #
        nome_arquivo = chave + '-proc-inu.xml'
        conteudo_arquivo = procinut.xml.encode('utf-8')
        tipo_arquivo = 'application/xml'

        anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo, tipo_arquivo)


def importa_nota_avulsa(self, cr, uid, ids, context={}):
    attachment_pool = self.pool.get('ir.attachment')

    for nota_obj in self.browse(cr, uid, ids, context=context):
        anexo_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sped.documento'), ('res_id', '=', nota_obj.id), ('name', 'ilike', '.xml'), ('datas', '!=', False)])
        for anexo_obj in attachment_pool.browse(cr, uid, anexo_ids):
            xml = base64.decodestring(anexo_obj.datas).decode('utf-8').replace('\n', '').replace('\r', '')

            if '<procEmi>1</procEmi>' not in xml:
                continue

            if '<cStat>100</cStat>' not in xml:
                continue

            nfe = ProcNFe_310()
            nfe.xml = xml

            chave = nfe.protNFe.infProt.chNFe.valor
            nfe.NFe.chave = chave
            nfe.chave = chave

            data_autorizacao = nfe.protNFe.infProt.dhRecbto.valor
            data_autorizacao = UTC.normalize(data_autorizacao)

            cr.execute("update sped_documento set state = 'autorizada', data_autorizacao = '{data_autorizacao}', chave = '{chave}' where id = {id};".format(id=nota_obj.id, data_autorizacao=data_autorizacao, chave=chave))

            nota_obj.chave = chave
            grava_nfe(self, cr, uid, nota_obj, nfe)
            grava_procnfe(self, cr, uid, nota_obj, nfe.NFe, nfe)
            gera_danfe(self, cr, uid, nota_obj)

