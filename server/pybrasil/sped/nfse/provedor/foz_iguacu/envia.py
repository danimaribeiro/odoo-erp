# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.codificacao = 'ascii'
conexao.forca_http = True

MODELO_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><RecebeLoteRPS xmlns="http://tempuri.org/"><xml>{body}</xml></RecebeLoteRPS></soap:Body></soap:Envelope>'''

MODELO_CONSULTA_SOAP_ENVELOPE = '''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ConsultarLoteRPS xmlns="http://tempuri.org/"><xml>{body}</xml></ConsultarLoteRPS></soap:Body></soap:Envelope>'''

def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    #lote_rps = escape_xml(lote_rps)

    conexao.certificado = certificado
    conexao.metodo = 'RecebeLoteRPS'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }
    print(lote_rps)
    conexao.servidor = 'nfse.pmfi.pr.gov.br'   
    conexao.url = 'nfsews/nfse.asmx'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/RecebeLoteRPS"'    
        
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE
    conexao.conectar_servico(conteudo=lote_rps)

    open('/home/monital/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/monital/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    resposta = conexao.resposta.Envelope.Body 
    print(resposta.como_xml_em_texto)
    if 'RecebeLoteRPSResult' in resposta.como_xml_em_texto:
        resposta = resposta.RecebeLoteRPSResponse['RecebeLoteRPSResult']
        #
        # Removemos os namespaces desnecessários
        #        
    return resposta

def envia_consulta_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_rps(protocolo, prestador, certificado)
    #consulta_rps = escape_xml(consulta_rps)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarLoteRPS'
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }
    
    conexao.servidor = 'nfse.pmfi.pr.gov.br'   
    conexao.url = 'nfsews/nfse.asmx'
    conexao.modelo_header['SOAPAction'] = '"http://tempuri.org/ConsultarLoteRPS"'    
    
    conexao.modelo_soap_envelope = MODELO_CONSULTA_SOAP_ENVELOPE    
    conexao.conectar_servico(conteudo=consulta_rps)

    resposta = conexao.resposta.Envelope.Body
    
    print(resposta.como_xml_em_texto)
    
    if 'ConsultarLoteRPSResult' in resposta.como_xml_em_texto:
        resposta = resposta.ConsultarLoteRPSResponse['ConsultarLoteRPSResult']
        
    return resposta

