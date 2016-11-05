# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
    # ('13', 'décimo terceiro'),
)

MESES_DIC = dict(MESES)

TIPOS = (
    ('T', 'Todos'),
    ('N', 'Somente holerites'),
    ('R', 'Somente rescisões'),
)


class estoque_relatorio(osv.osv_memory):
    _name = 'estoque.relatorio'
    _description = u'Relatórios do Estoque'
    _rec_name = 'nome'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data do Arquivo'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'tipo': fields.selection(TIPOS, u'Tipo'),
        'product_id': fields.many2one('product.product', u'Produto'),
        'location_id': fields.many2one('stock.location', u'Local do Estoque'),
        'category_id': fields.many2one('product.category', u'Categoria'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'data': fields.date.today,
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'tipo': 'T',
    }
    
    def gera_movimento_estoque(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        
        id = ids[0]
        
        rel_obj = self.browse(cr, uid, id)
        
        if (not rel_obj.product_id) and (not rel_obj.category_id):
            raise osv.except_osv(u'Erro!', u'Selecione um Produto ou uma Categoria!')
        
        if rel_obj.category_id:
            rel = Report('Posição de Estoque', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'posicao_estoque.jrxml')           
            rel.parametros['LOCATION_ID'] = rel_obj.location_id.id
            rel.parametros['CATEGORIA'] = rel_obj.category_id.name
            rel.parametros['DATA_FINAL'] = rel_obj.data_final
            
            pdf, formato = rel.execute()

            dados = {
                'nome': u'posicao_estoque.pdf',
                'arquivo': base64.encodestring(pdf)
            }
        else:    
            rel = Report('Movimento de Estoque', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'movimento_estoque.jrxml')
            rel.parametros['PRODUCT_ID'] = rel_obj.product_id.id
            rel.parametros['LOCATION_ID'] = rel_obj.location_id.id
            rel.parametros['DATA_INICIAL'] = rel_obj.data_inicial
            rel.parametros['DATA_FINAL'] = rel_obj.data_final

            pdf, formato = rel.execute()
    
            dados = {
                'nome': u'movimento_estoque.pdf',
                'arquivo': base64.encodestring(pdf)
            }
        rel_obj.write(dados)
        
        return True
    
estoque_relatorio()   
