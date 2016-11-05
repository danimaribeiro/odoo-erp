# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from datetime import datetime, date
from pytz import datetime as pytz_datetime
from dateutil.parser import parse as parse_datetime
from ..data import ParserInfoBrasil, data_por_extenso
from .tag_caracter import TagCaracter


class TagData(TagCaracter):
    def __init__(self, *args, **kwargs):
        self.formato = b'%Y-%m-%d'
        super(TagData, self).__init__(*args, **kwargs)
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
            print('data 1', data, isinstance(data, (datetime, pytz_datetime.datetime)))
            self.valor = data

        elif isinstance(valor, (datetime, pytz_datetime.datetime)):
            data = date(valor.year, valor.month, valor.day)
            print('data 2', data, isinstance(data, (datetime, pytz_datetime.datetime)))
            print('data 3', data, isinstance(data, date))
            self.valor = data

        elif isinstance(valor, date):
            self._valor = valor
            self._texto = self.valor.strftime(self.formato)
        else:
            self._valor = None
            self._texto = ''

    @property
    def formatado(self):
        if self.valor:
            return self.valor.strftime(b'%d/%m/%Y')

        else:
            return ''

    @property
    def extenso(self):
        if self.valor:
            return data_por_extenso(self.valor)

        else:
            return ''
