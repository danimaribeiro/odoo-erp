# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
import re


ESPACO_MULTIPLO = re.compile(r'\s+')


def escape(texto):
    if isinstance(texto, str):
        texto = texto.decode('utf-8')

    texto = texto.replace('&', '&amp;')
    texto = texto.replace('<', '&lt;')
    texto = texto.replace('>', '&gt;')
    texto = texto.replace('"', '&quot;')
    texto = texto.replace("'", '&apos;')

    #
    # Trocar ENTER e TAB
    #
    texto = texto.replace('\t', ' ')
    texto = texto.replace('\n', '| ')

    # Remove espaços seguidos
    # Dá pau em alguns webservices isso
    texto = ESPACO_MULTIPLO.sub(' ', texto)

    return texto


def unescape(texto):
    if isinstance(texto, str):
        texto = texto.decode('utf-8')

    texto = texto.replace('&#39;', "'")
    texto = texto.replace('&apos;', "'")
    texto = texto.replace('&quot;', '"')
    texto = texto.replace('&gt;', '>')
    texto = texto.replace('&lt;', '<')
    texto = texto.replace('&amp;', '&')
    texto = texto.replace('&APOS;', "'")
    texto = texto.replace('&QUOT;', '"')
    texto = texto.replace('&GT;', '>')
    texto = texto.replace('&LT;', '<')
    texto = texto.replace('&AMP;', '&')

    return texto
