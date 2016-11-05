# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from datetime import datetime, time
from pytz import datetime as pytz_datetime
from dateutil.parser import parse as parse_datetime
from ..data import ParserInfoBrasil, hora_por_extenso
from .tag_caracter import TagCaracter


class TagHora(TagCaracter):
    def __init__(self, *args, **kwargs):
        self.formato = b'%H:%M:%S'
        super(TagHora, self).__init__(*args, **kwargs)
        self.valor = None

    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, valor):
        if isinstance(valor, str):
            self.valor = valor.decode('utf-8')

        elif isinstance(valor, unicode) and valor:
            try:
                data = parse_datetime(valor)
            except:
                try:
                    data = parse_datetime(valor, ParserInfoBrasil())
                except:
                    data = None
            self.valor = data

        elif isinstance(valor, (datetime, pytz_datetime.datetime)):
            data = time(valor.hour, valor.minute, valor.second)
            self.valor = data

        elif isinstance(valor, time):
            self._valor = valor
            self._texto = self.valor.strftime(self.formato)
        else:
            self._valor = None
            self._texto = ''

    @property
    def formatado(self):
        if self.valor:
            return self.valor.strftime(b'%H:%M:%S')

        else:
            return ''

    @property
    def extenso(self):
        if self.valor:
            return hora_por_extenso(self.valor, segundos=True)

        else:
            return ''
