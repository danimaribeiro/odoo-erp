# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import os
import base64
from decimal import Decimal as D
from pysped.nfe.processador_nfe import ProcessadorNFe
from pysped.nfe.webservices_flags import *
from pysped.nfe.leiaute import NFe_200, Det_200
from pybrasil.inscricao import limpa_formatacao


#
#
#
processador = ProcessadorNFe()
processador.danfe.nome_sistema = 'ERP Integra 6.1'
processador.danfe.site = 'http://www.ERPIntegra.com.br'


def envia_nfe(cursor, user_id, ids, registro_nfe):
    empresa = registro_nfe.company_id.partner_id
    caminho_empresa = os.path.expanduser('~/sped')
    caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf))

    processador.caminho = os.path.join(caminho_empresa, 'nfe')
    processador.estado  = empresa.municipio_id.estado_id.uf
    processador.ambiente = int(registro_nfe.ambiente_nfe)
    processador.contingencia_SCAN = registro_nfe.tipo_emissao_nfe != '1'

    processador.certificado.arquivo = open(os.path.join(caminho_empresa, 'certificado_caminho.txt')).read().strip()
    processador.certificado.senha   = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip()

    if os.path.exists(os.path.join(caminho_empresa, 'logo_caminho.txt')):
        processador.danfe.logo = open(os.path.join(caminho_empresa, 'logo_caminho.txt')).read().strip()

    #
    # Instancia uma NF-e
    #
    nfe = NFe_200()

    #
    # Identificação da NF-e
    #
    nfe.infNFe.ide.cUF.valor     = UF_CODIGO[processador.estado]
    nfe.infNFe.ide.natOp.valor   = registro_nfe.naturezaoperacao_id.nome
    nfe.infNFe.ide.indPag.valor  = registro_nfe.forma_pagamento
    nfe.infNFe.ide.serie.valor   = registro_nfe.serie
    nfe.infNFe.ide.nNF.valor     = registro_nfe.numero
    nfe.infNFe.ide.dEmi.valor    = registro_nfe.data_emissao
    nfe.infNFe.ide.dSaiEnt.valor = registro_nfe.data_entrada_saida or registro_nfe.data_emissao
    nfe.infNFe.ide.cMunFG.valor  = empresa.municipio_id.codigo_ibge[:7]
    nfe.infNFe.ide.tpImp.valor   = 1 # DANFE em retrato
    nfe.infNFe.ide.tpEmis.valor  = registro_nfe.tipo_emissao_nfe
    nfe.infNFe.ide.finNFe.valor  = registro_nfe.finalidade_nfe
    nfe.infNFe.ide.procEmi.valor = 0 # Emissão por aplicativo próprio
    nfe.infNFe.ide.verProc.valor = processador.danfe.nome_sistema

    #
    # Emitente (Confeitaria Day)
    #
    nfe.infNFe.emit.CNPJ.valor  = empresa.cnpj_cpf
    nfe.infNFe.emit.xNome.valor = empresa.nome
    nfe.infNFe.emit.xFant.valor = empresa.fantasia
    nfe.infNFe.emit.enderEmit.xLgr.valor    = empresa.endereco
    nfe.infNFe.emit.enderEmit.nro.valor     = empresa.numero
    nfe.infNFe.emit.enderEmit.xCpl.valor    = empresa.complemento or ''
    nfe.infNFe.emit.enderEmit.xBairro.valor = empresa.bairro
    nfe.infNFe.emit.enderEmit.cMun.valor    = empresa.municipio_id.codigo_ibge[:7]
    nfe.infNFe.emit.enderEmit.xMun.valor    = empresa.municipio_id.nome
    nfe.infNFe.emit.enderEmit.UF.valor      = empresa.municipio_id.estado_id.uf
    nfe.infNFe.emit.enderEmit.CEP.valor     = empresa.cep
    #nfe.infNFe.emit.enderEmit.cPais.valor   = '1058'
    #nfe.infNFe.emit.enderEmit.xPais.valor   = 'Brasil'
    nfe.infNFe.emit.enderEmit.fone.valor    = empresa.fone or ''
    nfe.infNFe.emit.IE.valor = empresa.ie
    nfe.infNFe.emit.CRT.valor = registro_nfe.regime_tributario

    #
    # Destinatário
    #
    if registro_nfe.participante_id.municipio_id.estado_id.uf == 'EX':
        #
        # Participantes estrangeiros não se preenche o CNPJ
        #
        print('estrangeiro')
        pass
    elif len(registro_nfe.participante_id.cnpj_cpf) == 11:
        nfe.infAdProd.dest.CPF.valor = registro_nfe.participante_id.cnpj_cpf
    else:
        nfe.infNFe.dest.CNPJ.valor  = registro_nfe.participante_id.cnpj_cpf

    if processador.ambiente == 2:
        nfe.infNFe.dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
    else:
        nfe.infNFe.dest.xNome.valor = registro_nfe.participante_id.nome

    nfe.infNFe.dest.enderDest.xLgr.valor    = registro_nfe.participante_id.endereco
    nfe.infNFe.dest.enderDest.nro.valor     = registro_nfe.participante_id.numero
    nfe.infNFe.dest.enderDest.xCpl.valor    = registro_nfe.participante_id.complemento or ''
    nfe.infNFe.dest.enderDest.xBairro.valor = registro_nfe.participante_id.bairro

    if registro_nfe.participante_id.municipio_id.estado_id.uf == 'EX':
        nfe.infNFe.dest.enderDest.cMun.valor  = registro_nfe.participante_id.municipio_id.codigo_ibge[:7]
        nfe.infNFe.dest.enderDest.xMun.valor  = registro_nfe.participante_id.municipio_id.nome
        nfe.infNFe.dest.enderDest.UF.valor    = registro_nfe.participante_id.municipio_id.estado_id.uf
        nfe.infNFe.dest.enderDest.CEP.valor   = '99999999'
        nfe.infNFe.dest.enderDest.cPais.valor = registro_nfe.participante_id.municipio_id.pais_id.codigo_ibge
        nfe.infNFe.dest.enderDest.xPais.valor = registro_nfe.participante_id.municipio_id.pais_id.nome
    else:
        nfe.infNFe.dest.enderDest.cMun.valor  = registro_nfe.participante_id.municipio_id.codigo_ibge[:7]
        nfe.infNFe.dest.enderDest.xMun.valor  = registro_nfe.participante_id.municipio_id.nome
        nfe.infNFe.dest.enderDest.UF.valor    = registro_nfe.participante_id.municipio_id.estado_id.uf
        nfe.infNFe.dest.enderDest.CEP.valor   = registro_nfe.participante_id.cep

    nfe.infNFe.dest.enderDest.fone.valor    = registro_nfe.participante_id.fone or ''
    nfe.infNFe.dest.email.valor = registro_nfe.participante_id.email_nfe or ''

    if registro_nfe.participante_id.municipio_id.estado_id.uf == 'EX':
        pass
    else:
        nfe.infNFe.dest.IE.valor = registro_nfe.participante_id.ie

    #
    # Zera os valores para somar ao preencher os itens
    #
    nfe.infNFe.total.ICMSTot.vBC.valor     = '0.00'
    nfe.infNFe.total.ICMSTot.vICMS.valor   = '0.00'
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
    for item in registro_nfe.documentoitem_ids:
        d = Det_200()

        i += 1
        d.nItem.valor = i
        d.prod.cProd.valor    = item.produto_id.product_id.code
        d.prod.cEAN.valor     = item.produto_id.product_id.ean13 or ''
        d.prod.xProd.valor    = item.produto_id.product_id.name
        d.prod.NCM.valor      = item.produto_id.ncm_id.codigo
        d.prod.EXTIPI.valor   = item.produto_id.ncm_id.ex or ''
        d.prod.CFOP.valor     = item.cfop_id.codigo
        d.prod.uCom.valor     = item.produto_id.product_id.uom_id.name[0:4] # O nome da unidade de medida no open tem mais de 4 caracteres
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

            nfe.infNFe.total.ICMSTot.vBC.valor     += D('%.2f' % item.bc_icms_proprio)
            nfe.infNFe.total.ICMSTot.vICMS.valor   += D('%.2f' % item.vr_icms_proprio)
            nfe.infNFe.total.ICMSTot.vBCST.valor   += D('%.2f' % item.bc_icms_st)
            nfe.infNFe.total.ICMSTot.vST.valor     += D('%.2f' % item.vr_icms_st)
            nfe.infNFe.total.ICMSTot.vProd.valor   += D('%.2f' % item.vr_produtos)
            nfe.infNFe.total.ICMSTot.vFrete.valor  += D('%.2f' % item.vr_frete)
            nfe.infNFe.total.ICMSTot.vSeg.valor    += D('%.2f' % item.vr_seguro)
            nfe.infNFe.total.ICMSTot.vDesc.valor   += D('%.2f' % item.vr_desconto)
            nfe.infNFe.total.ICMSTot.vII.valor     += D('%.2f' % item.vr_ii)
            nfe.infNFe.total.ICMSTot.vIPI.valor    += D('%.2f' % item.vr_ipi)
            nfe.infNFe.total.ICMSTot.vPIS.valor    += D('%.2f' % item.vr_pis_proprio)
            nfe.infNFe.total.ICMSTot.vCOFINS.valor += D('%.2f' % item.vr_cofins_proprio)
            nfe.infNFe.total.ICMSTot.vOutro.valor  += D('%.2f' % item.vr_outras)
            nfe.infNFe.total.ICMSTot.vNF.valor     += D('%.2f' % item.vr_nf)

        else:
            d.prod.indTot.valor = '0'

        #
        # Impostos
        #

        #
        # ICMS comum
        #
        d.imposto.ICMS.orig.valor     = item.org_icms
        d.imposto.ICMS.CST.valor      = item.cst_icms

        #
        # ICMS SIMPLES
        #
        if registro_nfe.regime_tributario == '1':
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
        d.imposto.ICMS.vBCSTRet.valor   = D('%.2f' % item.bc_icms_st_retido)
        d.imposto.ICMS.vICMSSTRet.valor = D('%.2f' % item.vr_icms_st_retido)
        #d.imposto.ICMS.vBCSTDest.valor =
        #d.imposto.ICMS.vICMSSTDest.valor =
        #d.imposto.ICMS.UFST.valor =
        #d.imposto.ICMS.pBCOp.valor =

        #
        # IPI
        #
        if item.cst_ipi:
            d.imposto.IPI.CST.valor    = item.cst_ipi or ''
            d.imposto.IPI.vBC.valor    = D('%.2f' % item.bc_ipi)
            d.imposto.IPI.qUnid.valor  = D('%.4f' % item.quantidade_tributacao)
            d.imposto.IPI.vUnid.valor  = D('%.4f' % item.al_ipi)
            d.imposto.IPI.pIPI.valor   = D('%.2f' % item.al_ipi)
            d.imposto.IPI.vIPI.valor   = D('%.2f' % item.vr_ipi)

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

        d.infAdProd.valor = item.infcomplementar or ''


        #
        # Inclui o detalhe na NF-e
        #
        nfe.infNFe.det.append(d)

    nfe.gera_nova_chave()

    registro_nfe.write({'chave': nfe.chave})

    processador.danfe.NFe= nfe
    processador.danfe.salvar_arquivo = False
    processador.danfe.gerar_danfe()
    grava_nfe(cursor, user_id, registro_nfe, nfe)
    grava_danfe(cursor, user_id, registro_nfe, nfe, processador.danfe.conteudo_pdf)

    #
    # Envia a nota
    #
    processo = None
    for p in processador.processar_notas([nfe]):
        processo = p
        #print(processo, processo.webservice)
        #print(processo.envio.xml)
        #print(processo.resposta.xml)

    grava_nfe(cursor, user_id, registro_nfe, nfe)

    #
    # Se o último processo foi a consulta do status do serviço, significa que
    # ele não está online...
    #
    if processo.webservice == WS_NFE_SITUACAO:
        return 'em_digitacao'

    #
    # Se o último processo foi a consulta da nota, significa que ela já está
    # emitida
    #
    elif processo.webservice == WS_NFE_CONSULTA:
        #print('aqui', processo.resposta.cStat.valor)
        if processo.resposta.cStat.valor in ('100', '150'):
            return 'autorizada'
        elif processo.resposta.cStat.valor in ('110', '301', '302'):
            return 'denegada'
        else:
            return 'em_digitacao'

    #
    # Se o último processo foi o envio do lote, significa que o envio falhou
    #
    elif processo.webservice == WS_NFE_ENVIO_LOTE:
        return 'em_digitacao'

    #
    # Se o último processo foi o retorno do recibo, a nota foi rejeitada,
    # denegada, autorizada, ou ainda não tem resposta
    #
    elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
        #
        # Consulta ainda sem resposta, a nota ainda não foi processada
        #
        if processo.resposta.cStat.valor == '105':
            return 'enviada'

        #
        # Lote processado
        #
        elif processo.resposta.cStat.valor == '104':
            if processo.resposta.dic_protNFe[nfe.chave].infProt.cStat.valor in ('100', '150'):
                grava_procnfe(cursor, user_id, registro_nfe, nfe, processo.resposta.dic_procNFe[nfe.chave])
                grava_danfe(cursor, user_id, registro_nfe, nfe, processo.resposta.dic_procNFe[nfe.chave].danfe_pdf)
                return 'autorizada'


            elif processo.resposta.dic_protNFe[nfe.chave].infProt.cStat.valor in ('110', '301', '302'):
                grava_procnfe(cursor, user_id, registro_nfe, nfe, processo.resposta.dic_procNFe[nfe.chave])
                grava_danfe(cursor, user_id, registro_nfe, nfe, processo.resposta.dic_procNFe[nfe.chave].danfe_pdf)
                return 'denegada'

            else:
                grava_nfe(cursor, user_id, registro_nfe, processo.resposta.dic_NFe[nfe.chave])
                grava_danfe(cursor, user_id, registro_nfe, nfe, processador.danfe.conteudo_pdf)
                return 'rejeitada'

        else:
                grava_nfe(cursor, user_id, registro_nfe, processo.resposta.dic_NFe[nfe.chave])
                grava_danfe(cursor, user_id, registro_nfe, nfe, processador.danfe.conteudo_pdf)
                return 'rejeitada'


