# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from lxml import etree
from .abertura import tira_abertura


class NohXML(object):
    def __init__(self, *args, **kwargs):
        self._arquivo_xml = None
        self.tags = {}
        self.sigla_ns = ''
        self.namespace = ''
        self.tag = ''
        self.nome = ''
        self.doctype = ''
        self.namespaces = {}
        self.noh_pai = None
        self.nohs_filhos = []
        self.propriedade = ''

        if 'tags' in kwargs:
            tags = kwargs.pop('tags')
        else:
            tags = {}

        for k, v in kwargs.items():
            setattr(self, k, v)

        if not self.tag:
            self.tag = self.nome

        self.tags = tags

    def le_xml(self, arquivo, codificacao='utf-8'):
        if not arquivo:
            return False

        if isinstance(arquivo, str):
            arquivo = arquivo.decode('utf-8')

        if not isinstance(arquivo, unicode):
            return False

        if '<' not in arquivo:
            arq = open(arquivo, 'rb')
            txt = b''.join(arq.readlines())
            arq.close()
            txt = txt.decode(codificacao)
            txt = tira_abertura(txt)
            txt = txt.encode('utf-8')

        else:
            txt = tira_abertura(arquivo)
            txt = txt.encode('utf-8')

        self.arquivo_xml = etree.fromstring(txt)
        self.valor = self.le_tag()

        return True

    def preenche_namespace(self, tag='', sigla_ns='', namespace=''):
        if not tag:
            tag = self.tag

        if not sigla_ns:
            sigla_ns = self.sigla_ns

        if not namespace:
            namespace = self.namespace

        tag = '//' + tag

        if sigla_ns and namespace:
            if not sigla_ns in self.namespaces:
                self.namespaces[sigla_ns] = namespace

            sigla_ns = '/' + sigla_ns + ':'
            tag = sigla_ns.join(tag.split('/'))
            tag = tag.replace(sigla_ns + sigla_ns, '/' + sigla_ns)

        return tag

    def le_nohs(self, tag='', sigla_ns='', namespace=''):
        if not tag:
            tag = self.tag

        if not sigla_ns:
            sigla_ns = self.sigla_ns

        if not namespace:
            namespace = self.namespace

        #
        # Tenta ler a tag sem os namespaces
        # Necessário para ler corretamente as tags de grupo reenraizadas
        #
        try:
            nohs = self.arquivo_xml.xpath('//' + tag)
            if len(nohs) >= 1:
                return nohs
        except:
            pass

        tag = self.preenche_namespace(tag, sigla_ns, namespace)

        nohs = self.arquivo_xml.xpath(tag, namespaces=self.namespaces)

        if len(nohs) >= 1:
            return nohs

        else:
            return None

    def le_noh(self, tag='', sigla_ns='', namespace='', ocorrencia=1):
        nohs = self.le_nohs(tag, sigla_ns, namespace)

        if (nohs is not None) and (len(nohs) >= ocorrencia):
            return nohs[ocorrencia - 1]

        else:
            return None

    def le_tag(self, ocorrencia=1):
        noh = self.le_noh(self.tag, self.sigla_ns, self.namespace, ocorrencia)

        if noh is None:
            return ''

        if self.propriedade and noh.attrib and (self.propriedade in noh.attrib):
            return noh.attrib[self.propriedade]

        return noh.text

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        if not isinstance(tags, dict):
            return

        self._tags = tags

        if not tags:
            return

        self.preenche_namespace(self.tag, self.sigla_ns, self.namespace)
        self._tags = tags
        self.__dict__.update(self.tags)
        for tag in self.tags:
            inst = getattr(self, tag)
            inst.nome = tag

            if self.tag:
                inst.tag = self.nome + '/' + inst.nome
            else:
                inst.tag = '/' + inst.nome

            inst.namespace = self.namespace
            inst.sigla_ns = self.sigla_ns
            inst.namespaces = self.namespaces
            self.preenche_namespace(self.tag, self.sigla_ns, self.namespace)

            if inst.tags:
                inst.tags = inst.tags

    @property
    def arquivo_xml(self):
        return self._arquivo_xml

    @arquivo_xml.setter
    def arquivo_xml(self, arquivo):
        self._arquivo_xml = arquivo
        for subtag in self.tags:
            self.tags[subtag].arquivo_xml = self.arquivo_xml
            self.tags[subtag].valor = self.tags[subtag].le_tag()


def teste():
    from collections import OrderedDict
    from pybrasil.xml import *


    cnr = NohXML(nome='consultarNotaResponse', sigla_ns='e', namespace='http://www.betha.com.br/e-nota-contribuinte-ws')
    lnfse = NohXML(nome='ListaNfse')
    complnfse = NohXML(nome='ComplNfse')
    nfse = NohXML(nome='Nfse')
    infnfse = NohXML(nome='InfNfse')
    numero = TagInteiro(nome='Numero')
    codver = TagCaracter(nome='Numero')
    demi = TagDataHoraUTC(nome='DataEmissao')

    cnr.tags = {
        'ListaNfse': NohXML(
            tags={
                'ComplNfse': NohXML(
                    tags={
                        'Nfse': NohXML(
                            tags={
                                'InfNfse': NohXML(
                                    tags={
                                        'Numero': TagInteiro(),
                                        'CodigoVerificacao': TagCaracter(),
                                        'DataEmissao': TagDataHoraUTC()
                                    }
                                 )
                            }
                        )
                    }
                )
            }
        )
    }


    cnr.le_xml('/home/ari/continental/LoteNfse_2381141521127972.xml', codificacao='iso-8859-1')
    #n.le_xml('/home/ari/openerp/PyBrasil/lote_rps.xml')


    #t = TagCaracter(tag='Cnpj', sigla_ns='e', namespace='http://www.betha.com.br/e-nota-contribuinte-ws')
    return cnr
