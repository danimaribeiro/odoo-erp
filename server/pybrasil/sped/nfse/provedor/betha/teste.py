# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .....base import DicionarioBrasil, xml_para_dicionario


#from StringIO import StringIO
#from ....base import gera_assinatura, tira_abertura
#from ...nfse import *
#from .servico_consultar_lote_rps_envio_v01 import *
#from .servico_consultar_lote_rps_envio_v01 import parseString
#from decimal import Decimal as D
#from ....participante import REGIME_TRIBUTARIO_SIMPLES


def Signature():
    xml  = '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">'
    xml +=     '<SignedInfo>'
    xml +=         '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
    xml +=         '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />'
    xml +=         '<Reference URI="#">'
    xml +=             '<Transforms>'
    xml +=                 '<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature" />'
    xml +=                 '<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
    xml +=             '</Transforms>'
    xml +=             '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />'
    xml +=             '<DigestValue></DigestValue>'
    xml +=         '</Reference>'
    xml +=     '</SignedInfo>'
    xml +=     '<SignatureValue></SignatureValue>'
    xml +=     '<KeyInfo>'
    xml +=         '<X509Data>'
    xml +=             '<X509Certificate></X509Certificate>'
    xml +=         '</X509Data>'
    xml +=     '</KeyInfo>'
    xml += '</Signature>'
    return xml_para_dicionario(xml)
