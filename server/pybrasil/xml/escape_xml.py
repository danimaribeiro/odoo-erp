# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)


def tirar_acentos(texto):
    if not texto:
        return texto

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
    # Nem pergunte...
    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto

def por_acentos(texto):
    if not texto:
        return texto

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

def tira_abertura(texto):
    if isinstance(texto, str):
        texto = texto.decode('utf-8')

    if '?>' in texto:
        texto = texto.split('?>')[1:]
        texto = ''.join(texto)

    return texto
