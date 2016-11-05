# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data
import base64
from finan.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes



DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
    ('rtf', u'WORD'),
)

class orcamento_relatorio(osv.Model):
    _name = 'orcamento.relatorio'
    _description = u'Orçamento Relatório'


    _columns = {        
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
       
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'orcamento.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'formato': 'pdf',                        
    }



orcamento_relatorio()
