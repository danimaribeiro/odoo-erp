# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from StringIO import StringIO
#from ....base import gera_assinatura, tira_abertura
from ...nfse import *
#from .servico_enviar_lote_rps_envio_v01 import *
#from .servico_enviar_lote_rps_envio_v01 import parseString as parse_lote_rps
#from .servico_consultar_lote_rps_envio_v01 import parseString as parse_lote_nfse
#from decimal import Decimal as D
from ....participante import REGIME_TRIBUTARIO_SIMPLES
from .....base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario, UnicodeBrasil, tira_acentos
from ....base import Signature, gera_assinatura


def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    lote_rps = DicionarioBrasil()
    lote_rps['__versao'] = '2.01'
    lote_rps['NumeroLote'] = numero_lote

    cnpj = DicionarioBrasil()
    cnpj['Cnpj'] = prestador.cnpj_cpf_numero
    lote_rps['CpfCnpj'] = cnpj
    lote_rps['InscricaoMunicipal'] = prestador.im or '0'

    #lote_rps['InscricaoMunicipal'] = int(prestador.im or 0)
    lote_rps['QuantidadeRps'] = len(lista_notas)
    lote_rps['ListaRps'] = []

    for nota in lista_notas:
        rps = DicionarioBrasil()
        rps['InfDeclaracaoPrestacaoServico'] = DicionarioBrasil()
        infrps = rps.InfDeclaracaoPrestacaoServico

        infrps['__Id'] = 'R' + str(nota.rps.numero)

        infrps['Rps'] = DicionarioBrasil()
        infrps.Rps['IdentificacaoRps'] = DicionarioBrasil()
        infrps.Rps.IdentificacaoRps['Numero'] = str(nota.rps.numero)
        infrps.Rps.IdentificacaoRps['Serie'] = 'RPS' # nota.rps.serie
        infrps.Rps.IdentificacaoRps['Tipo'] = str(nota.rps.tipo + 1)
        infrps.Rps['DataEmissao'] = nota.rps.data_hora_emissao.isoformat()[:10]
        infrps.Rps['Status'] = 2 if nota.cancelada else 1
        infrps['Competencia'] = nota.rps.data_hora_emissao.isoformat()[:10]
        #infrps['NaturezaOperacao'] = nota.natureza_operacao + 1
        #InfRps.RegimeEspecialTributacao =
        #infrps['OptanteSimplesNacional'] = 1 if nota.prestador.optante_simples_nacional else 2
        #infrps['IncentivadorCultural'] = 1 if nota.prestador.incentivador_cultural else 2

        if nota.nfse_substituida.numero != 0:
            infrps['RpsSubstituido'] = DicionarioBrasil()
            infrps.RpsSubstituido['Numero'] = nota.nfse_substituida.numero
            infrps.RpsSubstituido['Serie'] = nota.nfse_substituida.serie
            #infrps.RpsSubstituido['tipo'] = nota.nfse_substituida.tipo + 1

        #
        # Serviço
        #
        infrps['Servico'] = DicionarioBrasil()
        servico = infrps.Servico

        servico['Valores'] = DicionarioBrasil()
        valores = servico.Valores
        valores['ValorServicos'] = nota.valor.servico
        valores['ValorDeducoes'] = nota.valor.deducao or '0.00'
        valores['ValorPis'] = nota.valor.retido.pis or '0.00'
        valores['ValorCofins'] = nota.valor.retido.cofins or '0.00'
        valores['ValorInss'] = nota.valor.retido.inss or '0.00'
        valores['ValorIr'] = nota.valor.retido.ir or '0.00'
        valores['ValorCsll'] = nota.valor.retido.csll or '0.00'

        if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores['ValorIss'] = '0.00'
            valores['OutrasRetencoes'] = nota.valor.retido.outras or '0.00'
            valores['Aliquota'] = '0.00'

        else:
            valores['ValorIss'] = nota.valor.vr_iss or '0.00'
            valores['OutrasRetencoes'] = nota.valor.retido.outras or '0.00'
            #valores['BaseCalculo'] = nota.valor.bc_iss or None
            valores['Aliquota'] = nota.valor.al_iss or '0.00'
            #valores['ValorLiquidoNfse'] = nota.valor.liquido or None
        valores['DescontoIncondicionado'] = nota.valor.desconto_incondicionado or '0.00'
        valores['DescontoCondicionado'] = nota.valor.desconto_condicionado or '0.00'
        #servico['ValorIssRetido'] = nota.valor.retido.iss or None

        servico['IssRetido'] = 1 if nota.valor.retido.iss != 0 else 2
        servico['ItemListaServico'] = nota.servico.codigo.zfill(4)
        #infrps.Servico.CodigoCnae = nota.servico.codigo
        #infrps.Servico.CodigoTributacaoMunicipio = nota.servico.codigo
        servico['Discriminacao'] = nota.descricao.replace('\n', ';').strip()

        if servico.Discriminacao[0:2] == '- ':
            servico.Discriminacao = servico.Discriminacao[2:]

        if nota.municipio_fato_gerador and nota.municipio_fato_gerador.codigo_ibge:
            servico['CodigoMunicipio'] = nota.municipio_fato_gerador.codigo_ibge
        elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
            servico['CodigoMunicipio'] = nota.tomador.municipio.codigo_ibge
        else:
            servico['CodigoMunicipio'] = nota.prestador.municipio.codigo_ibge

        servico['ExigibilidadeISS'] = '1'

        #
        # Prestador
        #
        infrps['Prestador'] = DicionarioBrasil()
        infrps.Prestador['CpfCnpj'] = DicionarioBrasil()
        infrps.Prestador.CpfCnpj['Cnpj'] = nota.prestador.cnpj_cpf_numero
        infrps.Prestador['InscricaoMunicipal'] = nota.prestador.im or '0'

        #
        # Tomador
        #
        infrps['Tomador'] = DicionarioBrasil()

        if nota.tomador.tipo_pessoa in ('PF', 'PJ'):
            infrps.Tomador['IdentificacaoTomador'] = DicionarioBrasil()
            infrps.Tomador.IdentificacaoTomador['CpfCnpj'] = DicionarioBrasil()
            if nota.tomador.tipo_pessoa == 'PF':
                infrps.Tomador.IdentificacaoTomador.CpfCnpj['Cpf'] = nota.tomador.cnpj_cpf_numero
            else:
                infrps.Tomador.IdentificacaoTomador.CpfCnpj['Cnpj'] = nota.tomador.cnpj_cpf_numero

        infrps.Tomador['RazaoSocial'] = nota.tomador.nome.strip()
        infrps.Tomador['Endereco'] = DicionarioBrasil()
        infrps.Tomador.Endereco['Endereco'] = nota.tomador.endereco.strip()
        infrps.Tomador.Endereco['Numero'] = nota.tomador.numero.strip()
        infrps.Tomador.Endereco['Complemento'] = nota.tomador.complemento.strip() or None
        infrps.Tomador.Endereco['Bairro'] = nota.tomador.bairro.strip()
        infrps.Tomador.Endereco['CodigoMunicipio'] = nota.tomador.municipio.codigo_ibge
        infrps.Tomador.Endereco['Uf'] = nota.tomador.estado.uf
        infrps.Tomador.Endereco['Cep'] = nota.tomador.cep_numero.strip()

        #if nota.tomador.fone or nota.tomador.email:
            #infrps.Tomador['Contato'] = DicionarioBrasil()
            #infrps.Tomador.Contato['Telefone'] = nota.tomador.fone_numero.strip() or None
            #infrps.Tomador.Contato['Email'] = nota.tomador.email.strip() or None

        infrps['RegimeEspecialTributacao'] = '1'
        infrps['OptanteSimplesNacional'] = '1' if nota.prestador.regime_tributario == REGIME_TRIBUTARIO_SIMPLES else '2'
        infrps['IncentivoFiscal'] = '2'

        #infrps['IntermediarioServico'] = DicionarioBrasil()
        #infrps['ConstrucaoCivil'] = DicionarioBrasil()
        #infrps['OutrasInformacoes'] = DicionarioBrasil()

        #if nota.condicao_pagamento == 'A VISTA':
            #infrps['CondicaoPagamento'] = DicionarioBrasil()
            #infrps.CondicaoPagamento['Condicao'] = 'A_VISTA'
            #infrps.CondicaoPagamento['QtdParcela'] = 1
            #infrps.CondicaoPagamento['Parcelas'] = DicionarioBrasil()
            #infrps.CondicaoPagamento.Parcelas['Parcela'] = 1
            #infrps.CondicaoPagamento.Parcelas['DataVencimento'] = nota.rps.data_emissao_iso
            #infrps.CondicaoPagamento.Parcelas['Valor'] = nota.valor.liquido

        #else:
            #infrps['CondicaoPagamento'] = DicionarioBrasil()
            #infrps.CondicaoPagamento['Condicao'] = 'A_PRAZO'
            #infrps.CondicaoPagamento['QtdParcela'] = len(nota.parcelas)
            #infrps.CondicaoPagamento['Parcelas'] = []
            #for parcela in nota.parcelas:
                #parc = DicionarioBrasil()
                #parc['Parcela'] = parcela.numero
                #parc['DataVencimento'] = parcela.data_vencimento_formatada
                #parc['Valor'] = parcela.valor
                #infrps.CondicaoPagamento.Parcelas.append(parc)

        rps_raiz = DicionarioBrasil()
        rps_raiz['Rps'] = rps

        assinatura = gera_assinatura(URI='#' + infrps.__Id)
        rps_raiz.Rps['Signature'] = assinatura
        if certificado:
            certificado.doctype = '<!DOCTYPE Rps [<!ATTLIST InfDeclaracaoPrestacaoServico Id ID #IMPLIED>]>'

            #print(rps_raiz.como_xml_em_texto)

            rps_assinado = certificado.assina_xml(tira_acentos(rps_raiz.como_xml_em_texto))

            ##
            ## Para João Pessoa, tem que tirar o Id do RPS
            ##
            #rps_assinado = rps_assinado.replace('URI="#R' + str(nota.rps.numero) + '"', 'URI=""')
            #rps_assinado = rps_assinado.replace(' Id="R' + str(nota.rps.numero) + '"', '')

            rps_raiz = xml_para_dicionario(rps_assinado)

        lote_rps.ListaRps.append(rps_raiz)

    raiz = DicionarioBrasil()
    raiz['EnviarLoteRpsEnvio'] = DicionarioBrasil()
    enviarloterpsenvio = raiz.EnviarLoteRpsEnvio
    enviarloterpsenvio['__xmlns'] = 'http://www.abrasf.org.br/nfse.xsd'
    #enviarloterpsenvio['__xmlns:jp'] = 'http://www.abrasf.org.br/nfse.xsd'
    enviarloterpsenvio['LoteRps'] = lote_rps

    lote_rps['__Id'] = 'L' + str(lote_rps.NumeroLote)
    enviarloterpsenvio['Signature'] = gera_assinatura(URI='#' + lote_rps.__Id)
    certificado.doctype = '<!DOCTYPE EnviarLoteRpsEnvio [<!ATTLIST LoteRps Id ID #IMPLIED>]>'
    raiz = certificado.assina_xml(raiz, sem_acentos=True)

    tags_inclui_ns = [
        'EnviarLoteRpsEnvio', 'LoteRps', 'NumeroLote', 'CpfCnpj', 'Cnpj', 'Cpf', 'QuantidadeRps', 'ListaRps', 'Rps',
        'InfDeclaracaoPrestacaoServico', 'IdentificacaoRps', 'Numero', 'Serie', 'Tipo', 'DataEmissao', 'Status',
        'Competencia', 'Servico', 'Valores', 'ValorServicos', 'ValorPis', 'ValorCofins', 'ValorInss', 'ValorIr',
        'ValorCsll', 'ValorIss', 'Aliquota', 'IssRetido', 'ItemListaServico', 'Discriminacao', 'CodigoMunicipio',
        'ExigibilidadeISS', 'Prestador', 'InscricaoMunicipal', 'Tomador', 'IdentificacaoTomador', 'RazaoSocial',
        'Endereco', 'Bairro', 'Uf', 'Cep', 'RegimeEspecialTributacao', 'OptanteSimplesNacional', 'IncentivoFiscal']

    res = raiz.como_xml_em_texto

    ##
    ## Para João Pessoa, tem que tirar o Id do RPS
    ##
    #res = res.replace('URI="#L' + str(lote_rps.NumeroLote) + '"', 'URL=""')
    #res = res.replace(' Id="L' + str(lote_rps.NumeroLote) + '"', '')

    #for tag in tags_inclui_ns:
        #res = res.replace('<' + tag, '<jp:' + tag)
        #res = res.replace('</' + tag, '</jp:' + tag)

    return res


