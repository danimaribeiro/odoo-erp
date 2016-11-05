# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from ...base import tira_acentos


class Remessa(object):
    def __init__(self):
        self.data_hora = None
        self.data_debito = None
        self.sequencia = 0
        self.boletos = []
        self.funcionarios = []
        self.holerites = []
        self.registros = []
        self.tipo = 'CNAB_400'
        self.valor_total = 0

    @property
    def arquivo_remessa(self):
        if len(self.boletos):
            boleto = self.boletos[0]
            banco = boleto.banco
        else:
            banco = self.beneficiario.banco

        self.registros = []

        if self.tipo == 'CNAB_400':
            header = banco.header_remessa_400(self).split(b'\n')
        elif self.tipo == 'CNAB_240':
            header = banco.header_remessa_240(self).split(b'\n')
        elif self.tipo == 'CNAB_200':
            header = banco.header_remessa_200(self).split(b'\n')
        elif self.tipo == 'CNAB_250':
            header = banco.header_remessa_250(self).split(b'\n')
        elif self.tipo == 'CNAB_500':
            header = banco.header_remessa_500(self).split(b'\n')

        if isinstance(header, list):
            self.registros += header
        else:
            self.registros += (header,)

        self.valor_total = 0

        for boleto in self.boletos:
            if self.tipo == 'CNAB_400':
                linhas = banco.linha_remessa_400(self, boleto).split(b'\n')
            elif self.tipo == 'CNAB_240':
                linhas = banco.linha_remessa_240(self, boleto).split(b'\n')

            self.valor_total += boleto.documento.valor

            if isinstance(linhas, list):
                self.registros += linhas
            else:
                self.registros += (linhas,)

        for funcionario in self.funcionarios:
            if self.tipo == 'CNAB_200':
                linhas = banco.linha_remessa_200(self, funcionario).split(b'\n')
            elif self.tipo == 'CNAB_240':
                linhas = banco.linha_remessa_240(self, funcionario).split(b'\n')

            self.valor_total += funcionario.valor_creditar

            if isinstance(linhas, list):
                self.registros += linhas
            else:
                self.registros += (linhas,)

        for holerite in self.holerites:
            if self.tipo == 'CNAB_250':
                linhas = banco.linha_remessa_250(self, holerite).split(b'\n')

            if isinstance(linhas, list):
                self.registros += linhas
            else:
                self.registros += (linhas,)

        if self.tipo == 'CNAB_400':
            trailler = banco.trailler_remessa_400(self).split(b'\n')
        elif self.tipo == 'CNAB_240':
            trailler = banco.trailler_remessa_240(self).split(b'\n')
        elif self.tipo == 'CNAB_200':
            trailler = banco.trailler_remessa_200(self).split(b'\n')
        elif self.tipo == 'CNAB_250':
            trailler = banco.trailler_remessa_250(self).split(b'\n')
        elif self.tipo == 'CNAB_500':
            trailler = banco.trailler_remessa_500(self).split(b'\n')

        if isinstance(trailler, list):
            self.registros += trailler
        else:
            self.registros += (trailler,)

        texto = b'\r\n'.join(self.registros) + b'\r\n'

        return texto
