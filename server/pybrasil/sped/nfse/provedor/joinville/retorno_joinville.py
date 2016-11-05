# -*- coding: utf-8 -*-

from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje 
from pybrasil.valor import formata_valor



def limpa_nfes(texto):
    probibidos = u'.,-_;:?!=+*/&#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


class RETORNO_JLLE(object):
    def __init__(self, *args, **kwargs):
        self.numero_lote = 0
        self.tipo = 0
        self.data_envio = hoje()
        self.data_processamento = hoje()
        self.status = 1
        self.descricao_status = ''
        self.observacao = ''
        self.documento = 0
        self.razao_social = ''
        self.rps = []
        
        
class RPS(object):
    def __init__(self, *args, **kwargs):
        
        self.numero = 0
        self.serie = ''
        self.nfem_numero = 0
        self.nfem_codigo_verificacao = ''                

