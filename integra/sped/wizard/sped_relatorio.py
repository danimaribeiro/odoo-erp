# -*- coding: utf-8 -*-

import os
from osv import fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime,hoje, agora
from pybrasil.base import DicionarioBrasil
from relatorio import *
import csv
from sped.constante_tributaria import *


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

TIPO_NOTAS = [
    ('1', 'Analítico'),
    ('2', 'Sintético'),
    ('3', 'Sintético por operação'),
]


class sped_relatorio(osv.osv_memory):
    _name = 'sped.relatorio'
    _description = u'Relatórios Fiscais'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'product_id': fields.many2one('product.product', u'Produto'),
        'naturezaoperacao_id': fields.many2one('sped.naturezaoperacao', u'Natureza Operação'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'tipo': fields.selection(TIPO_NOTAS, u'Tipo'),
        'modelo': fields.selection(MODELO_FISCAL, u'Modelo fiscal'),
        'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão'),
        'soh_empresa': fields.boolean(u'Somente esta empresa/unidade?'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'nome': '',
        'formato': 'pdf',
        'emissao': '0',
        'soh_empresa': False,
    }


    def gera_relatorio_notas_canceladas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Notas Canceladas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_notas_canceladas.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['CNPJ_CPF'] = rel_obj.company_id.cnpj_cpf
        natureza_id = rel_obj.naturezaoperacao_id.id
        emissao = rel_obj.emissao

        rel.parametros['EMISSAO'] = emissao

        if rel_obj.naturezaoperacao_id.id:
            rel.parametros['NATUREZA_ID'] = str(natureza_id)
        else:
            rel.parametros['NATUREZA_ID'] = '%'

        if rel_obj.modelo:
            rel.parametros['MODELO'] = rel_obj.modelo
        else:
            rel.parametros['MODELO'] = '%'

        rel.parametros['EMISSAO'] = rel_obj.emissao

        rel.outputFormat = rel_obj.formato
        relatorio = u'notas_canceladas_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_retencao_inss(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório Retenção de INSS', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'retencao_inss.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['CNPJ_CPF'] = rel_obj.company_id.cnpj_cpf

        if rel_obj.modelo:
            rel.parametros['MODELO'] = rel_obj.modelo
        else:
            rel.parametros['MODELO'] = '%'

        rel.outputFormat = rel_obj.formato

        relatorio = u'retenção_inss_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_notas_emitidas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        emissao = rel_obj.emissao
        natureza_id = rel_obj.naturezaoperacao_id.id

        rel = Report('Relatório de Notas Emitidas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_notas_emitidas.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['CNPJ_CPF'] = rel_obj.company_id.cnpj_cpf
        rel.parametros['EMISSAO'] = emissao
        rel.parametros['SOH_EMPRESA'] = '1' if rel_obj.soh_empresa else '0'

        if rel_obj.naturezaoperacao_id.id:
            rel.parametros['NATUREZA_ID'] = str(natureza_id)
            rel.parametros['FILTRO_NATUREZA'] = rel_obj.naturezaoperacao_id.nome or ''
        else:
            rel.parametros['NATUREZA_ID'] = '%'
            rel.parametros['FILTRO_NATUREZA'] = ''

        if rel_obj.product_id.id:
            rel.parametros['PRODUCT_ID'] = str(rel_obj.product_id.id)
            if rel_obj.product_id.default_code:
                rel.parametros['PRODUCT_NAME'] = '[' + rel_obj.product_id.default_code + '] ' +  rel_obj.product_id.name_template
            else:
                rel.parametros['PRODUCT_NAME'] = '[]' +  rel_obj.product_id.name_template
        else:
            rel.parametros['PRODUCT_ID'] = '%'
            rel.parametros['PRODUCT_NAME'] = ''

        if rel_obj.modelo:
            rel.parametros['MODELO'] = rel_obj.modelo
        else:
            rel.parametros['MODELO'] = '%'

        if rel_obj.emissao == '0':
            rel.parametros['TITULO_REL'] = u'RELATÓRIO DE NOTAS EMITIDAS'
            rel.parametros['TITULO_COLUNA_DATA_EMISSAO'] = '1'
            rel.parametros['EMISSAO'] = rel_obj.emissao
        else:
            rel.parametros['TITULO_REL'] = u'RELATÓRIO DE NOTAS RECEBIDAS'
            rel.parametros['TITULO_COLUNA_DATA_EMISSAO'] = '2'
            rel.parametros['EMISSAO'] = rel_obj.emissao

        rel.outputFormat = rel_obj.formato

        if rel_obj.tipo == '1':
            rel.parametros['TIPO'] = '1'
            rel.parametros['TIPO_ANALISE'] = 'finan_notas_emitidas_analitico.jasper'
            relatorio = u'notas_emitidas_analitico_'

        elif rel_obj.tipo == '2':
            rel.parametros['TIPO'] = '2'
            rel.parametros['TIPO_ANALISE'] = 'finan_notas_emitidas_sintetico.jasper'
            relatorio = u'notas_emitidas_sintetico_'

        elif rel_obj.tipo == '3':
            rel.parametros['TIPO'] = '2'
            rel.parametros['TIPO_ANALISE'] = 'finan_notas_emitidas_sintetico_operacao.jasper'
            relatorio = u'notas_emitidas_sintetico_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

sped_relatorio()
