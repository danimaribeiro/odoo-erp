# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

#
# Tenta evitar a necessidade do xmlsec estar instalado
#
try:
    import xmlsec
except ImportError:
    pass

import libxml2
import os
from datetime import datetime
from time import mktime
from OpenSSL import crypto
from pytz import UTC
import base64
from ...base import xml_para_dicionario, DicionarioBrasil, tira_acentos


DIRNAME = os.path.dirname(__file__)


def tira_abertura(texto):
    if '?>' in texto:
        texto = texto.split('?>')[1:]
        texto = ''.join(texto)

    return texto


class Certificado(object):
    def __init__(self):
        self.arquivo = ''
        self.senha = ''
        self.chave = ''
        self.certificado = ''
        self._emissor = {}
        self._proprietario = {}
        self._data_inicio_validade = None
        self._data_fim_validade = None
        self._numero_serie = None
        self._extensoes = {}
        self._doc_xml = None
        self.doctype = ''
        self.ignora_doctype = False
        self.abertura = '<?xml version="1.0" encoding="utf-8"?>'
        self.logo = ''

    def prepara_certificado_arquivo_pfx(self):
        # Lendo o arquivo pfx no formato pkcs12 como binário
        pkcs12 = crypto.load_pkcs12(open(self.arquivo, 'rb').read(), self.senha)
        self.pkcs12 = pkcs12

        # Retorna a string decodificada da chave privada
        self.chave = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkcs12.get_privatekey())

        # Retorna a string decodificada do certificado
        self.prepara_certificado_txt(crypto.dump_certificate(crypto.FILETYPE_PEM, pkcs12.get_certificate()))

        self.certificado_ca = []
        if pkcs12.get_ca_certificates() is not None:
            for cert_ca in pkcs12.get_ca_certificates():
                self.prepara_certificado_txt_ca(crypto.dump_certificate(crypto.FILETYPE_PEM, cert_ca))

    def prepara_certificado_arquivo_pem(self):
        self.prepara_certificado_txt(open(self.arquivo, 'rb').read())

    def prepara_certificado_txt(self, cert_txt):
        #
        # Para dar certo a leitura pelo xmlsec, temos que separar o certificado
        # em linhas de 64 caracteres de extensão...
        #
        cert_txt = cert_txt.replace('\n', '')
        cert_txt = cert_txt.replace('-----BEGIN CERTIFICATE-----', '')
        cert_txt = cert_txt.replace('-----END CERTIFICATE-----', '')

        linhas_certificado = ['-----BEGIN CERTIFICATE-----\n']
        for i in range(0, len(cert_txt), 64):
            linhas_certificado.append(cert_txt[i:i + 64] + '\n')
        linhas_certificado.append('-----END CERTIFICATE-----\n')

        self.certificado = ''.join(linhas_certificado)

        cert_openssl = crypto.load_certificate(crypto.FILETYPE_PEM, self.certificado)
        self.cert_openssl = cert_openssl

        self._emissor = dict(cert_openssl.get_issuer().get_components())
        self._proprietario = dict(cert_openssl.get_subject().get_components())
        self._numero_serie = cert_openssl.get_serial_number()
        self._data_inicio_validade = datetime.strptime(cert_openssl.get_notBefore(), '%Y%m%d%H%M%SZ')
        self._data_inicio_validade = UTC.localize(self._data_inicio_validade)
        self._data_fim_validade = datetime.strptime(cert_openssl.get_notAfter(), '%Y%m%d%H%M%SZ')
        self._data_fim_validade = UTC.localize(self._data_fim_validade)

        for i in range(cert_openssl.get_extension_count()):
            extensao = cert_openssl.get_extension(i)
            self._extensoes[extensao.get_short_name()] = extensao.get_data()

    def prepara_certificado_txt_ca(self, cert_txt):
        #
        # Para dar certo a leitura pelo xmlsec, temos que separar o certificado
        # em linhas de 64 caracteres de extensão...
        #
        cert_txt = cert_txt.replace('\n', '')
        cert_txt = cert_txt.replace('-----BEGIN CERTIFICATE-----', '')
        cert_txt = cert_txt.replace('-----END CERTIFICATE-----', '')

        linhas_certificado = ['-----BEGIN CERTIFICATE-----\n']
        for i in range(0, len(cert_txt), 64):
            linhas_certificado.append(cert_txt[i:i + 64] + '\n')
        linhas_certificado.append('-----END CERTIFICATE-----\n')

        self.certificado_ca.append(''.join(linhas_certificado))

    def _set_chave(self, chave):
        self._chave = chave

    def _get_chave(self):
        try:
            if self._chave:
                return self._chave
            else:
                raise AttributeError("'chave' precisa ser regenerada")
        except AttributeError:
            if self.arquivo:    # arquivo disponível
                self.prepara_certificado_arquivo_pfx()
                return self._chave  # agora já disponível
            else:
                return ''

    chave = property(_get_chave, _set_chave)

    def _set_certificado(self, certificado):
        self._certificado = certificado

    def _get_certificado(self):
        try:
            if self._certificado:   # != ''
                return self._certificado
            else:
                raise AttributeError("'certificado' precisa ser regenerado")
        except AttributeError:
            if self.arquivo:    # arquivo disponível
                self.prepara_certificado_arquivo_pfx()
                return self._certificado  # agora já disponível
            else:
                return ''

    certificado = property(_get_certificado, _set_certificado)

    @property
    def proprietario_nome(self):
        if 'CN' in self.proprietario:
            #
            # Alguns certrificados não têm o CNPJ na propriedade CN, somente o
            # nome do proprietário
            #
            if ':' in self.proprietario['CN']:
                return self.proprietario['CN'].rsplit(':', 1)[0]
            else:
                return self.proprietario['CN']
        else:  # chave CN ainda não disponível
            try:
                self.prepara_certificado_arquivo_pfx()
                return self.proprietario['CN'].rsplit(':', 1)[0]
            except IOError:  # arquivo do certificado não disponível
                return ''

    @property
    def proprietario_cnpj(self):
        if 'CN' in self.proprietario:
            #
            # Alguns certrificados não têm o CNPJ na propriedade CN, somente o
            # nome do proprietário
            #
            if ':' in self.proprietario['CN']:
                return self.proprietario['CN'].rsplit(':', 1)[1]
            else:
                return ''
        else:  # chave CN ainda não disponível
            try:
                self.prepara_certificado_arquivo_pfx()
                return self.proprietario['CN'].rsplit(':', 1)[1]
            except IOError:  # arquivo do certificado não disponível
                return ''

    @property
    def proprietario(self):
        if self._proprietario:
            return self._proprietario
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._proprietario
            except IOError:  # arquivo do certificado não disponível
                return dict()

    @property
    def emissor(self):
        if self._emissor:
            return self._emissor
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._emissor
            except IOError:  # arquivo do certificado não disponível
                return dict()

    @property
    def data_inicio_validade(self):
        if self._data_inicio_validade:
            return self._data_inicio_validade
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._data_inicio_validade
            except IOError:  # arquivo do certificado não disponível
                return None

    @property
    def data_fim_validade(self):
        if self._data_fim_validade:
            return self._data_fim_validade
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._data_fim_validade
            except IOError:  # arquivo do certificado não disponível
                return None

    @property
    def numero_serie(self):
        if self._numero_serie:
            return self._numero_serie
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._numero_serie
            except IOError:  # arquivo do certificado não disponível
                return None

    @property
    def extensoes(self):
        if self._extensoes:
            return self._extensoes
        else:
            try:
                self.prepara_certificado_arquivo_pfx()
                return self._extensoes
            except IOError:  # arquivo do certificado não disponível
                return dict()

    def _inicia_funcoes_externas(self):
        # Ativa as funções de análise de arquivos XML
        libxml2.initParser()
        libxml2.substituteEntitiesDefault(1)

        # Ativa as funções da API de criptografia
        xmlsec.init()
        xmlsec.cryptoAppInit(None)
        xmlsec.cryptoInit()

    def _finaliza_funcoes_externas(self):
        ''' Desativa as funções criptográficas e de análise XML
        As funções devem ser chamadas na ordem inversa da ativação
        '''
        #xmlsec.cryptoShutdown()
        #xmlsec.cryptoAppShutdown()
        xmlsec.shutdown()

        libxml2.cleanupParser()

    def assina_arquivo(self, doc):
        xml = open(doc, 'r').read()
        xml = self.assina_xml(xml)
        return xml

    def _obtem_doctype(self, xml):
        """Obtém DOCTYPE do XML

        Determina o tipo de arquivo que vai ser assinado, procurando pela tag
        correspondente.
        """

        if self.doctype:
            return self.doctype

        doctype = None

        #
        # XML da NF-e
        #
        if '</NFe>' in xml:
            doctype = '<!DOCTYPE NFe [<!ATTLIST infNFe Id ID #IMPLIED>]>'
        elif '</cancNFe>' in xml:
            doctype = '<!DOCTYPE cancNFe [<!ATTLIST infCanc Id ID #IMPLIED>]>'
        elif '</inutNFe>' in xml:
            doctype = '<!DOCTYPE inutNFe [<!ATTLIST infInut Id ID #IMPLIED>]>'
        elif '</infEvento>' in xml:
            doctype = '<!DOCTYPE evento [<!ATTLIST infEvento Id ID #IMPLIED>]>'

        #
        # XML do CT-e
        #
        elif '</CTe>' in xml:
            doctype = '<!DOCTYPE CTe [<!ATTLIST infCte Id ID #IMPLIED>]>'
        elif '</cancCTe>' in xml:
            doctype = '<!DOCTYPE cancCTe [<!ATTLIST infCanc Id ID #IMPLIED>]>'
        elif '</inutCTe>' in xml:
            doctype = '<!DOCTYPE inutCTe [<!ATTLIST infInut Id ID #IMPLIED>]>'
        #elif 'infEvento' in xml:
            #doctype = '<!DOCTYPE evento [<!ATTLIST infEvento Id ID #IMPLIED>]>'

        #
        # XML da NFS-e
        #
        elif 'ReqEnvioLoteRPS' in xml:
            doctype = '<!DOCTYPE Lote [<!ATTLIST Lote Id ID #IMPLIED>]>'
        elif 'EnviarLoteRpsEnvio' in xml:
            doctype = '<!DOCTYPE EnviarLoteRpsEnvio>'
        elif 'CancelarNfseEnvio' in xml:
            doctype = '<!DOCTYPE CancelarNfseEnvio>'

        else:
            raise ValueError('Tipo de arquivo desconhecido para assinatura/validacao')

        return doctype

    def _prepara_doc_xml(self, xml):
        if isinstance(xml, str):
            xml = xml.decode('utf-8')

        if not self.ignora_doctype:
            doctype = self._obtem_doctype(xml)
        else:
            doctype = ''

        #
        # Importantíssimo colocar o encode, pois do contário não é possível
        # assinar caso o xml tenha letras acentuadas
        #
        xml = tira_abertura(xml)
        xml = self.abertura + xml
        xml = xml.replace(self.abertura, self.abertura + doctype)

        #
        # Remove todos os \n
        #
        xml = xml.replace('\n', '')
        xml = xml.replace('\r', '')

        return xml

    def _finaliza_xml(self, xml):
        if isinstance(xml, str):
            xml = unicode(xml.decode('utf-8'))

        if not self.ignora_doctype:
            doctype = self._obtem_doctype(xml)
        else:
            doctype = ''

        #
        # Remove o doctype e os \n acrescentados pela libxml2
        #
        xml = xml.replace('\n', '')
        xml = xml.replace(self.abertura + doctype, self.abertura)

        return xml

    def assina_xml(self, xml, sem_acentos=False):
        self._inicia_funcoes_externas()

        devolve_dicionario = False
        if isinstance(xml, DicionarioBrasil):
            xml = xml.como_xml_em_texto
            if sem_acentos:
                xml = tira_acentos(xml)

            devolve_dicionario = True

        xml = self._prepara_doc_xml(xml)

        #
        # Colocamos o texto no avaliador XML
        #
        doc_xml = libxml2.parseMemory(xml.encode('utf-8'), len(xml.encode('utf-8')))

        #
        # Separa o nó da assinatura
        #
        xpath = doc_xml.xpathNewContext()
        xpath.xpathRegisterNs('sig', 'http://www.w3.org/2000/09/xmldsig#')
        nohs_assinatura = xpath.xpathEval('//sig:Signature')
        #nohs_assinatura = xpath.xpathEval(b"//*[local-name()='Signature']")
        #print(xpath.xpathEval(b"//*[local-name()='Signature']"))
        noh_assinatura = nohs_assinatura[-1]

        #
        # Cria a variável de chamada (callable) da função de assinatura
        #
        assinador = xmlsec.DSigCtx()

        #
        # Buscamos a chave no arquivo do certificado
        #
        chave = xmlsec.cryptoAppKeyLoad(filename=str(self.arquivo), format=xmlsec.KeyDataFormatPkcs12, pwd=str(self.senha), pwdCallback=None, pwdCallbackCtx=None)

        #
        # Atribui a chave ao assinador
        #
        assinador.signKey = chave

        #
        # Realiza a assinatura
        #
        assinador.sign(noh_assinatura)

        #
        # Guarda o status
        #
        status = assinador.status

        #
        # Libera a memória ocupada pelo assinador manualmente
        #
        assinador.destroy()

        if status != xmlsec.DSigStatusSucceeded:
            #
            # Libera a memória ocupada pelo documento xml manualmente
            #
            doc_xml.freeDoc()
            self._finaliza_funcoes_externas()
            raise RuntimeError('Erro ao realizar a assinatura do arquivo; status: "' + str(status) + '"')

        #
        # Elimina do xml assinado a cadeia certificadora, deixando somente
        # o certificado que assinou o documento
        #
        certificados = xpath.xpathEval('//sig:X509Data/sig:X509Certificate')
        #import pdb
        #pdb.set_trace()
        for i in range(len(certificados) - 1):
            if len(nohs_assinatura) == 1 or (len(nohs_assinatura) > 1 and i > 0):
                certificados[i].unlinkNode()
                certificados[i].freeNode()

        #
        # Retransforma o documento xml em texto
        #
        xml = doc_xml.serialize()

        #
        # Libera a memória ocupada pelo documento xml manualmente
        #
        doc_xml.freeDoc()
        self._finaliza_funcoes_externas()

        xml = self._finaliza_xml(xml)

        if devolve_dicionario:
            xml = xml_para_dicionario(xml)

        return xml

    def verifica_assinatura_arquivo(self, doc):
        xml = open(doc, 'r').read()
        return self.verifica_assinatura_xml(xml)

    def verifica_assinatura_xml(self, xml):
        self._inicia_funcoes_externas()
        xml = self._prepara_doc_xml(xml)

        #
        # Colocamos o texto no avaliador XML
        #
        doc_xml = libxml2.parseMemory(xml.encode('utf-8'), len(xml.encode('utf-8')))

        #
        # Separa o nó da assinatura
        #
        xpath = doc_xml.xpathNewContext()
        xpath.xpathRegisterNs('sig', 'http://www.w3.org/2000/09/xmldsig#')
        nohs_assinatura = xpath.xpathEval('//sig:Signature')
        noh_assinatura = nohs_assinatura[-1]

        #
        # Prepara o gerenciador dos certificados confiáveis para verificação
        #
        certificados_confiaveis = xmlsec.KeysMngr()
        xmlsec.cryptoAppDefaultKeysMngrInit(certificados_confiaveis)

        #
        # Prepara a cadeia certificadora
        #
        certificados = os.listdir(DIRNAME + '/cadeia-certificadora/certificados')
        certificados.sort()
        for certificado in certificados:
            certificados_confiaveis.certLoad(filename=str(DIRNAME + '/cadeia-certificadora/certificados/' + certificado), format=xmlsec.KeyDataFormatPem, type=xmlsec.KeyDataTypeTrusted)

        #
        # Cria a variável de chamada (callable) da função de assinatura/verificação,
        # agora passando quais autoridades certificadoras são consideradas
        # confiáveis
        #
        verificador = xmlsec.DSigCtx(certificados_confiaveis)

        #
        # Separa o certificado que assinou o arquivo, e prepara a instância
        # com os dados desse certificado
        #
        certificado = xmlsec.findNode(noh_assinatura, xmlsec.NodeX509Certificate, xmlsec.DSigNs).content
        self.prepara_certificado_txt(certificado)

        #
        # Recupera a chave do certificado que assinou o documento, e altera
        # a data que será usada para fazer a verificação, para que a assinatura
        # seja validada mesmo que o certificado já tenha expirado
        # Para isso, define a data de validação para a data de início da validade
        # do certificado
        # Essa data deve ser informada como um inteiro tipo "unixtime"
        #
        noh_chave = xmlsec.findNode(noh_assinatura, xmlsec.NodeKeyInfo, xmlsec.DSigNs)
        manipulador_chave = xmlsec.KeyInfoCtx(mngr=certificados_confiaveis)
        manipulador_chave.certsVerificationTime = mktime(self.data_inicio_validade.timetuple())

        #
        # Cria uma chave vazia e recupera a chave, dizendo ao verificador que
        # é essa a chave que deve ser usada na validação da assinatura
        #
        verificador.signKey = xmlsec.Key()
        xmlsec.keyInfoNodeRead(noh_chave, verificador.signKey, manipulador_chave)

        #
        # Realiza a verificação
        #
        verificador.verify(noh_assinatura)

        #
        # Guarda o status
        #
        status = verificador.status
        resultado = status == xmlsec.DSigStatusSucceeded

        #
        # Libera a memória ocupada pelo verificador manualmente
        #
        verificador.destroy()
        certificados_confiaveis.destroy()

        if status != xmlsec.DSigStatusSucceeded:
            #
            # Libera a memória ocupada pelo documento xml manualmente
            #
            doc_xml.freeDoc()
            self._finaliza_funcoes_externas()
            raise RuntimeError('Erro ao validar a assinatura do arquivo; status: "' + str(status) + '"')

        #
        # Libera a memória ocupada pelo documento xml manualmente
        #
        doc_xml.freeDoc()
        self._finaliza_funcoes_externas()

        return resultado

    def assina_texto(self, texto, metodo=b'sha1'):
        #
        # Carrega o arquivo do certificado
        #
        pkcs12 = crypto.load_pkcs12(open(self.arquivo, 'rb').read(), self.senha)

        assinatura = crypto.sign(pkcs12.get_privatekey(), texto, metodo)
        assinatura = base64.encodestring(assinatura)
        assinatura = assinatura.replace('\n', '')

        return assinatura

    def verifica_assinatura_texto(self, texto, assinatura, methodo=b'sha1'):
        #
        # Carrega o arquivo do certificado
        #
        pkcs12 = crypto.load_pkcs12(open(self.arquivo, 'rb').read(), self.senha)

        try:
            assinatura = base64.decodestring(assinatura)
            crypto.verify(pkcs12.get_certificate(), assinatura, texto, metodo)
        except:
            return False

        return True
