# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals


import urllib
import urllib2
from BeautifulSoup import BeautifulSoup


def _separa_campo(soup, table, td, b):
    tables = soup.html.body.findAll('table')
    tds = tables[table].findAll('td')
    bs = tds[td].findAll('b')
    campo = unicode(bs[b]).strip('<b>').strip('</b>').strip()
    campo = campo.replace('&amp;', '&')

    while '  ' in campo:
        campo = campo.replace('  ', ' ')

    return campo


def executa_consulta_cnae(codigo=''):
    url = 'http://www.cnae.ibge.gov.br/subclasse.asp'

    dados = {
        'TabelaBusca': 'CNAE_201@CNAE 2.1 - Subclasses@0@cnaefiscal@0',
        'codsubclasse': codigo,
    }

    retorno = {}

    try:
        req = urllib2.Request(url, data=urllib.urlencode(dados))
        resp = urllib2.urlopen(req)
        texto = resp.read().decode('iso8859-1')

    except (UnicodeDecodeError,):
        retorno['cnae_nao_existe'] = True
        return retorno

    if 'Erro' in texto:
        retorno['erro_cnae'] = True
        return retorno

    soup = BeautifulSoup(texto, fromEncoding='iso-8859-1')

    # Separa os campos
    retorno['descricao'] = _separa_campo(soup,  4, 19, 0)

    return retorno
