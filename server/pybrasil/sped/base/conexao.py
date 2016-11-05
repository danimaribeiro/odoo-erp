# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

import os
from httplib import HTTPSConnection, HTTPConnection
import socket
import ssl
from uuid import uuid4
#from StringIO import StringIO

from .certificado import Certificado
from ...base import xml_para_dicionario
#from .soap_11 import parseString as parse_soap11


#ssl._create_default_https_context = ssl._create_unverified_context

DIRNAME = os.path.dirname(__file__)
CAMINHO_TEMPORARIO = '/tmp/'


class ConexaoHTTPS(HTTPSConnection):
    #
    # O objetivo dessa derivação da classe HTTPSConnection é o seguinte:
    #
    # No estado do PR, o webservice deles anuncia que aceita os protocolos SSLv2 e SSLv3
    # A classe HTTPSConnection, nesse caso, assume que pode ser usado SSLv2, anunciando pelo servidor
    # MAS... se você não usar SSLv3 é impossível a conexão...
    #
    def connect(self):
        "Connect to a host on a given (SSL) port."

        #
        # source_address é atributo incluído na versão 2.7 do Python
        # Verificando a existência para funcionar em versões anteriores à 2.7
        #
        if hasattr(self, 'source_address'):
            sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
        else:
            sock = socket.create_connection((self.host, self.port), self.timeout)

        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        if getattr(self, 'forca_cadeia_conexao', False):
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23, ca_certs=self.ca_certs)
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)


SOAP_11 = 'soap_1.1'
SOAP_12 = 'soap_1.2'

NS_SOAP_PADRAO = b'http://www.w3.org/2003/05/soap-envelope'
SOAP_11_ENVELOPE = b'<soap:Envelope xmlns:soap="{ns}"><soap:Body>{body}</soap:Body></soap:Envelope>'
SOAP_12_ENVELOPE = b'<soap:Envelope xmlns:soap="{ns}"><soap:Header>{header}</soap:Header><soap:Body>{body}</soap:Body></soap:Envelope>'


class ConexaoWebService(object):
    def __init__(self, certificado=None, servidor='', url='', metodo='', versao_soap=SOAP_11, action=''):
        self.certificado = certificado or Certificado()
        self.servidor = servidor
        self.url = url
        self.metodo = metodo
        self.versao_soap = versao_soap
        self.action = action
        self.header = {}
        self.xml_envio = ''
        self.xml_resposta = ''
        self.response = None
        self.resposta = None
        self.codificacao = 'utf-8'
        self.modelo_soap_envelope = None
        self.modelo_header = None
        self.namespace_soap = NS_SOAP_PADRAO
        self.forca_sslv3 = False
        self.forca_http = False
        self.porta = 443
        self.forca_cadeia_conexao = False

    def conectar_servico(self, conteudo='', cabecalho=''):
        if isinstance(conteudo, unicode):
            conteudo = conteudo.encode('utf-8')

        if isinstance(cabecalho, unicode):
            cabecalho = cabecalho.encode('utf-8')

        if isinstance(self.namespace_soap, unicode):
            self.namespace_soap = self.namespace_soap.encode('utf-8')

        dados = {
            b'body': conteudo,
            b'header': cabecalho,
            b'ns': self.namespace_soap
        }

        if self.modelo_header:
            self.header = self.modelo_header
        elif self.versao_soap == SOAP_11:
            self.header = {
                b'content-type': b'application/soap+xml; charset=utf-8',
                b'Accept': b'application/soap+xml; charset=utf-8',
                b'SOAPAction': self.action.encode('utf-8') or self.metodo.encode('utf-8')
            }
        else:
            self.header = {
                b'content-type': b'application/soap+xml; charset=utf-8; action="%s"' % self.action.encode('utf-8')
            }

        if self.modelo_soap_envelope is not None:
            self.xml_envio = self.modelo_soap_envelope.format(**dados)
        elif self.versao_soap == SOAP_11:
            self.xml_envio = SOAP_11_ENVELOPE.format(**dados)
        else:
            self.xml_envio = SOAP_12_ENVELOPE.format(**dados)

        self.certificado.prepara_certificado_arquivo_pfx()

        #open('/home/william/envio.xml', 'w').write(self.xml_envio)

        #
        # Salva o certificado e a chave privada para uso na conexão HTTPS
        # Salvamos como um arquivo de nome aleatório para evitar o conflito
        # de uso de vários certificados e chaves diferentes na mesma máquina
        # ao mesmo tempo
        #
        nome_arq_chave = CAMINHO_TEMPORARIO + uuid4().hex
        arq_tmp = open(nome_arq_chave, 'w')
        arq_tmp.write(self.certificado.chave)
        arq_tmp.close()

        nome_arq_certificado = CAMINHO_TEMPORARIO + uuid4().hex
        arq_tmp = open(nome_arq_certificado, 'w')
        arq_tmp.write(self.certificado.certificado)
        arq_tmp.close()

        nome_arq_cadeia = CAMINHO_TEMPORARIO + uuid4().hex
        arq_tmp = open(nome_arq_cadeia, 'w')
        arq_tmp.write(self.certificado.certificado)
        for cert_ca in self.certificado.certificado_ca:
            arq_tmp.write(cert_ca)
        arq_tmp.close()

        if self.forca_sslv3:
            con = ConexaoHTTPS(self.servidor, port=self.porta, key_file=nome_arq_chave, cert_file=nome_arq_certificado)
        elif self.forca_http:
            con = HTTPConnection(self.servidor)
        else:
            con = HTTPSConnection(self.servidor, port=self.porta, key_file=nome_arq_chave, cert_file=nome_arq_certificado)

        con.forca_cadeia_conexao = self.forca_cadeia_conexao
        con.ca_certs = nome_arq_cadeia

        #
        # É preciso definir o POST abaixo como bytestring, já que importamos
        # os unicode_literals... Dá um pau com xml com acentos sem isso...
        #
        con.set_debuglevel(1)
        con.request(b'POST', b'/' + self.url.encode('utf-8'), self.xml_envio, self.header)
        con.sock.settimeout(600.0)
        #import pdb; pdb.set_trace()

        self.response = con.getresponse()

        #
        # Apagamos os arquivos do certificado e o da chave privada, para evitar
        # um potencial risco de segurança; muito embora o uso da chave privada
        # para assinatura exija o uso da senha, pode haver serviços que exijam
        # apenas o uso do certificado para validar a identidade, independente
        # da existência de assinatura digital
        #
        os.remove(nome_arq_chave)
        os.remove(nome_arq_certificado)
        os.remove(nome_arq_cadeia)

        #print('status', self.response.status)
        #print('reason', self.response.reason)
        #print('msg', self.response.msg)
        #print('headers', self.response.getheaders())

        xml_resp = self.response.read()
        #print(xml_resp)
        self.xml_resposta = xml_resp
        con.close()

        self.resposta = xml_para_dicionario(self.xml_resposta)
