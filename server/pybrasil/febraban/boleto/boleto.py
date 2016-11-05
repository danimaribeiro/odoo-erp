# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from ...base import modulo10
from ..pessoa import Beneficiario, Pagador
from ..banco import Banco
from ...valor import formata_valor


class Documento(object):
    def __init__(self):
        self.numero = ''
        self.data = None
        self.valor = 0
        self.especie = 'DM'
        self.numero_original = ''

    @property
    def data_formatada(self):
        if self.data:
            return self.data.strftime(b'%d/%m/%Y')
        else:
            return ''

    @property
    def valor_formatado(self):
        return formata_valor(self.valor)


class Boleto(object):
    def __init__(self, **kwargs):
        self.banco = Banco()
        self.beneficiario = Beneficiario()
        self.pagador = Pagador()

        self.local_pagamento = 'Pagável em qualquer banco até o vencimento'
        self.aceite = 'N'
        self.moeda = '9'
        self.especie = 'R$'
        self.parcela = 1
        self.total_parcelas = 1

        self.nosso_numero = ''
        self.identificacao = ''

        self.documento = Documento()

        self.data_vencimento = None
        self.data_processamento = None
        self.data_ocorrencia = None
        self.data_credito = None
        self.data_abatimento = None
        self.data_desconto = None
        self.data_juros = None
        self.data_multa = None
        self.dias_protesto = 0
        self.dias_baixa = 0
        self.dias_atraso = 0
        self.data_protesto = None
        self.data_baixa = None
        self.comando = ''
        self.motivo = ''

        self.valor_despesa_cobranca = 0
        self.valor_abatimento = 0
        self.valor_desconto = 0
        self.valor_juros = 0
        self.percentual_juros = 0
        self.valor_multa = 0
        self.percentual_multa = 0
        self.valor_iof = 0
        self.valor_outras_despesas = 0
        self.valor_outros_creditos = 0
        self.valor_recebido = 0

        self.imprime_desconto = 0
        self.imprime_juros_multa = 0
        self.imprime_outras_deducoes = 0
        self.imprime_outros_acrescimos = 0
        self.imprime_valor_cobrado = 0

        self.pagamento_duplicado = False

        self.descricao = []
        self.instrucoes = []

    @property
    def imprime_desconto_formatado(self):
        if self.imprime_desconto:
            return formata_valor(self.imprime_desconto)
        else:
            return u''

    @property
    def imprime_juros_multa_formatado(self):
        if self.imprime_juros_multa:
            return formata_valor(self.imprime_juros_multa)
        else:
            return u''

    @property
    def imprime_outras_deducoes_formatado(self):
        if self.imprime_outras_deducoes:
            return formata_valor(self.imprime_outras_deducoes)
        else:
            return u''

    @property
    def imprime_outros_acrescimos_formatado(self):
        if self.imprime_outros_acrescimos:
            return formata_valor(self.imprime_outros_acrescimos)
        else:
            return u''

    @property
    def imprime_valor_cobrado_formatado(self):
        if self.imprime_valor_cobrado:
            return formata_valor(self.imprime_valor_cobrado)
        else:
            return u''

    @property
    def data_vencimento_formatada(self):
        return self.data_vencimento.strftime(b'%d/%m/%Y')

    @property
    def data_processamento_formatada(self):
        if self.data_processamento:
            return self.data_processamento.strftime(b'%d/%m/%Y')
        else:
            return ''

    @property
    def digito_nosso_numero(self):
        return self.banco.calcula_digito_nosso_numero(self)

    @property
    def codigo_barras(self):
        """Essa função sempre é a mesma para todos os bancos. Então basta
        implementar o método :func:`barcode` para o pyboleto calcular a linha
        digitável.

        Posição  #   Conteúdo
        01 a 03  03  Número do banco
        04       01  Código da Moeda - 9 para Real
        05       01  Digito verificador do Código de Barras
        06 a 09  04  Data de vencimento em dias partis de 07/10/1997
        10 a 19  10  Valor do boleto (8 inteiros e 2 decimais)
        20 a 44  25  Campo Livre definido por cada banco
        Total    44
        """
        codigo_barras = str(self.banco.codigo or '0').zfill(3)
        codigo_barras += str(self.moeda or '9').zfill(1)
        codigo_barras += str(self.banco.fator_vencimento(self) or '0').zfill(4)
        codigo_barras += str(int((self.documento.valor * 100) or 0)).zfill(10)
        codigo_barras += str(self.banco.campo_livre(self)).zfill(25)

        dv = self.banco.calcula_digito_codigo_barras(codigo_barras)

        #
        # Insere o dígito verificador na 5ª posição do código
        #
        codigo_barras = codigo_barras[:4] + dv + codigo_barras[4:]

        return codigo_barras

    @property
    def linha_digitavel(self):
        campo_1 = self.codigo_barras[0:4] + self.codigo_barras[19:24]
        campo_2 = self.codigo_barras[24:34]
        campo_3 = self.codigo_barras[34:44]
        campo_4 = self.codigo_barras[4]
        campo_5 = self.codigo_barras[5:19]

        #print('campo_1', campo_1)
        #print('campo_2', campo_2)
        #print('campo_3', campo_3)
        #print('campo_4', campo_4)
        #print('campo_5', campo_5)

        #
        # Pelos manuais, o correto seria modulo=True, mas os boletos
        # que já estão sendo gerados estão assim...
        #
        campo_1 += str(modulo10(campo_1, modulo=False))
        campo_2 += str(modulo10(campo_2, modulo=False))
        campo_3 += str(modulo10(campo_3, modulo=False))

        campo_1 = campo_1[:5] + '.' + campo_1[5:]
        campo_2 = campo_2[:5] + '.' + campo_2[5:]
        campo_3 = campo_3[:5] + '.' + campo_3[5:]
        #campo_5 = campo_5[:7] + '.' + campo_5[7:]

        return ' '.join([campo_1, campo_2, campo_3, campo_4, campo_5])

    @property
    def descricao_impressao(self):
        return '<br/>'.join(self.descricao)

    @property
    def instrucoes_impressao(self):
        return '<br/>'.join(self.instrucoes)

    @property
    def comando_remessa_descricao(self):
        if self.comando in self.banco.descricao_comandos_remessa:
            return self.banco.descricao_comandos_remessa[self.comando]
        else:
            return self.comando

    @property
    def comando_retorno_descricao(self):
        if self.comando in self.banco.descricao_comandos_retorno:
            return self.banco.descricao_comandos_retorno[self.comando]
        else:
            return self.comando

    @property
    def comando_remessa_descricao_grupo(self):
        if self.comando in self.banco.descricao_comandos_remessa:
            return self.comando + ' - ' + self.banco.descricao_comandos_remessa[self.comando]
        else:
            return self.comando

    @property
    def comando_retorno_descricao_grupo(self):
        if self.comando in self.banco.descricao_comandos_retorno:
            return self.comando + ' - ' + self.banco.descricao_comandos_retorno[self.comando]
        else:
            return self.comando

    @property
    def imprime_carteira_nosso_numero(self):
        #print('passou aqui também', self.banco.carteira_nosso_numero(self))
        return self.banco.carteira_nosso_numero(self)

    @property
    def imprime_agencia_conta(self):
        #print('passou aqui', self.banco.agencia_conta(self))
        return self.banco.agencia_conta(self)

    @property
    def imprime_agencia_beneficiario(self):
        return self.banco.agencia_beneficiario(self)

    @property
    def imprime_carteira(self):
        return self.banco.imprime_carteira(self)
