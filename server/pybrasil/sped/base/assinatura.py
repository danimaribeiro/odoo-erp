# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

#from .base_xml import XMLNFe
#from .signature import SignatureType, SignedInfoType, CanonicalizationMethod, SignatureMethod, ReferenceType, TransformsType, TransformType, DigestMethod, SignatureValueType, KeyInfoType, X509DataType
#import os
from ...base import xml_para_dicionario


#DIRNAME = os.path.dirname(__file__)

def Signature():
    xml = '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">'
    xml += '<SignedInfo>'
    xml += '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
    xml += '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />'
    xml += '<Reference URI="#">'
    xml += '<Transforms>'
    xml += '<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature" />'
    xml += '<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
    xml += '</Transforms>'
    xml += '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />'
    xml += '<DigestValue></DigestValue>'
    xml += '</Reference>'
    xml += '</SignedInfo>'
    xml += '<SignatureValue></SignatureValue>'
    xml += '<KeyInfo>'
    xml += '<X509Data>'
    xml += '<X509Certificate></X509Certificate>'
    xml += '</X509Data>'
    xml += '</KeyInfo>'
    xml += '</Signature>'
    return xml_para_dicionario(xml)


def gera_assinatura(URI='#', ignora_uri=False):
    if not ignora_uri:
        if not URI:
            URI = '#'

        if URI[0] != '#':
            URI = '#' + URI

    assinatura = Signature()
    assinatura.Signature.SignedInfo.Reference.__URI = URI
    return assinatura.Signature
