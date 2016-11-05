# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from ..inscricao import (valida_cnpj, valida_cpf, formata_cnpj, formata_cpf, limpa_formatacao)
from .banco import Banco
from ..data import hoje


PESSOA_JURIDICA = 'PJ'
PESSOA_FISICA = 'PF'
PESSOA_ESTRANGEIRA = 'EX'
PESSOA_NAO_IDENTIFICADA = 'NI'

TIPO_PESSOA = [
    PESSOA_JURIDICA,
    PESSOA_FISICA,
    PESSOA_ESTRANGEIRA,
    PESSOA_NAO_IDENTIFICADA,
]


class Pagador(object):
    def __init__(self, **kwargs):
        self.cnpj_cpf = kwargs.get('cnpj_cpf', '')
        self.nome = kwargs.get('nome', '')
        self.endereco = kwargs.get('endereco', '')
        self.numero = kwargs.get('numero', '')
        self.complemento = kwargs.get('complemento', '')
        self.bairro = kwargs.get('bairro', '')
        self.cidade = kwargs.get('cidade', '')
        self.estado = kwargs.get('estado', '')
        self.cep = kwargs.get('cep', '')
        self.email = kwargs.get('email', '')
        self.fone = kwargs.get('fone', '')

    @property
    def cnpj_cpf(self):
        return self._cnpj_cpf

    @cnpj_cpf.setter
    def cnpj_cpf(self, valor):
        if valor:
            if valida_cnpj(valor):
                self._cnpj_cpf = formata_cnpj(valor)

            elif valida_cpf(valor):
                self._cnpj_cpf = formata_cpf(valor)

            else:
                self._cnpj_cpf = ''

        else:
            self._cnpj_cpf = ''

    @property
    def cnpj_cpf_numero(self):
        return limpa_formatacao(self._cnpj_cpf)

    @property
    def tipo_pessoa(self):
        if len(self.cnpj_cpf) == 18:
            return PESSOA_JURIDICA
        else:
            return PESSOA_FISICA

    @property
    def cep(self):
        return self._cep

    @cep.setter
    def cep(self, valor):
        if valor:
            self._cep = valor
            #self._cep = funcao.valida_cep(valor)
        else:
            self._cep = ''

    @property
    def endereco_numero_complemento(self):
        texto = self.endereco

        if self.numero:
            texto += ', ' + self.numero

        if self.complemento:
            texto += ' - ' + self.complemento

        return texto

    @property
    def endereco_completo(self):
        texto = self.endereco_numero_complemento
        texto += '\n'

        texto += self.bairro + ' - ' + self.cidade + ' - ' + self.estado + ' - ' + self.cep

        return texto

    @property
    def endereco_completo_uma_linha(self):
        texto = self.endereco_numero_complemento
        texto += ' - '
        texto += self.bairro + ' - ' + self.cidade + ' - ' + self.estado + ' - ' + self.cep

        return texto

    @property
    def impressao(self):
        texto = self.nome + '\n'
        texto += self.endereco_completo
        return texto.replace('\n', '<br/>')

    @property
    def impressao_sacador(self):
        if not (self.nome and self.cnpj_cpf):
            return ''

        texto = self.nome
        texto += ' - CNPJ ' + self.cnpj_cpf
        texto += '\n'
        texto += self.endereco_completo_uma_linha
        return texto.replace('\n', '<br/>')


class NumeroDigito(object):
    def __init__(self, numero='', digito=''):
        self.numero = numero
        self.digito = digito


class Beneficiario(Pagador):
    def __init__(self, **kwargs):
        super(Beneficiario, self).__init__(**kwargs)
        self.banco = Banco()
        self.agencia = NumeroDigito()
        self.conta = NumeroDigito()
        self.codigo_beneficiario = NumeroDigito()

    @property
    def agencia_conta(self):
        if self.conta.digito:
            return '%s/%s-%s' % (self.agencia.numero, self.conta.numero, self.conta.digito)

        else:
            return '%s/%s' % (self.agencia.numero, self.conta.numero)

    @property
    def agencia_codigo_beneficiario(self):
        if self.codigo_beneficiario.digito:
            return '%s/%s-%s' % (self.agencia.numero, self.codigo_beneficiario.numero, self.codigo_beneficiario.digito)

        else:
            return '%s/%s' % (self.agencia.numero, self.codigo_beneficiario.numero)

    @property
    def nome_cnpj(self):
        return '%s - %s' % (self.nome, self.cnpj_cpf)


class Funcionario(Beneficiario):
    def __init__(self, **kwargs):
        super(Funcionario, self).__init__(**kwargs)
        self.valor_creditar = 0
        self.matricula = ''
        self.holerite_id = ''
        self.nis = ''
        self.rg = ''
        self.carteira_trabalho = ''
        self.funcao = ''
        self.registro = 0
        self.sequencia_arquivo = 0
        self.data_admissao = hoje()
