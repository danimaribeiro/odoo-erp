# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


from .converte import gera_rps,le_envio_lote_rps

def envia_rps(lista_notas, numero_lote, certificado, producao=False):
    lote_rps = gera_rps(lista_notas, numero_lote, certificado)
        
    lote_rps.encode('utf-8')
    
    print(lote_rps)
    
    return lote_rps

def processar_retorno(xml):
    nfes = le_envio_lote_rps(xml)
    
    return nfes