def grava_arquivo(cursor, user_id, registro_nfe, nome_arquivo, conteudo_arquivo, tipo_arquivo):
    dados = {
        'datas': base64.encodestring(conteudo_arquivo),
        'name': nome_arquivo,
        'datas_fname': nome_arquivo,
        'res_model': 'sped.documento',
        'res_id': registro_nfe.id,
        'file_type': tipo_arquivo,
        #'lock': True,
        }

    lista_documentos_id = registro_nfe.pool.get('ir.attachment').search(cursor, user_id, args=[
        ('res_model', '=', 'sped.documento'),
        ('res_id', '=', registro_nfe.id),
        ('name', '=', nome_arquivo),
        ])

    #
    # Se um arquivo com o mesmo nome já existia, deletar antes
    #
    registro_nfe.pool.get('ir.attachment').unlink(cursor, user_id, lista_documentos_id)

    anexo = registro_nfe.pool.get('ir.attachment').create(cursor, user_id, dados)
    return anexo


def grava_nfe(cursor, user_id, registro_nfe, nfe):
    nome_arquivo = nfe.chave + '-nfe.xml'
    conteudo_arquivo = nfe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(cursor, user_id, registro_nfe, nome_arquivo, conteudo_arquivo, tipo_arquivo)
    return anexo

def grava_procnfe(cursor, user_id, registro_nfe, nfe, procNFe):
    nome_arquivo = nfe.chave + '-proc-nfe.xml'
    conteudo_arquivo = procNFe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(cursor, user_id, registro_nfe, nome_arquivo, conteudo_arquivo, tipo_arquivo)
    return anexo

def grava_protnfe(cursor, user_id, registro_nfe, nfe, protNFe):
    nome_arquivo = nfe.chave + '-prot-nfe.xml'
    conteudo_arquivo = protNFe.xml.encode('utf-8')
    tipo_arquivo = 'application/xml'

    anexo = grava_arquivo(cursor, user_id, registro_nfe, nome_arquivo, conteudo_arquivo, tipo_arquivo)
    return anexo

def grava_danfe(cursor, user_id, registro_nfe, nfe, danfe_pdf):
    nome_arquivo = nfe.chave + '.pdf'
    conteudo_arquivo = danfe_pdf
    tipo_arquivo = 'application/pdf'

    anexo = grava_arquivo(cursor, user_id, registro_nfe, nome_arquivo, conteudo_arquivo, tipo_arquivo)
    return anexo
