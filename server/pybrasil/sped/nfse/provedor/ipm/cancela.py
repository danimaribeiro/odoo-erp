# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_cancelamento_nota
from ....base import ConexaoWebService

conexao = ConexaoWebService()
conexao.servidor = 'e-gov.betha.com.br'
conexao.codificacao = 'iso-8859-1'


def cancela_nota(nfse, certificado, producao=False):
    cancelamento = gera_cancelamento_nota(nfse, certificado)

    conexao.certificado = certificado
    conexao.metodo = 'CancelarNfseEnvio'

    if producao:
        conexao.url = 'e-nota-contribuinte-ws/cancelarNfse'
    else:
        conexao.url = 'e-nota-contribuinte-test-ws/cancelarNfse'

    conexao.conectar_servico(conteudo=cancelamento)

    #open('/home/ari/envelope.xml', 'wb').write(conexao.xml_envio)
    #open('/home/ari/envelope_resposta.xml', 'wb').write(conexao.xml_resposta)

    return conexao.resposta.Envelope.Body
