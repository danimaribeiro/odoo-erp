# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_situacao_rps, gera_consulta_rps
from ....base import ConexaoWebService
from pybrasil.base import escape_xml, unescape_xml, xml_para_dicionario, tira_acentos

conexao = ConexaoWebService()
conexao.servidor = 'sispmjp.joaopessoa.pb.gov.br'
#conexao.servidor = 'nfsehomolog.joaopessoa.pb.gov.br'
conexao.codificacao = 'ascii'
conexao.forca_sslv3 = True
conexao.forca_cadeia_conexao = True
conexao.porta = 8443
#conexao.namespace_soap = 'http://schemas.xmlsoap.org/soap/envelope/'

#
# Muito cuidado aqui, essa PRODAM faz o webservice
# em .NET, ou seja, padrão XML não existe...
# Se o Envelope SOAP não for enviado com as quebras de linha
# e os espaços de identação, o webservice não processa a requisição...
#
            #<nfseCabecMsg xmlns=""><cabecalho versao="2.01" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.01</versaoDados></cabecalho></nfseCabecMsg>
#MODELO_SOAP_ENVELOPE_PRODUCAO = b'''<?xml version="1.0" encoding="UTF-8"?>
#<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://nfse.abrasf.org.br">
    #<soapenv:Header />
    #<soapenv:Body>
        #<nfse:RecepcionarLoteRpsRequest>
            #<nfseCabecMsg xmlns=""></nfseCabecMsg>
            #<nfseDadosMsg xmlns=""><?xml version="1.0" encoding="UTF-8"?>{body}</nfseDadosMsg>
        #</nfse:RecepcionarLoteRpsRequest>
    #</soapenv:Body>
#</soapenv:Envelope>'''
MODELO_SOAP_ENVELOPE_PRODUCAO = b'''<?xml version="1.0" encoding="utf-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://nfse.abrasf.org.br/"><soapenv:Body><nfse:RecepcionarLoteRpsRequest xmlns:nfse="http://nfse.abrasf.org.br"><nfseCabecMsg><cabecalho versao="2.02" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.02</versaoDados></cabecalho></nfseCabecMsg><nfseDadosMsg><?xml version="1.0" encoding="UTF-8"?>{body}</nfseDadosMsg></nfse:RecepcionarLoteRpsRequest></soapenv:Body></soapenv:Envelope>'''

conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO


def envia_rps(lista_notas, numero_lote, certificado, producao=False):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    #lote_rps = '<?xml version="1.0" encoding="UTF-8"?>' + lote_rps
    #lote_rps = escape_xml(lote_rps)
    x = MODELO_SOAP_ENVELOPE_PRODUCAO.format(body=lote_rps)

    #open('/home/prottege/lote.xml', 'w').write(lote_rps.encode('utf-8'))

    #lote_rps = open('/home/prottege/lote-original.xml', 'r').read()

    #lote_rps = escape_xml(lote_rps)
    #lote_rps = tira_acentos(lote_rps)

    conexao.url = b'sispmjp/NfseWSService'
    conexao.certificado = certificado
    conexao.modelo_header = {
        b'Content-Type': b'text/xml;charset=UTF-8',
        #b'Accept-Encoding': b'gzip,deflate',
        b'Host': b'sispmjp.joaopessoa.pb.gov.br:8443',
        #b'Connection': b'Keep-Alive',
        #b'User-Agent': b'Apache-HttpClient/4.1.1 (java 1.5)',
    }

    #if producao:
    conexao.metodo = 'RecepcionarLoteRps'
    conexao.modelo_header[b'SOAPAction'] = b'RecepcionarLoteRps'
    conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_PRODUCAO
    #else:
        #conexao.metodo = 'TesteEnvioLoteRPS'
        #conexao.modelo_header['SOAPAction'] = 'http://nfse.blumenau.sc.gov.br/ws/testeenvio'
        #conexao.modelo_soap_envelope = MODELO_SOAP_ENVELOPE_HOMOLOGACAO

    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/ari/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    #
    # A PRODAM envia o conteúdo da resposta escapado
    #
    resp = conexao.resposta.Envelope.Body.como_xml_em_texto
    resp = unescape_xml(resp)
    resp = resp.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    #print(resp)
    open('/home/prottege/resposta.xml', 'w').write(resp.encode('utf-8'))
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
