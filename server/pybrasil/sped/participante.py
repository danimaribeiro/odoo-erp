# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


import re
from ..inscricao import (valida_cnpj, valida_cpf, formata_cnpj, formata_cpf, valida_inscricao_estadual, formata_inscricao_estadual)
from ..ibge import (Local, Municipio, Estado, Pais, MUNICIPIO_ESTADO_NOME, MUNICIPIO_IBGE, MUNICIPIO_SIAFI, ESTADO_IBGE, ESTADO_SIGLA, PAIS_BACEN, PAIS_NOME, PAIS_BRASIL, PAIS_ISO_3166_2, PAIS_ISO_3166_3)
from ..base import tira_acentos
from ..telefone import formata_fone, valida_fone_fixo, valida_fone_internacional, valida_fone_celular


LIMPA = re.compile(r'[^0-9]')

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


REGIME_TRIBUTARIO_SIMPLES = 'SIMPLES'
REGIME_TRIBUTARIO_SIMPLES_EXCESSO = 'SIMPLES_EXCESSO'
REGIME_TRIBUTARIO_LUCRO_PRESUMIDO = 'LUCRO_PRESUMIDO'
REGIME_TRIBUTARIO_LUCRO_REAL = 'LUCRO_REAL'

REGIME_TRIBUTARIO = [
    REGIME_TRIBUTARIO_SIMPLES,
    REGIME_TRIBUTARIO_SIMPLES_EXCESSO,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO
]


class Participante(Local):
    def __init__(self, **kwargs):
        super(Participante, self).__init__(**kwargs)
        self.cnpj_cpf = kwargs.get('cnpj_cpf', '')
        self.nome = kwargs.get('nome', '')
        self.fantasia = kwargs.get('fantasia', self.nome)
        self.endereco = kwargs.get('endereco', '')
        self.numero = kwargs.get('numero', '')
        self.complemento = kwargs.get('complemento', '')
        self.bairro = kwargs.get('bairro', '')
        self.cep = kwargs.get('cep', '')
        self.email = kwargs.get('email', '')
        self.fone = kwargs.get('fone', '')
        self.celular = kwargs.get('celular', '')
        self.ie = kwargs.get('ie', '')
        self.im = kwargs.get('im', '')
        self.suframa = kwargs.get('suframa', '')
        self.regime_tributario = REGIME_TRIBUTARIO_SIMPLES

    @property
    def codigo(self):
        return self._cnpj_cpf

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

            elif valor[0:2] in ('NI', 'EX'):
                self._cnpj_cpf = valor

            else:
                self._cnpj_cpf = ''

        else:
            self._cnpj_cpf = ''

    @property
    def cnpj_cpf_numero(self):
        return LIMPA.sub('', self._cnpj_cpf)

    @property
    def tipo_pessoa(self):
        if self.cnpj_cpf[:2] == 'EX':
            return PESSOA_ESTRANGEIRA

        elif self.cnpj_cpf[:2] == 'NI':
            return PESSOA_NAO_IDENTIFICADA

        elif len(self.cnpj_cpf) == 18:
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
    def cep_numero(self):
        return LIMPA.sub('', self._cep)

    @property
    def endereco_completo(self):
        texto = self.endereco

        if self.numero:
            texto += ', ' + self.numero

        if self.complemento:
            texto += ' - ' + self.complemento

        #texto += '\n'

        #texto += self.bairro
        #texto += '\n' + self.municipio.nome + ' - ' + self.municipio.estado.sigla + ' - ' + self.cep

        return texto

    @property
    def ie(self):
        return self._ie

    @ie.setter
    def ie(self, valor):
        if self.estado.sigla:
            if valida_inscricao_estadual(valor, self.estado.sigla):
                self._ie = formata_inscricao_estadual(valor, self.estado.sigla)

            else:
                self._ie = ''

        else:
            self._ie = ''

    @property
    def ie_numero(self):
        if self._ie == '' or self.ie == 'ISENTO':
            return self._ie
        else:
            return LIMPA.sub('', self._ie)

    @property
    def suframa(self):
        return self._suframa

    @suframa.setter
    def suframa(self, valor):
        if valida_inscricao_estadual(valor, 'SUFRAMA'):
            self._suframa = formata_inscricao_estadual(valor, 'SUFRAMA')
        else:
            self._suframa = ''

    @property
    def endereco_completo_impressao(self):
        texto = self.endereco_completo.replace('\n', '<br/>')
        return texto

    @property
    def fone(self):
        return self._fone

    @fone.setter
    def fone(self, valor):
        if valida_fone_fixo(valor) or valida_fone_internacional(valor):
            self._fone = formata_fone(valor)
        else:
            self._fone = ''

    @property
    def fone_numero(self):
        return LIMPA.sub('', self._fone)

    @property
    def celular(self):
        return self._celular

    @celular.setter
    def celular(self, valor):
        if valida_fone_celular(valor) or valida_fone_internacional(valor):
            self._celular = formata_fone(valor)
        else:
            self._celular = ''

    @property
    def celular_numero(self):
        return LIMPA.sub('', self._celular)
