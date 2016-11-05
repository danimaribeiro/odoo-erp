# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps #, gera_consulta_situacao_rps, gera_consulta_rps

from StringIO import StringIO
import requests
from .....base import xml_para_dicionario
#import urllib
#import urllib2
#from BeautifulSoup import BeautifulSoup


def envia_rps(lista_notas, numero_lote, certificado, producao=False):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
    nota = lista_notas[0]
    lote_rps = u'<?xml version="1.0" encoding="ISO-8859-1"?>' + lote_rps
    print('lote_rps')
    print(lote_rps.encode('utf-8'))

    url = 'http://sync.nfs-e.net/datacenter/include/nfw/importa_nfw/nfw_import_upload.php?eletron=1'
    #url = 'http://sync.nfs-e.net/datacenter/include/nfw/importa_nfw/nfw_import_upload.php'

    cnpj = nota.prestador.cnpj_cpf_numero

    dados = {
        #'eletron': 1,
        'login': cnpj,
        'senha': certificado.senha,
        'cidade': nota.prestador.municipio.codigo_siafi,
    }

    arq = StringIO()
    arq.write(lote_rps.encode('iso8859-1'))
    arq.seek(0)

    arquivos = {
        'f1': arq,
    }

    texto = ''
    #try:
    resp = requests.post(url, data=dados, files=arquivos)
    #print(resp.content)
    para_unicode = resp.content.decode('iso-8859-1')
    #print(para_unicode.encode('utf-8'))

    #
    # O encoding vem declarado iso8859-1, mas é de fato utf-8...
    #
    texto = resp.content.decode('iso-8859-1')
    texto = texto.replace(u"encoding='iso-8859-1'", u"encoding='utf-8'")

    try:
        texto = xml_para_dicionario(texto)
    except:
        pass

    #except (UnicodeDecodeError,):
        #arq.close()
        #return ''

    arq.close()

    return texto


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
