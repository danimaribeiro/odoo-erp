# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from pysped.xml_sped import (ABERTURA, Signature, TagCaracter,
                             TagDataHoraUTC, TagDecimal, TagInteiro, XMLNFe)
import os

DIRNAME = os.path.dirname(__file__)

NAMESPACE_NFSE_BETHA = 'http://www.betha.com.br/e-nota-contribuinte-ws'


class RPS(XMLNFe):
    def __init__(self):
        super(RPS, self).__init__()
        self.infRPS = InfRPS()
        self.Signature = Signature()

    def get_xml(self):
        xml = XMLNFe.get_xml(self)
        xml += ABERTURA
        xml += '<Rps xmlns="http://www.betha.com.br/e-nota-contribuinte-ws">'
        xml += self.infRPS.xml

        #
        # Define a URI a ser assinada
        #
        self.Signature.URI = '#' + self.infRPS.Id.valor

        xml += self.Signature.xml
        xml += '</Rps>'
        return xml

    def set_xml(self, arquivo):
        if self._le_xml(arquivo):
            self.infRPS.xml    = arquivo
            self.Signature.xml = self._le_noh('//Rps/sig:Signature')

    xml = property(get_xml, set_xml)


class InfRPS(XMLNFe):
    def __init__(self):
        super(InfRPS, self).__init__()
        self.Id       = TagCaracter(nome='infRps', propriedade='Id', raiz='//Rps', namespace=NAMESPACE_NFSE_BETHA)
        #self.IdentificacaoRPS = Ide()
        self.DataEmissao = TagDataHoraUTC(nome='DataEmissao', raiz='//Rps/InfRps')
        self.NaturezaOperacao = TagCaracter(nome='NaturezaOperacao', raiz='//Rps/InfRps')
        self.OptanteSimplesNacional = TagCaracter(nome='OptanteSimplesNacional', raiz='//Rps/InfRps')
        self.IncentivadorCultural = TagCaracter(nome='IncentivadorCultural', raiz='//Rps/InfRps')
        self.Status = TagCaracter(nome='Status', raiz='//Rps/InfRps')

    def get_xml(self):
        xml = XMLNFe.get_xml(self)
        xml += '<infRps Id="' + self.Id.valor + '">'
        xml += self.DataEmissao.xml
        xml += self.NaturezaOperacao.xml
        xml += self.OptanteSimplesNacional.xml
        xml += self.IncentivadorCultural.xml
        xml += self.Status.xml
        xml += '</infRps>'
        return xml

    def set_xml(self, arquivo):
        if self._le_xml(arquivo):
            self.Id.xml = arquivo
            self.DataEmissao.xml = arquivo
            self.NaturezaOperacao.xml = arquivo
            self.OptanteSimplesNacional.xml = arquivo
            self.IncentivadorCultural.xml = arquivo
            self.Status.xml = arquivo

            #
            # Técnica para leitura de tags múltiplas
            # As classes dessas tags, e suas filhas, devem ser
            # "reenraizadas" (propriedade raiz) para poderem ser
            # lidas corretamente
            #
            #self.det = self.le_grupo('//NFe/infNFe/det', Det)

    xml = property(get_xml, set_xml)
