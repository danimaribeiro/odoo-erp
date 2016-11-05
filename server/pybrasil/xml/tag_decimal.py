# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from decimal import Decimal as D
from .tag_inteiro import TagInteiro
from ..valor import formata_valor, valor_por_extenso, valor_por_extenso_unidade


class TagDecimal(TagInteiro):
    def __init__(self, *args, **kwargs):
        super(TagDecimal, self).__init__(*args, **kwargs)
        self.valor = 0
        self.precisao_decimal = 2
        self.unidade = None
        self.genero_unidade_masculino = True
        self.unidade_decimal = None
        self.genero_unidade_decimal_masculino = True
        self.arredonda = True

    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, valor):
        if valor:
            if isinstance(valor, str):
                self.valor = valor.decode('utf-8')

            elif isinstance(valor, unicode):
                self.valor = D(valor)

            elif isinstance(valor, (int, float)):
                self.valor = D(str(valor))

            elif isinstance(valor, D):
                if self.arredonda:
                    ajuste_arredonda = '1'.zfill(self.precisao_decimal + 1)
                    ajuste_arredonda = ajuste_arredonda[0] + '.' + ajuste_arredonda[1:]
                    valor = valor.quantize(D(ajuste_arredonda))

                self._valor = valor
                self._texto = str(self.valor)

        else:
            self._valor = 0
            self._texto = str(self.valor)

    @property
    def formatado(self):
        return formata_valor(self.valor, casas_decimais=self.precisao_decimal)

    @property
    def extenso(self):
        if isinstance(self.unidade, (list, tuple)):
            return valor_por_extenso_unidade(numero=self.valor, unidade=self.unidade, genero_unidade_masculino=self.genero_unidade_masculino, unidade_decimal=self.unidade_decimal, genero_unidade_decimal_masculino=self.genero_unidade_decimal_masculino, precisao_decimal=self.precisao_decimal)
        else:
            return valor_por_extenso(self.valor)


class TagDinheiro(TagDecimal):
    def __init__(self, *args, **kwargs):
        super(TagDinheiro, self).__init__(*args, **kwargs)
        self.valor = 0
        self.precisao_decimal = 2
        self.unidade = ('real', 'reais')
        self.genero_unidade_masculino = True
        self.unidade_decimal = ('centavo', 'centavos')
        self.genero_unidade_decimal_masculino = True
        self.arredonda = True
