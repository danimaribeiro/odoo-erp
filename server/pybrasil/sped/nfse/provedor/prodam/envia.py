# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_situacao_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario

conexao = ConexaoWebService()
conexao.servidor = 'nfse.blumenau.sc.gov.br'
conexao.codificacao = 'ascii'
conexao.forca_sslv3 = True
conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

#MODELO_SOAP_ENVELOPE_PRODUCAO = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><EnvioLoteRPSRequest xmlns="http://www.blumenau.sc.gov.br/nfse"><VersaoSchema>1</VersaoSchema><MensagemXML>{body}</MensagemXML></EnvioLoteRPSRequest></soap:Body></soap:Envelope>'
MODELO_SOAP_ENVELOPE_HOMOLOGACAO = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><TesteEnvioLoteRPSRequest xmlns="http://www.blumenau.sc.gov.br/nfse"><VersaoSchema>1</VersaoSchema><MensagemXML>{body}</MensagemXML></TesteEnvioLoteRPSRequest></soap:Body></soap:Envelope>'

#
# Muito cuidado aqui, essa PRODAM faz o webservice
# em .NET, ou seja, padrão XML não existe...
# Se o Envelope SOAP não for enviado com as quebras de linha
# e os espaços de identação, o webservice não processa a requisição...
#
MODELO_SOAP_ENVELOPE_PRODUCAO_BLUMENAU = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://nfse.blumenau.sc.gov.br">
   <soapenv:Header/>
   <soapenv:Body>
      <nfse:EnvioLoteRPSRequest>
         <nfse:VersaoSchema>1</nfse:VersaoSchema>
         <nfse:MensagemXML>{body}</nfse:MensagemXML>
      </nfse:EnvioLoteRPSRequest>
   </soapenv:Body>
</soapenv:Envelope>'''
conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO_BLUMENAU

MODELO_SOAP_ENVELOPE_PRODUCAO_SAOPAULO = '''<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
      <VersaoSchema>1</VersaoSchema>
      <MensagemXML>{body}</MensagemXML>
    </EnvioLoteRPSRequest>
  </soap12:Body>
</soap12:Envelope>'''


def envia_rps(lista_notas, numero_lote, certificado, producao=False, municipio=None):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)

    #open('/home/ari/lote.xml', 'w').write(lote_rps)

    lote_rps = escape_xml(lote_rps)

    conexao.url = 'ws/lotenfe.asmx'
    conexao.certificado = certificado
    conexao.modelo_header = {
        'Content-Type': 'text/xml; charset=utf-8',
    }


    if municipio is None or municipio == '42024040000':
        conexao.servidor = 'nfse.blumenau.sc.gov.br'
        conexao.modelo_header['SOAPAction'] = 'http://nfse.blumenau.sc.gov.br/ws/envioLoteRPS'
        conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO_BLUMENAU
    elif municipio == '35503080000':
        conexao.servidor = 'nfe.prefeitura.sp.gov.br'
        conexao.modelo_header['SOAPAction'] = 'http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPS'
        conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO_SAOPAULO
        
    conexao.metodo = 'EnvioLoteRPS'

    #open('/home/william/envelope.xml', 'wb').write(lote_rps.encode('utf-8'))
    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    #
    # A PRODAM envia o conteúdo da resposta escapado
    #
    resp = conexao.resposta.Envelope.Body.como_xml_em_texto
    resp = unescape_xml(resp)
    resp = resp.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    #print(resp)
    #open('/home/ari/resposta.xml', 'w').write(resp.encode('utf-8'))
    resp = xml_para_dicionario(resp)
    conexao.resposta.Envelope.Body = resp

    return conexao.resposta.Envelope.Body


def envia_consulta_situacao_rps(protocolo, prestador, certificado, producao=False):
    consulta_rps = gera_consulta_situacao_rps(protocolo, prestador)

    conexao.certificado = certificado
    conexao.metodo = 'ConsultarSituacaoLoteRpsEnvio'

    if producao:
        conexao.url = 'e-nota-contribuinte-ws/consultarSituacaoLoteRps'
    else:
        conexao.url = 'e-nota-contribuinte-test-ws/consultarSituacaoLoteRps'

    conexao.conectar_servico(conteudo=consulta_rps)

    #open('/home/ari/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    #<ns2:ConsultarSituacaoLoteRpsEnvioResponse>
        #<ConsultarSituacaoLoteRpsResposta>
            #<ListaMensagemRetorno>
                #<MensagemRetorno>
                    #<Codigo>E10</Codigo>
                    #<Mensagem>RPS já informado.</Mensagem>
                    #<Correcao>Para essa Inscrição Municipal/CNPJ já existe um RPS informado com o mesmo número, série e tipo.</Correcao>
                #</MensagemRetorno>
            #</ListaMensagemRetorno>
        #</ConsultarSituacaoLoteRpsResposta>
    #</ns2:ConsultarSituacaoLoteRpsEnvioResponse>

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

    #open('/home/ari/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

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
