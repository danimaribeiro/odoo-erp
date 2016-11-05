# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.codificacao = 'ascii'
#conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

MODELO_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="UTF-8"?><env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><env:Header/><env:Body><RecepcionarLoteRps xmlns="http://tempuri.org/"><cabec/><msg><![CDATA[<?xml version="1.0" encoding="UTF-8"?>{body}]]></msg></RecepcionarLoteRps></env:Body></env:Envelope>'''

MODELO_CONSULTA_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="UTF-8"?><env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><env:Header/><env:Body><ConsultarLoteRps xmlns="http://tempuri.org/"><cabec/><msg><![CDATA[<?xml version="1.0" encoding="UTF-8"?>{body}]]></msg></ConsultarLoteRps></env:Body></env:Envelope>'''


def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    #lote_rps = escape_xml(lote_rps)

    conexao.certificado = certificado
    conexao.metodo = 'RecepcionarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'www.webiss.com.br'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/INfseServices/RecepcionarLoteRps"'

    #
    # Barbacena
    #
    if municipio is None or municipio == '31056080000':
        conexao.url = 'mgbarbacena_wsnfse/NfseServices.svc'

    elif municipio == '31701070000':
        conexao.url = 'mguberaba_wsnfse/NfseServices.svc'

    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=lote_rps)

    open('/home/olhovivo/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/olhovivo/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    resposta = conexao.resposta.Envelope.Body
    if 'RecepcionarLoteRpsResult' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.RecepcionarLoteRpsResponse['RecepcionarLoteRpsResult'])
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace('xmlns="http://www.abrasf.org.br/nfse"', '')
        resposta = resposta.replace('xmlns:xsd="http://www.w3.org/2001/XMLSchema"', '')
        resposta = xml_para_dicionario(resposta)

    return resposta

def envia_consulta_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_rps(protocolo, prestador, certificado)
    #consulta_rps = escape_xml(consulta_rps)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarLoteRps'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    conexao.servidor = 'www.webiss.com.br'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/INfseServices/ConsultarLoteRps"'

    if prestador.municipio.codigo_ibge == '3105608':
        conexao.url = 'mgbarbacena_wsnfse/NfseServices.svc'

    elif prestador.municipio.codigo_ibge == '3170107':
        conexao.url = 'mguberaba_wsnfse/NfseServices.svc'

    conexao.modelo_soap_envelope = MODELO_CONSULTA_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=consulta_rps)

    resposta = conexao.resposta.Envelope.Body

    resposta = conexao.resposta.Envelope.Body
        
    if 'detail' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta)
        print(resposta.como_xml_em_texto)
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns="http://schemas.microsoft.com/2003/10/Serialization/"', '')        
        print(resposta)
        resposta = xml_para_dicionario(resposta)
        
    elif 'ConsultarLoteRpsResult' in resposta.como_xml_em_texto:
        resposta = unescape_xml(resposta.ConsultarLoteRpsResponse['ConsultarLoteRpsResult'])
        print(resposta)
        #
        # Removemos os namespaces desnecessários
        #
        resposta = resposta.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        resposta = resposta.replace('xmlns="http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd"', '')
        resposta = resposta.replace('xmlns:xsd="http://www.w3.org/2001/XMLSchema"', '')
        resposta = xml_para_dicionario(resposta)
        

    return resposta

