# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


def tira_abertura(texto):
    if isinstance(texto, str):
        texto = texto.decode('utf-8')

    if '?>' in texto:
        texto = texto.split('?>')[1:]
        texto = ''.join(texto)

    return texto


def poe_abertura(texto):
    if isinstance(texto, str):
        texto = texto.decode('utf-8')

    texto = tira_abertura(texto)
    texto = '<?xml version="1.0" encoding="utf-8"?>' + texto
    texto = texto.encode('utf-8')

    return texto
