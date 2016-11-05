# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from imp import load_source
import os
import sys
import types
from .banco import Banco


CURDIR = os.path.dirname(os.path.abspath(__file__))


def _monta_dicionario_codigo():
    dicionario = {}

    arquivo = open(os.path.join(CURDIR, 'banco.txt'), 'r')

    #
    # Pula a primeira linha
    #
    arquivo.readline()

    for linha in arquivo:
        linha = linha.decode('utf-8').replace('\n', '').replace('\r', '')
        campos = linha.split('|')
        codigo = campos[0]
        nome = campos[1]

        arquivo_classe = os.path.join(CURDIR, 'banco_' + codigo + '.py')

        b = Banco(codigo, nome)

        if os.path.exists(arquivo_classe):
            modulo = load_source('banco_' + codigo, arquivo_classe)

            if hasattr(modulo, 'campo_livre'):
                b.campo_livre = types.MethodType(getattr(modulo, 'campo_livre'), b)

            if hasattr(modulo, 'calcula_digito_nosso_numero'):
                b.calcula_digito_nosso_numero = types.MethodType(getattr(modulo, 'calcula_digito_nosso_numero'), b)

            if hasattr(modulo, 'fator_vencimento'):
                b.fator_vencimento = types.MethodType(getattr(modulo, 'fator_vencimento'), b)

            if hasattr(modulo, 'header_remessa_240'):
                b.header_remessa_240 = types.MethodType(getattr(modulo, 'header_remessa_240'), b)

            if hasattr(modulo, 'trailler_remessa_240'):
                b.trailler_remessa_240 = types.MethodType(getattr(modulo, 'trailler_remessa_240'), b)

            if hasattr(modulo, 'linha_remessa_240'):
                b.linha_remessa_240 = types.MethodType(getattr(modulo, 'linha_remessa_240'), b)
                
            if hasattr(modulo, 'header_retorno_240'):
                b.header_retorno_240 = types.MethodType(getattr(modulo, 'header_retorno_240'), b)

            if hasattr(modulo, 'trailler_retorno_240'):
                b.trailler_retorno_240 = types.MethodType(getattr(modulo, 'trailler_retorno_240'), b)

            if hasattr(modulo, 'linha_retorno_240'):
                b.linha_retorno_240 = types.MethodType(getattr(modulo, 'linha_retorno_240'), b)
                
            if hasattr(modulo, 'fp_header_retorno_240'):
                b.fp_header_retorno_240 = types.MethodType(getattr(modulo, 'fp_header_retorno_240'), b)

            if hasattr(modulo, 'fp_trailler_retorno_240'):
                b.fp_trailler_retorno_240 = types.MethodType(getattr(modulo, 'fp_trailler_retorno_240'), b)

            if hasattr(modulo, 'fp_linha_retorno_240'):
                b.fp_linha_retorno_240 = types.MethodType(getattr(modulo, 'fp_linha_retorno_240'), b)
            
            if hasattr(modulo, 'header_remessa_400'):
                b.header_remessa_400 = types.MethodType(getattr(modulo, 'header_remessa_400'), b)

            if hasattr(modulo, 'trailler_remessa_400'):
                b.trailler_remessa_400 = types.MethodType(getattr(modulo, 'trailler_remessa_400'), b)

            if hasattr(modulo, 'linha_remessa_400'):
                b.linha_remessa_400 = types.MethodType(getattr(modulo, 'linha_remessa_400'), b)

            if hasattr(modulo, 'header_retorno_400'):
                b.header_retorno_400 = types.MethodType(getattr(modulo, 'header_retorno_400'), b)

            if hasattr(modulo, 'trailler_retorno_400'):
                b.trailler_retorno_400 = types.MethodType(getattr(modulo, 'trailler_retorno_400'), b)

            if hasattr(modulo, 'linha_retorno_400'):
                b.linha_retorno_400 = types.MethodType(getattr(modulo, 'linha_retorno_400'), b)

            if hasattr(modulo, 'DESCRICAO_COMANDO_REMESSA'):
                b.descricao_comandos_remessa = getattr(modulo, 'DESCRICAO_COMANDO_REMESSA')

            if hasattr(modulo, 'DESCRICAO_COMANDO_RETORNO'):
                b.descricao_comandos_retorno = getattr(modulo, 'DESCRICAO_COMANDO_RETORNO')

            if hasattr(modulo, 'COMANDOS_RETORNO_LIQUIDACAO'):
                b.comandos_liquidacao = getattr(modulo, 'COMANDOS_RETORNO_LIQUIDACAO')

            if hasattr(modulo, 'COMANDOS_RETORNO_BAIXA'):
                b.comandos_baixa = getattr(modulo, 'COMANDOS_RETORNO_BAIXA')

            if hasattr(modulo, 'header_remessa_200'):
                b.header_remessa_200 = types.MethodType(getattr(modulo, 'header_remessa_200'), b)

            if hasattr(modulo, 'trailler_remessa_200'):
                b.trailler_remessa_200 = types.MethodType(getattr(modulo, 'trailler_remessa_200'), b)

            if hasattr(modulo, 'linha_remessa_200'):
                b.linha_remessa_200 = types.MethodType(getattr(modulo, 'linha_remessa_200'), b)

            if hasattr(modulo, 'header_remessa_250'):
                b.header_remessa_250 = types.MethodType(getattr(modulo, 'header_remessa_250'), b)
                
            if hasattr(modulo, 'trailler_remessa_250'):
                b.trailler_remessa_250 = types.MethodType(getattr(modulo, 'trailler_remessa_250'), b)
            
            if hasattr(modulo, 'linha_remessa_250'):
                b.linha_remessa_250 = types.MethodType(getattr(modulo, 'linha_remessa_250'), b)

            if hasattr(modulo, 'header_remessa_500'):
                b.header_remessa_500 = types.MethodType(getattr(modulo, 'header_remessa_500'), b)
                
            if hasattr(modulo, 'trailler_remessa_500'):
                b.trailler_remessa_500 = types.MethodType(getattr(modulo, 'trailler_remessa_500'), b)
            
            #if hasattr(modulo, 'linha_remessa_500'):
                #b.linha_remessa_500 = types.MethodType(getattr(modulo, 'linha_remessa_500'), b)
                
            if hasattr(modulo, 'carteira_nosso_numero'):
                b.carteira_nosso_numero = types.MethodType(getattr(modulo, 'carteira_nosso_numero'), b)

            if hasattr(modulo, 'agencia_conta'):
                b.agencia_conta = types.MethodType(getattr(modulo, 'agencia_conta'), b)

            if hasattr(modulo, 'imprime_carteira'):
                b.imprime_carteira = types.MethodType(getattr(modulo, 'imprime_carteira'), b)

        dicionario[b.codigo] = b

    return dicionario


if not hasattr(sys.modules[__name__], 'BANCO_CODIGO'):
    BANCO_CODIGO = _monta_dicionario_codigo()
