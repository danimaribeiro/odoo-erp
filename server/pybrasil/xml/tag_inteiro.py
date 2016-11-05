# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from .tag_caracter import TagCaracter
from ..valor import formata_valor, valor_por_extenso, valor_por_extenso_unidade


class TagInteiro(TagCaracter):
    def __init__(self, *args, **kwargs):
        super(TagInteiro, self).__init__(*args, **kwargs)
        self.valor = 0
        self.unidade = None
        self.genero_unidade_masculino = True

    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, valor):
        if valor:
            if isinstance(valor, str):
                self.valor = valor.decode('utf-8')

            elif isinstance(valor, unicode):
                self.valor = int(valor)

            elif isinstance(valor, int):
                self._valor = valor
                self._texto = str(self.valor)

        else:
            self._valor = 0
            self._texto = str(self.valor)

    @property
    def formatado(self):
        return formata_valor(self.valor, casas_decimais=0)

    @property
    def extenso(self):
        if isinstance(self.unidade, (list, tuple)):
            return valor_por_extenso_unidade(numero=self.valor, unidade=self.unidade, genero_unidade_masculino=self.genero_unidade_masculino)
        else:
            return valor_por_extenso(self.valor)
