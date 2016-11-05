# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.codificacao = 'ascii'
#conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

MODELO_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <RecepcionarLoteRpsRequest xmlns="http://notacarioca.rio.gov.br/">
      <inputXML>{body}</inputXML>
    </RecepcionarLoteRpsRequest>
  </soap:Body>
</soap:Envelope>'''

MODELO_CONSULTA_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ConsultarLoteRpsRequest xmlns="http://notacarioca.rio.gov.br/">
      <inputXML>{body}</inputXML>
    </ConsultarLoteRpsRequest>
  </soap:Body>
</soap:Envelope>'''


def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    lote_rps = escape_xml('<?xml version="1.0" encoding="utf-8"?>' + lote_rps)

    conexao.certificado = certificado
    conexao.metodo = 'RecepcionarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'notacarioca.rio.gov.br'
    conexao.url = 'WSNacional/nfse.asmx'
    conexao.modelo_header['SOAPAction'] = '"http://notacarioca.rio.gov.br/RecepcionarLoteRps"'
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/mastervig/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/mastervig/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    resposta = conexao.resposta.Envelope.Body
    if 'outputXML' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.RecepcionarLoteRpsResponse['outputXML'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace('xmlns="http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd"', '')
        resposta = xml_para_dicionario(resposta)

    return resposta

def envia_consulta_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_rps(protocolo, prestador, certificado)
    consulta_rps = escape_xml(consulta_rps)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'notacarioca.rio.gov.br'
    conexao.url = 'WSNacional/nfse.asmx'
    conexao.modelo_header['SOAPAction'] = '"http://notacarioca.rio.gov.br/ConsultarLoteRps"'

    conexao.modelo_soap_envelope = MODELO_CONSULTA_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=consulta_rps)

    resposta = conexao.resposta.Envelope.Body

    resposta = conexao.resposta.Envelope.Body
    if 'outputXML' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.ConsultarLoteRpsResponse['outputXML'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace('xmlns="http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd"', '')
        resposta = xml_para_dicionario(resposta)

    return resposta

