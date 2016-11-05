# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.codificacao = 'ascii'
conexao.forca_http = True

MODELO_SOAP_ENVELOPE = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Header/><soapenv:Body><tem:RecepcionarLoteRps xmlns:tem="http://tempuri.org/"><tem:xmlEnvio><![CDATA[{body}]]></tem:xmlEnvio></tem:RecepcionarLoteRps></soapenv:Body></soapenv:Envelope>'''

MODELO_CONSULTA_SOAP_ENVELOPE = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Header/><soapenv:Body><tem:ConsultarLoteRps xmlns:tem="http://tempuri.org/"><tem:xmlEnvio><![CDATA[{body}]]></tem:xmlEnvio></tem:ConsultarLoteRps></soapenv:Body></soapenv:Envelope>'''

def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    #lote_rps = escape_xml(lote_rps)

    conexao.certificado = certificado
    conexao.metodo = 'RecepcionarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'nfse.stitaipu.pr.gov.br'
    conexao.url = 'NFSEWS/Services.svc'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/INFSEGeracao/RecepcionarLoteRps"'

    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=lote_rps)

    open('/home/monital/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/olhovivo/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    resposta = conexao.resposta.Envelope.Body
    print(resposta.como_xml_em_texto)
    if 'RecepcionarLoteRpsResult' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.RecepcionarLoteRpsResponse['RecepcionarLoteRpsResult'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace('xmlns="http://www.abrasf.org.br/nfse"', '')
        resposta = resposta.replace('xmlns:xsd="http://www.w3.org/2001/XMLSchema"', '')
        resposta = xml_para_dicionario(resposta)
        print(resposta)

    return resposta

def envia_consulta_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_rps(protocolo, prestador, certificado)
    #consulta_rps = escape_xml(consulta_rps)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'nfse.stitaipu.pr.gov.br'
    conexao.url = 'NFSEWS/Services.svc'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/INFSEConsultas/ConsultarLoteRps"'

    conexao.modelo_soap_envelope = MODELO_CONSULTA_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=consulta_rps)

    resposta = conexao.resposta.Envelope.Body

    resposta = conexao.resposta.Envelope.Body

    if 'ConsultarLoteRpsResult' in resposta.como_xml_em_texto:
        #
        # Essa GovBR não escapa os arquivos corretamente, tentamos corrigir aqui
        #
        resposta = resposta.ConsultarLoteRpsResponse['ConsultarLoteRpsResult']
        resposta = resposta.replace('\n', '')
        resposta = resposta.replace('\r', '')
        resposta = unescape_xml(resposta)
        resposta = resposta.replace(' & ', ' &amp; ')
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace(' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace(' xmlns="http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd"', '')
        resposta = resposta.replace(' xmlns:xsd="http://www.w3.org/2001/XMLSchema"', '')
        print(resposta)
        resposta = xml_para_dicionario(resposta)

    return resposta

