# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from ...base import tira_acentos
from .lista_banco import BANCO_CODIGO
from ..pessoa import Beneficiario
from .banco import Banco


class Retorno(object):
    def __init__(self):
        self.banco = Banco()
        self.beneficiario = Beneficiario()
        self.data_hora = None
        self.sequencia = 0
        self.boletos = []
        self.registros = []
        self.tipo = 'CNAB_400'
        self.linhas = []

    def arquivo_retorno(self, arquivo):
        if isinstance(arquivo, (str, unicode)):
            arquivo = open(arquivo, 'r')

        for linha in arquivo.readlines():
            self.linhas.append(linha.decode('iso-8859-1').replace('\n', '').replace('\r', ''))

        header = self.linhas[0]

        if len(header) != 400 and len(header) != 240:
            return False
            
        if header[:3] == '085':
            codigo_banco= '085'
            if len(header) == 240:
                self.tipo ="CNAB_240"
        else:
            codigo_banco = header[76:79]

        if not codigo_banco in BANCO_CODIGO:
            return False

        banco = BANCO_CODIGO[codigo_banco]
        self.banco = banco
        
        if self.tipo == "CNAB_400" and not hasattr(banco, 'header_retorno_400'):
            return False
        
        if self.tipo == "CNAB_240" and not hasattr(banco, 'header_retorno_240'):
            return False
        
        if self.tipo == "CNAB_400":
            
            banco.header_retorno_400(self)
    
            #if not self.beneficiario.nome:
                #return False
    
            banco.linha_retorno_400(self)
            
        elif self.tipo == "CNAB_240":
            
            banco.header_retorno_240(self)
                
            banco.linha_retorno_240(self)
    

        return True
