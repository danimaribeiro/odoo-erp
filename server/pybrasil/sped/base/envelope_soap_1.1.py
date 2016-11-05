# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

#from .base_xml import XMLNFe
from .signature import SignatureType, SignedInfoType, CanonicalizationMethod, SignatureMethod, ReferenceType, TransformsType, TransformType, DigestMethod, SignatureValueType, KeyInfoType, X509DataType
#import os


#DIRNAME = os.path.dirname(__file__)


def gera_assinatura(URI='#'):
    if not URI:
        URI = '#'

    if URI[0] != '#':
        URI = '#' + URI

    signature = SignatureType()
    signature.SignedInfo = SignedInfoType()
    signature.SignedInfo.CanonicalizationMethod = CanonicalizationMethod()
    signature.SignedInfo.CanonicalizationMethod.Algorithm = b'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    signature.SignedInfo.SignatureMethod = SignatureMethod()
    signature.SignedInfo.SignatureMethod.Algorithm = b'http://www.w3.org/2000/09/xmldsig#rsa-sha1'
    signature.SignedInfo.Reference = ReferenceType()
    signature.SignedInfo.Reference.URI = URI

    signature.SignedInfo.Reference.Transforms = TransformsType()
    t1 = TransformType()
    t1.Algorithm = b'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
    signature.SignedInfo.Reference.Transforms.add_Transform(t1)
    t2 = TransformType()
    t2.Algorithm = b'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    signature.SignedInfo.Reference.Transforms.add_Transform(t2)

    signature.SignedInfo.Reference.DigestMethod = DigestMethod()
    signature.SignedInfo.Reference.DigestMethod.Algorithm = b'http://www.w3.org/2000/09/xmldsig#sha1'
    signature.SignedInfo.Reference.DigestValue = ''


    signature.SignatureValue = SignatureValueType()
    signature.KeyInfo = KeyInfoType()
    signature.KeyInfo.X509Data = X509DataType()
    signature.KeyInfo.X509Data.X509Certificate = ''

    return signature


#class Signature(XMLNFe):
    #def __init__(self):
        #super(Signature, self).__init__()
        #self.URI = ''
        #self.DigestValue = ''
        #self.SignatureValue = ''
        #self.X509Certificate = ''
        #self.caminho_esquema = os.path.join(DIRNAME, 'schema/')
        #self.arquivo_esquema = 'xmldsig-core-schema_v1.01.xsd'

    #def get_xml(self):
        #if not len(self.URI):
            #self.URI = '#'

        #if self.URI[0] != '#':
            #self.URI = '#' + self.URI

        #xml  = '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">'
        #xml +=     '<SignedInfo>'
        #xml +=         '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
        #xml +=         '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />'
        #xml +=         '<Reference URI="' + self.URI + '">'
        #xml +=             '<Transforms>'
        #xml +=                 '<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature" />'
        #xml +=                 '<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />'
        #xml +=             '</Transforms>'
        #xml +=             '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />'
        #xml +=             '<DigestValue>' + self.DigestValue + '</DigestValue>'
        #xml +=         '</Reference>'
        #xml +=     '</SignedInfo>'
        #xml +=     '<SignatureValue>' + self.SignatureValue + '</SignatureValue>'
        #xml +=     '<KeyInfo>'
        #xml +=         '<X509Data>'
        #xml +=             '<X509Certificate>' + self.X509Certificate + '</X509Certificate>'
        #xml +=         '</X509Data>'
        #xml +=     '</KeyInfo>'
        #xml += '</Signature>'
        #return xml

    #def set_xml(self, arquivo):
        #if self._le_xml(arquivo):
            #self.URI = self._le_tag('//sig:Signature/sig:SignedInfo/sig:Reference', 'URI') or ''
            #self.DigestValue = self._le_tag('//sig:Signature/sig:SignedInfo/sig:Reference/sig:DigestValue') or ''
            #self.SignatureValue = self._le_tag('//sig:Signature/sig:SignatureValue') or ''
            #self.X509Certificate = self._le_tag('//sig:Signature/sig:KeyInfo/sig:X509Data/sig:X509Certificate') or ''
        #return self.xml

    #xml = property(get_xml, set_xml)
