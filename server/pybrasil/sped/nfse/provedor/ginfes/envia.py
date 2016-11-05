# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_situacao_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.codificacao = 'ascii'
conexao.servidor = 'producao.ginfes.com.br'
conexao.url = 'ServiceGinfesImpl'


MODELO_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:prod="http://producao.ginfes.com.br">
    <soapenv:Header/>
    <soapenv:Body>
        <prod:RecepcionarLoteRpsV3>
            <arg0><ns2:cabecalho versao="3" xmlns:ns2="http://www.ginfes.com.br/cabecalho_v03.xsd"><versaoDados>3</versaoDados></ns2:cabecalho></arg0>
            <arg1>{body}</arg1>
        </prod:RecepcionarLoteRpsV3>
    </soapenv:Body>
</soapenv:Envelope>'''

MODELO_SOAP_ENVELOPE_CONSULTA_SITUACAO = '''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:prod="http://producao.ginfes.com.br">
    <soapenv:Header/>
    <soapenv:Body>
        <prod:ConsultarLoteRpsV3>
            <arg0><ns2:cabecalho versao="3" xmlns:ns2="http://www.ginfes.com.br/cabecalho_v03.xsd"><versaoDados>3</versaoDados></ns2:cabecalho></arg0>
            <arg1>{body}</arg1>
        </prod:ConsultarLoteRpsV3>
    </soapenv:Body>
</soapenv:Envelope>'''


def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE
    conexao.certificado = certificado

    conexao.modelo_header = {
        b'Content-Type': b'text/xml;charset=UTF-8',
        b'Accept-Encoding': b'gzip,deflate',
        b'Host': b'producao.ginfes.com.br',
        b'Connection': b'Keep-Alive',
        b'User-Agent': b'Apache-HttpClient/4.1.1 (java 1.5)',
        b'SOAPAction': b'""',
    }


    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/protectfort/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/protectfort/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    resposta = conexao.resposta.Envelope.Body
    print(resposta.como_xml_em_texto)
    if 'return' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.RecepcionarLoteRpsV3Response['return'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:ns2="http://www.ginfes.com.br/tipos_v03.xsd"', '').replace(':ns2', '').replace('ns2:', '')
        resposta = resposta.replace('xmlns:ns3="http://www.ginfes.com.br/servico_enviar_lote_rps_resposta_v03.xsd"', '').replace(':ns3', '').replace('ns3:', '')
        resposta = xml_para_dicionario(resposta)

    return resposta

def envia_consulta_situacao_rps(doc_id, protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_situacao_rps(doc_id,protocolo, prestador, certificado)

    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_CONSULTA_SITUACAO
    conexao.certificado = certificado

    conexao.modelo_header = {
        b'Content-Type': b'text/xml;charset=UTF-8',
        b'Accept-Encoding': b'gzip,deflate',
        b'Host': b'producao.ginfes.com.br',
        b'Connection': b'Keep-Alive',
        b'User-Agent': b'Apache-HttpClient/4.1.1 (java 1.5)',
        b'SOAPAction': b'""',
    }

    conexao.conectar_servico(conteudo=consulta_rps)

    resposta = conexao.resposta.Envelope.Body

    if 'return' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.ConsultarLoteRpsV3Response['return'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:ns4="http://www.ginfes.com.br/tipos_v03.xsd"', '').replace(':ns4', '').replace('ns4:', '')
        resposta = resposta.replace('xmlns:ns3="http://www.ginfes.com.br/servico_consultar_lote_rps_resposta_v03.xsd"', '').replace(':ns3', '').replace('ns3:', '')

        resposta = xml_para_dicionario(resposta)

    return resposta

