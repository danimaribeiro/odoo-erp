# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv
import urllib2
import json


def consulta_cep(cep_consulta, cr, uid, pool_municipio):
    cep_consulta = cep_consulta.replace('-', '').replace(' ', '')

    if len(cep_consulta) != 8 or not cep_consulta.isdigit():
        raise osv.except_osv('CEP incorreto', 'O CEP deve ter 8 algarismos!')

    try:
        resposta = urllib2.urlopen('http://consulta-cep.ocean.erpintegra.com.br:8237/cep/' + cep_consulta)
        texto_resposta = resposta.read().decode('utf-8')
        resposta = json.loads(texto_resposta)
    except:
        raise osv.except_osv('CEP incorreto ou inexistente', u'O CEP não foi localizado!')

    municipio_id = pool_municipio.search(cr, uid, [('codigo_ibge', '=', resposta['municipio']['codigo_ibge'] + '0000')])[0]

    dados = {
        'endereco': resposta['logradouro'],
        'bairro': resposta['bairro'],
        'municipio_id': municipio_id,
    }

    return dados
