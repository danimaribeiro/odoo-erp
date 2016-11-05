# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

import os
import base64
from datetime import date
from ...base import modulo11, modulo10, tira_acentos

CURDIR = os.path.dirname(os.path.abspath(__file__))


class Banco(object):
    def __init__(self, codigo='', nome=''):
        self.codigo = codigo
        self.nome = nome
        self.arquivo_logo = os.path.join(CURDIR, 'logo', codigo + '.jpg')

        if os.path.exists(self.arquivo_logo):
            self.logo = base64.b64encode(open(self.arquivo_logo, 'rb').read())
        else:
            self.logo = None
            self.arquivo_logo = ''

        self.carteira = ''
        self.modalidade = ''
        self.modulo10 = modulo10
        self.modulo11 = modulo11
        self.tira_acentos = tira_acentos
        self.descricao_comandos_remessa = {}
        self.descricao_comandos_retorno = {}
        self.comandos_liquidacao = {}
        self.comandos_baixa = []

    def __str__(self):
        return unicode.encode(self.__unicode__(), 'utf-8')

    def __unicode__(self):
        return self.nome + ' - ' + self.codigo

    def __repr__(self):
        return str(self)

    @property
    def digito(self):
        if self.codigo in ['748']:
            return 'X'
        elif self.codigo in ['085']:
            return '1'
        else:
            return modulo11(self.codigo)

    @property
    def codigo_digito(self):
        return '%s-%s' % (self.codigo.zfill(3), self.digito)

    def fator_vencimento(self, boleto):
        fator_vencimento = boleto.data_vencimento - date(1997, 10, 7)
        return fator_vencimento.days

    def calcula_digito_codigo_barras(self, codigo_barras):
        return modulo11(codigo_barras, mapa_digitos={0: 1, 1: 1, 10: 1, 11: 1})

    def calcula_digito_nosso_numero(self, boleto):
        return self.modulo10(boleto.nosso_numero)

    def campo_livre(self, boleto):
        return ''

    def carteira_nosso_numero(self, boleto):
        return '%s/%s-%s' % (boleto.banco.carteira, boleto.nosso_numero, boleto.digito_nosso_numero)

    def agencia_conta(self, boleto):
        if boleto.beneficiario.conta.digito:
            return '%s/%s-%s' % (boleto.beneficiario.agencia.numero, boleto.beneficiario.conta.numero, boleto.beneficiario.conta.digito)

        else:
            return '%s/%s' % (boleto.beneficiario.agencia.numero, boleto.beneficiario.conta.numero)

    def agencia_codigo_beneficiario(self, boleto):
        if boleto.beneficiario.codigo_beneficiario.digito:
            return '%s/%s-%s' % (boleto.beneficiario.agencia.numero, boleto.beneficiario.codigo_beneficiario.numero, boleto.beneficiario.codigo_beneficiario.digito)

        else:
            return '%s/%s' % (boleto.beneficiario.agencia.numero, boleto.beneficiario.codigo_beneficiario.numero)

    def imprime_carteira(self, boleto):
        return boleto.banco.carteira