def gera_consulta_situacao_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarSituacaoLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarSituacaoLoteRpsEnvio
    consultarps['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps['Protocolo'] = protocolo

    return raiz.como_xml_em_texto


def gera_consulta_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarLoteRpsEnvio
    consultarps['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps['Protocolo'] = protocolo

    return raiz.como_xml_em_texto


def le_envio_lote_rps(xml):
    envio_lote_rps = xml_para_dicionario(xml)
    lote_rps = envio_lote_rps.EnviarLoteRpsEnvio.LoteRps
    numero_lote = lote_rps.NumeroLote

    if isinstance(lote_rps.ListaRps, DicionarioBrasil):
        lote_rps.ListaRps = [lote_rps.ListaRps]

    lista_notas = []
    for item_rps in lote_rps.ListaRps:
        rps = item_rps.Rps

        nota = NFSe()
        Prestador = infrps.Prestador
        Tomador = infrps.Tomador

        #
        # Prestador
        #
        nota.prestador.cnpj_cpf = unicode(getattr(Prestador, 'Cnpj', '') or '') or unicode(getattr(Prestador, 'Cpf', '') or '')
        nota.prestador.im = unicode(getattr(Prestador, 'InscricaoMunicipal', '') or '')

        if getattr(infrps, 'OptanteSimplesNacional', 2) == 1:
            nota.prestador.regime_tributario = REGIME_TRIBUTARIO_SIMPLES

        nota.prestador.incentivador_cultural = getattr(infrps, 'IncentivadorCultural', 2) == 1

        #
        # Tomador
        #
        if hasattr(Tomador, 'IdentificacaoTomador') and hasattr(Tomador.IdentificacaoTomador, 'CpfCnpj'):
            nota.tomador.cnpj_cpf = unicode(getattr(Tomador.IdentificacaoTomador.CpfCnpj, 'Cnpj', '') or '') or unicode(getattr(Tomador.IdentificacaoTomador.CpfCnpj, 'Cpf', '') or '')

        nota.tomador.nome = unicode(getattr(Tomador, 'RazaoSocial', '') or '')

        if hasattr(Tomador, 'Endereco'):
            nota.tomador.endereco = unicode(getattr(Tomador.Endereco, 'Endereco', '') or '')
            nota.tomador.numero = unicode(getattr(Tomador.Endereco, 'Numero', '') or '')
            nota.tomador.complemento = unicode(getattr(Tomador.Endereco, 'Complemento', '') or '')
            nota.tomador.bairro = unicode(getattr(Tomador.Endereco, 'Bairro', ''))
            nota.tomador.estado = unicode(getattr(Tomador.Endereco, 'Uf', ''))
            nota.tomador.municipio = unicode(getattr(Tomador.Endereco, 'CodigoMunicipio', '')).zfill(7)
            nota.tomador.cep = unicode(getattr(Tomador.Endereco, 'Cep', ''))

        if hasattr(Tomador, 'Contato'):
            nota.tomador.fone = unicode(getattr(Tomador.Contato, 'Telefone', ''))
            nota.tomador.email = unicode(getattr(Tomador.Contato, 'Email', ''))

        #
        # Dados do RPS/Nota
        #
        if hasattr(infrps, 'IdentificacaoRps'):
            nota.rps.numero = getattr(infrps.IdentificacaoRps, 'Numero', 0)
            nota.rps.serie = unicode(getattr(infrps.IdentificacaoRps, 'Serie', ''))
            nota.rps.tipo = (getattr(infrps.IdentificacaoRps, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        nota.rps.data_hora_emissao = getattr(infrps, 'DataEmissao', None)
        nota.natureza_operacao = (getattr(infrps, 'NaturezaOperacao', UnicodeBrasil('1')).inteiro - 1) or 0
        #infrps.RegimeEspecialTributacao =
        nota.cancelada = getattr(infrps, 'Status', '2') == '1'
        #infrps.OutrasInformacoes =

        if hasattr(infrps, 'RpsSubstituido'):
            nota.nfse_substituida.numero = getattr(infrps.RpsSubstituido, 'Numero', UnicodeBrasil('0')).inteiro
            nota.nfse_substituida.serie = unicode(getattr(infrps.RpsSubstituido, 'Serie', ''))
            nota.nfse_substituida.tipo = (getattr(infrps.RpsSubstituido, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        #
        # Serviço
        #
        Servico = infrps.Servico
        nota.valor.servico = D(getattr(Servico.Valores, 'ValorServicos', '0'))
        nota.valor.deducao = D(getattr(Servico.Valores, 'ValorDeducoes', '0'))
        nota.valor.desconto_incondicionado = D(getattr(Servico.Valores, 'DescontoIncondicionado', '0'))
        nota.valor.bc_iss = D(getattr(Servico.Valores, 'BaseCalculo', '0'))
        nota.valor.al_iss = D(getattr(Servico.Valores, 'Aliquota', '0')) * 100
        nota.valor.vr_iss = D(getattr(Servico.Valores, 'ValorIss', '0'))
        nota.valor.retido.iss = D(getattr(Servico.Valores, 'ValorIssRetido', '0'))
        nota.valor.retido.pis = D(getattr(Servico.Valores, 'ValorPis', '0'))
        nota.valor.retido.cofins = D(getattr(Servico.Valores, 'ValorCofins', '0'))
        nota.valor.retido.inss = D(getattr(Servico.Valores, 'ValorInss', '0'))
        nota.valor.retido.ir = D(getattr(Servico.Valores, 'ValorIr', '0'))
        nota.valor.retido.csll = D(getattr(Servico.Valores, 'ValorCsll', '0'))
        nota.valor.retido.outras = D(getattr(Servico.Valores, 'OutrasRetencoes', '0'))
        nota.valor.desconto_condicionado = D(getattr(Servico.Valores, 'DescontoCondicionado', '0'))
        nota.valor.liquido = D(getattr(Servico.Valores, 'ValorLiquidoNfse', '0'))

        nota.servico = unicode(getattr(Servico, 'ItemListaServico', '') or '')
        #infrps.Servico.CodigoCnae = nota.servico.codigo
        #infrps.Servico.CodigoTributacaoMunicipio = nota.servico.codigo
        nota.descricao = unicode(getattr(Servico, 'Discriminacao', '') or '')
        nota.municipio_fato_gerador = unicode(getattr(Servico, 'CodigoMunicipio', '') or '').zfill(7)

        lista_notas.append(nota)

    return lista_notas, numero_lote

def gera_cancelamento_nota(nota, certificado):
    raiz = DicionarioBrasil()
    raiz['CancelarNfseEnvio'] = DicionarioBrasil()
    cancelanota = raiz.CancelarNfseEnvio
    cancelanota['__xmlns:e'] = 'http://www.betha.com.br/e-nota-contribuinte-ws'
    cancelanota['Pedido'] = DicionarioBrasil()
    pedcanc = cancelanota.Pedido
    pedcanc['InfPedidoCancelamento'] = DicionarioBrasil()
    pedcanc.InfPedidoCancelamento['__Id'] = 'L' + str(nota.numero)
    pedcanc.InfPedidoCancelamento['IdentificacaoNfse'] = DicionarioBrasil()
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['Numero'] = str(nota.numero)
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['Cnpj'] = nota.prestador.cnpj_cpf_numero
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['InscricaoMunicipal'] = nota.prestador.im or '0'
    pedcanc.InfPedidoCancelamento.IdentificacaoNfse['CodigoMunicipio'] = nota.prestador.municipio.codigo_ibge
    pedcanc.InfPedidoCancelamento['CodigoCancelamento'] = '1'

    assinatura = gera_assinatura(URI='#' + pedcanc.InfPedidoCancelamento.__Id)
    pedcanc['Signature'] = assinatura

    if certificado:
        certificado.doctype = '<!DOCTYPE Pedido [<!ATTLIST InfPedidoCancelamento Id ID #IMPLIED>]>'
        raiz = certificado.assina_xml(raiz)
        print(raiz.como_xml_em_texto)

    return raiz.como_xml_em_texto
