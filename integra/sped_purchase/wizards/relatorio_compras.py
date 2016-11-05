# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
import base64
from finan.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from relatorio import *
from finan.wizard.finan_relatorio import Report



DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)



class relatorio_compras(osv.osv_memory):
    _name = 'relatorio.compras'
    _description = u'Relatórios de Compras'
    _rec_name = 'nome'

    _columns = {
        #'ano': fields.integer(u'Ano'),
        #'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data do Arquivo'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        #'tipo': fields.selection(TIPOS, u'Tipo'),
        'product_id': fields.many2one('product.product', u'Produto'),
        'location_id': fields.many2one('stock.location', u'Local do Estoque'),
        'category_id': fields.many2one('product.category', u'Categoria'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'data': fields.date.today,
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        #'tipo': 'T',
        'formato': 'pdf',
    }   


relatorio_compras()
