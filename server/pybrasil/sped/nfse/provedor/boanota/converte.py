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
from sped.constante_tributaria import *


def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    lote_rps = DicionarioBrasil()
    lote_rps['NumeroLote'] = numero_lote
    lote_rps['__Id'] = 'L' + str(lote_rps.NumeroLote)
    lote_rps['Cnpj'] = prestador.cnpj_cpf_numero
    lote_rps['InscricaoMunicipal'] = prestador.im
    lote_rps['QuantidadeRps'] = len(lista_notas)
    lote_rps['ListaRps'] = []

    for nota in lista_notas:
        rps = DicionarioBrasil()
        rps['InfRps'] = DicionarioBrasil()
        rps.InfRps['__Id'] = 'R' + str(nota.rps.numero)
        rps.InfRps['IdentificacaoRps'] = DicionarioBrasil()
        rps.InfRps.IdentificacaoRps['Numero'] = str(nota.rps.numero)
        rps.InfRps.IdentificacaoRps['Serie'] = nota.rps.serie
        rps.InfRps.IdentificacaoRps['Tipo'] = str(nota.rps.tipo + 1)
        rps.InfRps['DataEmissao'] = nota.rps.data_hora_emissao.isoformat()[:19]
        rps.InfRps['NaturezaOperacao'] = nota.natureza_operacao + 1
        #rps.InfRps.RegimeEspecialTributacao =
        rps.InfRps['OptanteSimplesNacional'] = 1 if nota.prestador.optante_simples_nacional else 2
        rps.InfRps['IncentivadorCultural'] = 1 if nota.prestador.incentivador_cultural else 2
        rps.InfRps['Status'] = 2 if nota.cancelada else 1

        if nota.nfse_substituida.numero != 0:
            rps.InfRps['RpsSubstituido'] = DicionarioBrasil()
            rps.InfRps.RpsSubstituido['Numero'] = nota.nfse_substituida.numero
            rps.InfRps.RpsSubstituido['Serie'] = nota.nfse_substituida.serie
            #rps.InfRps.RpsSubstituido['tipo'] = nota.nfse_substituida.tipo + 1

        #
        # Serviço
        #
        rps.InfRps['Servico'] = DicionarioBrasil()
        servico = rps.InfRps.Servico

        servico['Valores'] = DicionarioBrasil()
        valores = servico.Valores
        valores['ValorServicos'] = nota.valor.servico
        valores['ValorDeducoes'] = nota.valor.deducao or None
        valores['ValorPis'] = nota.valor.retido.pis or None
        valores['ValorCofins'] = nota.valor.retido.cofins or None
        valores['ValorInss'] = nota.valor.retido.inss or None
        valores['ValorIr'] = nota.valor.retido.ir or None
        valores['ValorCsll'] = nota.valor.retido.csll or None
        valores['IssRetido'] = 1 if nota.valor.retido.iss != 0 else 2
        valores['ValorIss'] = nota.valor.vr_iss or None
        valores['ValorIssRetido'] = nota.valor.retido.iss or None
        valores['OutrasRetencoes'] = nota.valor.retido.outras or None
        valores['BaseCalculo'] = nota.valor.bc_iss or None
        valores['Aliquota'] = nota.valor.al_iss / 100 or None
        valores['ValorLiquidoNfse'] = nota.valor.liquido or None
        valores['DescontoIncondicionado'] = nota.valor.desconto_incondicionado or None
        valores['DescontoCondicionado'] = nota.valor.desconto_condicionado or None

        servico['ItemListaServico'] = nota.servico.codigo.zfill(4)
        #rps.InfRps.Servico.CodigoCnae = nota.servico.codigo
        #rps.InfRps.Servico.CodigoTributacaoMunicipio = nota.servico.codigo
        servico['Discriminacao'] = nota.descricao.replace('\n', ';').strip()
        if nota.municipio_fato_gerador and nota.municipio_fato_gerador.codigo_ibge:
            servico['CodigoMunicipio'] = nota.municipio_fato_gerador.codigo_ibge
        elif nota.natureza_operacao == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
            servico['CodigoMunicipio'] = nota.tomador.municipio.codigo_ibge
        else:
            servico['CodigoMunicipio'] = nota.prestador.municipio.codigo_ibge

        #
        # Prestador
        #
        rps.InfRps['Prestador'] = DicionarioBrasil()
        rps.InfRps.Prestador['Cnpj'] = nota.prestador.cnpj_cpf_numero
        rps.InfRps.Prestador['InscricaoMunicipal'] = nota.prestador.im or '0'

        #
        # Tomador
        #
        rps.InfRps['Tomador'] = DicionarioBrasil()

        if nota.tomador.tipo_pessoa in ('PF', 'PJ'):
            rps.InfRps.Tomador['IdentificacaoTomador'] = DicionarioBrasil()
            rps.InfRps.Tomador.IdentificacaoTomador['CpfCnpj'] = DicionarioBrasil()
            if nota.tomador.tipo_pessoa == 'PF':
                rps.InfRps.Tomador.IdentificacaoTomador.CpfCnpj['Cpf'] = nota.tomador.cnpj_cpf_numero
            else:
                rps.InfRps.Tomador.IdentificacaoTomador.CpfCnpj['Cnpj'] = nota.tomador.cnpj_cpf_numero

        rps.InfRps.Tomador['RazaoSocial'] = nota.tomador.nome.strip()
        rps.InfRps.Tomador['Endereco'] = DicionarioBrasil()
        rps.InfRps.Tomador.Endereco['Endereco'] = nota.tomador.endereco.strip()
        rps.InfRps.Tomador.Endereco['Numero'] = nota.tomador.numero.strip()
        rps.InfRps.Tomador.Endereco['Complemento'] = nota.tomador.complemento.strip() or None
        rps.InfRps.Tomador.Endereco['Bairro'] = nota.tomador.bairro.strip()
        rps.InfRps.Tomador.Endereco['CodigoMunicipio'] = nota.tomador.municipio.codigo_ibge
        rps.InfRps.Tomador.Endereco['Uf'] = nota.tomador.estado.uf
        rps.InfRps.Tomador.Endereco['Cep'] = nota.tomador.cep_numero.strip()

        if nota.tomador.fone or nota.tomador.email:
            rps.InfRps.Tomador['Contato'] = DicionarioBrasil()
            rps.InfRps.Tomador.Contato['Telefone'] = nota.tomador.fone_numero.strip() or None
            rps.InfRps.Tomador.Contato['Email'] = nota.tomador.email.strip() or None

        #rps.InfRps['IntermediarioServico'] = DicionarioBrasil()
        #rps.InfRps['ConstrucaoCivil'] = DicionarioBrasil()
        #rps.InfRps['OutrasInformacoes'] = DicionarioBrasil()
        #rps.InfRps['CondicaoPagamento'] = DicionarioBrasil()

        assinatura = gera_assinatura(URI='#' + rps.InfRps.__Id)
        rps_raiz = DicionarioBrasil()
        rps_raiz['Rps'] = rps
        rps_raiz.Rps['Signature'] = assinatura

        if certificado:
            certificado.doctype = '<!DOCTYPE Rps [<!ATTLIST InfRps Id ID #IMPLIED>]>'
            rps_assinado = certificado.assina_xml(tira_acentos(rps_raiz.como_xml_em_texto))
            ##print(rps_assinado)
            rps_raiz = xml_para_dicionario(rps_assinado)
            #print(rps_raiz.como_xml_em_texto)

        lote_rps.ListaRps.append(rps_raiz)

    #print(lote_rps.como_xml_em_texto)
    raiz = DicionarioBrasil()
    raiz['EnviarLoteRpsEnvio'] = DicionarioBrasil()
    enviarloterpsenvio = raiz.EnviarLoteRpsEnvio
    enviarloterpsenvio['__xmlns'] = 'http://isscuritiba.curitiba.pr.gov.br/iss/nfse.xsd'
    enviarloterpsenvio['__xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    #enviarloterpsenvio['__xsi:schemaLocation'] = 'http://isscuritiba.curitiba.pr.gov.br/iss/nfse.xsd'
    enviarloterpsenvio['LoteRps'] = lote_rps
    enviarloterpsenvio['Signature'] = gera_assinatura(URI='#' + lote_rps.__Id)
    certificado.doctype = '<!DOCTYPE EnviarLoteRpsEnvio [<!ATTLIST LoteRps Id ID #IMPLIED>]>'
    raiz = certificado.assina_xml(raiz, sem_acentos=True)
    #print(raiz.como_xml_em_texto)

    return raiz.como_xml_em_texto


def gera_consulta_situacao_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarSituacaoLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarSituacaoLoteRpsEnvio
    consultarps['__xmlns'] = 'http://www.e-governeapps2.com.br/'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps.Prestador['InscricaoMunicipal'] = prestador.im
    consultarps['Protocolo'] = protocolo
    
    return raiz.como_xml_em_texto


def gera_consulta_rps(protocolo, prestador):
    raiz = DicionarioBrasil()
    raiz['ConsultarSituacaoLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarSituacaoLoteRpsEnvio
    consultarps['__xmlns'] = 'http://www.e-governeapps2.com.br/'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps.Prestador['InscricaoMunicipal'] = prestador.im
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
        Prestador = rps.InfRps.Prestador
        Tomador = rps.InfRps.Tomador

        #
        # Prestador
        #
        nota.prestador.cnpj_cpf = unicode(getattr(Prestador, 'Cnpj', '') or '') or unicode(getattr(Prestador, 'Cpf', '') or '')
        nota.prestador.im = unicode(getattr(Prestador, 'InscricaoMunicipal', '') or '')

        if getattr(rps.InfRps, 'OptanteSimplesNacional', 2) == 1:
            nota.prestador.regime_tributario = REGIME_TRIBUTARIO_SIMPLES

        nota.prestador.incentivador_cultural = getattr(rps.InfRps, 'IncentivadorCultural', 2) == 1

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
        if hasattr(rps.InfRps, 'IdentificacaoRps'):
            nota.rps.numero = getattr(rps.InfRps.IdentificacaoRps, 'Numero', 0)
            nota.rps.serie = unicode(getattr(rps.InfRps.IdentificacaoRps, 'Serie', ''))
            nota.rps.tipo = (getattr(rps.InfRps.IdentificacaoRps, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        nota.rps.data_hora_emissao = getattr(rps.InfRps, 'DataEmissao', None)
        nota.natureza_operacao = (getattr(rps.InfRps, 'NaturezaOperacao', UnicodeBrasil('1')).inteiro - 1) or 0
        #rps.InfRps.RegimeEspecialTributacao =
        nota.cancelada = getattr(rps.InfRps, 'Status', '2') == '1'
        #rps.InfRps.OutrasInformacoes =

        if hasattr(rps.InfRps, 'RpsSubstituido'):
            nota.nfse_substituida.numero = getattr(rps.InfRps.RpsSubstituido, 'Numero', UnicodeBrasil('0')).inteiro
            nota.nfse_substituida.serie = unicode(getattr(rps.InfRps.RpsSubstituido, 'Serie', ''))
            nota.nfse_substituida.tipo = (getattr(rps.InfRps.RpsSubstituido, 'Tipo', UnicodeBrasil('1')).inteiro - 1) or 0

        #
        # Serviço
        #
        Servico = rps.InfRps.Servico
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
        #rps.InfRps.Servico.CodigoCnae = nota.servico.codigo
        #rps.InfRps.Servico.CodigoTributacaoMunicipio = nota.servico.codigo
        nota.descricao = unicode(getattr(Servico, 'Discriminacao', '') or '')
        nota.municipio_fato_gerador = unicode(getattr(Servico, 'CodigoMunicipio', '') or '').zfill(7)

        lista_notas.append(nota)

    return lista_notas, numero_lote

def gera_cancelamento_nota(nota, certificado):
    raiz = DicionarioBrasil()
    raiz['CancelarLoteRpsEnvio'] = DicionarioBrasil()
    cancelanota = raiz.CancelarLoteRpsEnvio
    cancelanota['LoteRps'] = DicionarioBrasil()
    pedcanc = cancelanota.LoteRps
    pedcanc['Protocolo'] = nota.numero_protocolo_nfse
    pedcanc['Cnpj'] = nota.prestador.cnpj_cpf_numero
    pedcanc['InscricaoMunicipal'] = nota.prestador.im or '0'    
    assinatura = gera_assinatura(URI='#' + pedcanc.InfPedidoCancelamento.__Id)
    pedcanc['Signature'] = assinatura

    if certificado:
        certificado.doctype = '<!DOCTYPE Pedido [<!ATTLIST InfPedidoCancelamento Id ID #IMPLIED>]>'
        raiz = certificado.assina_xml(raiz)
        print(raiz.como_xml_em_texto)


    return raiz.como_xml_em_texto
