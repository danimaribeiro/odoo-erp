# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from datetime import datetime, date
from pytz import datetime as pytz_datetime
from pytz import UTC, timezone, tzinfo
from dateutil.parser import parse as parse_datetime
from ..data import ParserInfoBrasil, data_por_extenso, hora_por_extenso
from .tag_caracter import TagCaracter


class TagDataHora(TagCaracter):
    def __init__(self, *args, **kwargs):
        super(TagDataHora, self).__init__(*args, **kwargs)
        self.formato = b'%Y-%m-%d %H:%M:%S'
        self.valor = None
        self.fuso_horario = 'America/Sao_Paulo'

    @property
    def fuso_horario(self):
        return self._fuso_horario

    @fuso_horario.setter
    def fuso_horario(self, valor):
        if isinstance(valor, tzinfo.tzinfo):
            self._fuso_horario = valor
        elif isinstance(valor, str):
            self.fuso_horario = valor.decode('utf-8')
        elif isinstance(valor, unicode):
            try:
                self.fuso_horario = timezone(valor)
            except:
                pass

    @property
    def valor(self):
        return self.fuso_horario.normalize(self._valor)

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

        elif isinstance(valor, (datetime, date, pytz_datetime.datetime)):
            if not valor.tzinfo:
                valor = self.fuso_horario.localize(valor)

            print('tzinfo', valor.tzinfo)
            self._valor = UTC.normalize(valor)
            self._texto = self.valor.strftime(self.formato)

        else:
            self._valor = None
            self._texto = ''

    @property
    def formatado(self):
        if self.valor:
            return self.valor.strftime(b'%d/%m/%Y %H:%M:%S')

        else:
            return ''

    @property
    def extenso(self):
        if self.valor:
            return data_por_extenso(self.valor) + ', ' + hora_por_extenso(self.valor, preposicao=True, segundos=True)

        else:
            return ''


class TagDataHoraUTC(TagDataHora):
    def __init__(self, *args, **kwargs):
        super(TagDataHoraUTC, self).__init__(*args, **kwargs)
        self.formato = b'%Y-%m-%dT%H:%M:%S%z'
