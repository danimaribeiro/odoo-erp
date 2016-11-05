# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from .tag_caracter import TagCaracter


class TagBoolean(TagCaracter):
    def __init__(self, *args, **kwargs):
        self.valores_texto = {
            None: '',
            True: 'true',
            False: 'false',
        }
        super(TagBoolean, self).__init__(*args, **kwargs)
        self.valor = None

    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, valor):
        if isinstance(valor, str):
            self.valor = valor.decode('utf-8')

        elif isinstance(valor, unicode):
            if valor.lower() == 'true':
                self.valor = True
            elif valor.lower() == 'false':
                self.valor = False
            else:
                self.valor = None

        elif isinstance(valor, bool):
            self._valor = valor
            if self.valor:
                self._texto = 'true'
            else:
                self._texto = 'false'

        elif valor is None:
            self._valor = None

        self._texto = self.valores_texto[self.valor]
