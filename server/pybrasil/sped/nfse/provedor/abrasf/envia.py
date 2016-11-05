# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps, gera_consulta_situacao_rps, gera_consulta_rps
from ....base import ConexaoWebService

conexao = ConexaoWebService()
conexao.servidor = 'http://cetil.apucarana.pr.gov.br/NFSEWS/Services.svc?wsdl'
conexao.codificacao = 'ascii'


def envia_rps(lista_notas, numero_lote, certificado, producao=False):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)

    conexao.certificado = certificado
    conexao.metodo = 'EnviarLoteRpsEnvio'

    if producao:
        conexao.url = 'NFSEWS/Services.svc/recepcionarLoteRps'
    else:
        conexao.url = 'NFSEWS/Services.svc/recepcionarLoteRps'

    conexao.conectar_servico(conteudo=lote_rps)

    #open('/home/catalog/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/catalog/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

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
