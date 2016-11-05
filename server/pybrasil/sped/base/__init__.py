# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

#from .base_xml import ABERTURA, NAMESPACE_SIG, \
    #TagCaracter, TagData, TagDataHora, TagDecimal, TagHora, TagInteiro, \
    #TagDataHoraUTC, \
    #XMLNFe, tira_abertura, tirar_acentos, por_acentos, TagBoolean, somente_ascii, \
    #NAMESPACE_CTE


#from assinatura import Signature
from .assinatura import gera_assinatura, Signature
from .signature import SignatureType
from .certificado import Certificado, tira_abertura
from .conexao import ConexaoWebService, SOAP_12
