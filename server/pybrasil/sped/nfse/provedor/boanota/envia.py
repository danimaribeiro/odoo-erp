# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_situacao_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario


conexao = ConexaoWebService()
conexao.servidor = 'isscuritiba.curitiba.pr.gov.br'
#conexao.servidor = 'pilotoisscuritiba.curitiba.pr.gov.br'
conexao.codificacao = 'ascii'
#conexao.forca_sslv3 = True
conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

#MODELO_SOAP_ENVELOPE_HOMOLOGACAO = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><TesteEnvioLoteRPSRequest xmlns="http://www.blumenau.sc.gov.br/nfse"><VersaoSchema>1</VersaoSchema><MensagemXML>{body}</MensagemXML></TesteEnvioLoteRPSRequest></soap:Body></soap:Envelope>'

#
# Muito cuidado aqui, essa PRODAM faz o webservice
# em .NET, ou seja, padrão XML não existe...
# Se o Envelope SOAP não for enviado com as quebras de linha
# e os espaços de identação, o webservice não processa a requisição...
#
MODELO_SOAP_ENVELOPE_PRODUCAO = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <RecepcionarLoteRps xmlns="http://www.e-governeapps2.com.br/">
    {body}
    </RecepcionarLoteRps>
  </soap:Body>
</soap:Envelope>'''

MODELO_SOAP_ENVELOPE_PRODUCAO_CONSULTA = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ConsultarSituacaoLoteRps xmlns="http://www.e-governeapps2.com.br/">
    {body}
    </ConsultarSituacaoLoteRps>
  </soap:Body>
</soap:Envelope>'''



def envia_rps(lista_notas, numero_lote, certificado, producao=False):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)

    #print('lote_rps')
    #print(lote_rps)

    conexao.url = 'Iss.NfseWebService/nfsews.asmx'
    conexao.certificado = certificado
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    #if producao:
    conexao.metodo = 'RecepcionarLoteRps'
    conexao.modelo_header['SOAPAction'] = 'http://www.e-governeapps2.com.br/RecepcionarLoteRps'
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO

    #if producao:
    #else:
        #conexao.url = 'nfse_ws/nfsews.asmx'
    #open('/home/ari/envelope.xml', 'wb').write(conexao.xml_envio)

    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    return conexao.resposta.Envelope.Body


def envia_consulta_situacao_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_situacao_rps(protocolo, prestador)
    
    
    conexao.url = 'Iss.NfseWebService/nfsews.asmx'
    conexao.certificado = certificado
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }
    conexao.metodo = 'ConsultarSituacaoLoteRps'
    conexao.modelo_header['SOAPAction'] = 'http://www.e-governeapps2.com.br/ConsultarSituacaoLoteRps'
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO_CONSULTA

    # if producao:
    #     conexao.url = 'e-nota-contribuinte-ws/consultarSituacaoLoteRps'
    # else:
    #     conexao.url = 'e-nota-contribuinte-test-ws/consultarSituacaoLoteRps'

    conexao.conectar_servico(conteudo=consulta_rps)

    #open('/home/william/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/william/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    return conexao.resposta.Envelope.Body


def envia_consulta_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_rps(protocolo, prestador)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarLoteRpsEnvio'

    if producao:
        conexao.url = 'e-nota-contribuinte-ws/consultarLoteRps'
    else:
        conexao.url = 'e-nota-contribuinte-test-ws/consultarLoteRps'

    conexao.conectar_servico(conteudo=consulta_rps)

    return conexao.resposta.Envelope.Body


def gera_notas(lista_notas, numero_lote, certificado):
    resposta_envia_rps = envia_rps(lista_notas, numero_lote, certificado)

    if '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
        protocolo = resposta_envia_rps.EnviarLoteRpsEnvioResponse.EnviarLoteRpsResposta.Protocolo
        prestador = lista_notas[0].prestador
        resposta_consulta_situacao_rps = envia_consulta_rps(protocolo, prestador, certificado)

        #
        # O processamento já está OK
        #
        if '<Situacao>4</Situacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
            pass

        return resposta_consulta_situacao_rps

    return resposta_envia_rps
