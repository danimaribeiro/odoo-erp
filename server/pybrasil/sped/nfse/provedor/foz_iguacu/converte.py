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
from ....base import Signature, gera_assinatura, tira_abertura


def gera_rps(lista_notas, numero_lote, certificado=None):
    prestador = lista_notas[0].prestador

    lote_rps = DicionarioBrasil()
    lote_rps['NumeroLote'] = numero_lote
    lote_rps['__Id'] = 'L' + str(lote_rps.NumeroLote)
    lote_rps['Cnpj'] = prestador.cnpj_cpf_numero
    lote_rps['InscricaoMunicipal'] = int(prestador.im or 0)
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
        #if nota.prestador.optante_simples_nacional:
        #    rps.InfRps['RegimeEspecialTributacao'] = 6
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
        valores['ValorDeducoes'] = nota.valor.deducao or 0
        valores['ValorPis'] = nota.valor.retido.pis or 0
        valores['ValorCofins'] = nota.valor.retido.cofins or 0
        valores['ValorInss'] = nota.valor.retido.inss or 0
        valores['ValorIr'] = nota.valor.retido.ir or 0
        valores['ValorCsll'] = nota.valor.retido.csll or 0

        #if nota.prestador.optante_simples_nacional:
            #valores['IssRetido'] = 2
            #valores['ValorIss'] = nota.valor.vr_iss or 0.00
            #valores['ValorIssRetido'] = 0
        #else:
        valores['IssRetido'] = 1 if nota.valor.retido.iss != 0 else 2
        valores['ValorIss'] = nota.valor.vr_iss or 0.00
        valores['ValorIssRetido'] = nota.valor.retido.iss or 0

        valores['OutrasRetencoes'] = nota.valor.retido.outras or 0
        valores['BaseCalculo'] = nota.valor.bc_iss or None

        valores['Aliquota'] = nota.valor.al_iss or 0.00

        valores['ValorLiquidoNfse'] = nota.valor.liquido or None
        valores['DescontoIncondicionado'] = nota.valor.desconto_incondicionado or 0
        valores['DescontoCondicionado'] = nota.valor.desconto_condicionado or 0

        if nota.servico_municipio:
            servico['ItemListaServico'] = nota.servico_municipio
            servico['CodigoCnae'] = nota.prestador.cnae or ''
            #servico['CodigoTributacaoMunicipio'] = nota.servico_municipio
        else:
            servico['ItemListaServico'] = nota.servico.codigo.zfill(4)
            servico['CodigoCnae'] = nota.prestador.cnae or ''
            #servico['CodigoCnae'] = nota.servico.codigo
            #servico['CodigoTributacaoMunicipio'] = nota.servico.codigo

        servico['Discriminacao'] = tira_acentos(nota.descricao).replace('\n', ';').strip()
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

        assinatura = gera_assinatura(URI='#' + rps.InfRps.__Id)
        rps_raiz = DicionarioBrasil()
        rps_raiz['Rps'] = rps
        #rps_raiz.Rps['Signature'] = assinatura

        #if certificado:
            #certificado.doctype = '<!DOCTYPE Rps [<!ATTLIST InfRps Id ID #IMPLIED>]>'
            #rps_assinado = certificado.assina_xml(tira_acentos(rps_raiz.como_xml_em_texto))
            #rps_raiz = xml_para_dicionario(rps_assinado)

        lote_rps.ListaRps.append(rps_raiz)

    raiz = DicionarioBrasil()
    raiz['EnviarLoteRpsEnvio'] = DicionarioBrasil()
    enviarloterpsenvio = raiz.EnviarLoteRpsEnvio
    enviarloterpsenvio['__xmlns'] = 'http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd'
    enviarloterpsenvio['LoteRps'] = lote_rps
    enviarloterpsenvio['Signature'] = gera_assinatura(URI='#' + lote_rps.__Id)
    certificado.doctype = '<!DOCTYPE EnviarLoteRpsEnvio [<!ATTLIST LoteRps Id ID #IMPLIED>]>'
    raiz = certificado.assina_xml(raiz, sem_acentos=True)

    return raiz.como_xml_em_texto


def gera_consulta_rps(protocolo, prestador, certificado=None):
    raiz = DicionarioBrasil()
    raiz['ConsultarLoteRpsEnvio'] = DicionarioBrasil()
    consultarps = raiz.ConsultarLoteRpsEnvio
    consultarps['__xmlns'] = 'http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd'
    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = prestador.cnpj_cpf_numero
    consultarps.Prestador['InscricaoMunicipal'] = prestador.im
    consultarps['Protocolo'] = protocolo

    return raiz.como_xml_em_texto

def gera_cancelamento_nota(nota, certificado):
    raiz = DicionarioBrasil()
    raiz['CancelarNfseEnvio'] = DicionarioBrasil()
    cancelanota = raiz.CancelarNfseEnvio
    cancelanota['__xmlns'] = 'http://www.ginfes.com.br/servico_cancelar_nfse_envio.xsd'
    cancelanota['__Id'] = str(doc_id)

    consultarps['Prestador'] = DicionarioBrasil()
    consultarps.Prestador['Cnpj'] = nota.prestador.cnpj_cpf_numero
    consultarps.Prestador['InscricaoMunicipal'] = nota.prestador.im
    consultarps['NumeroNfse'] = str(nota.numero)
    consultarps['Signature'] = gera_assinatura(URI='#' + raiz.ConsultarLoteRpsEnvio.__Id)
    #xml_a_assinar = tira_acentos(raiz.como_xml_em_texto)
    certificado.doctype = '<!DOCTYPE ConsultarLoteRpsEnvio [<!ATTLIST ConsultarLoteRpsEnvio Id ID #IMPLIED>]>'
    novo_raiz = raiz.como_xml_em_texto
    #novo_raiz = novo_raiz.replace('<ConsultarSituacaoLoteRpsEnvio', '<ConsultarSituacaoLoteRpsEnvio xmlns="http://www.ginfes.com.br/servico_consultar_situacao_lote_rps_envio_v03.xsd"')
    #novo_raiz = novo_raiz.replace('<Prestador', '<Prestador xmlns:tipos="http://www.ginfes.com.br/tipos_v03.xsd"')
    novo_raiz = novo_raiz.replace('<Cnpj', '<Cnpj xmlns="http://www.ginfes.com.br/tipos_v02.xsd"')
    novo_raiz = novo_raiz.replace('<InscricaoMunicipal', '<InscricaoMunicipal xmlns="http://www.ginfes.com.br/tipos_v02.xsd"')
    #novo_raiz = novo_raiz.replace('<Protocolo', '<Protocolo xmlns:tipos="http://www.ginfes.com.br/tipos_v03.xsd"')
    raiz = certificado.assina_xml(novo_raiz)
    raiz = tira_abertura(raiz)

    return raiz
