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
     ('2', 'Sintetico'),
]


class sped_relatorio(osv.osv_memory):
    _name = 'sped.relatorio'
    _inherit = 'sped.relatorio'

    _columns = {
              'cfop_id': fields.many2one('sped.cfop', u'CFOP', ondelete='restrict', select=True),
              'ncm_id': fields.many2one('sped.ncm', u'NCM', ondelete='restrict', select=True),                
              'product_id': fields.many2one('product.product', u'Produto', ondelete='restrict', select=True),                
    }

    _defaults = {
        
    }


    def gera_relatorio_faturamento_direto(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        emissao = rel_obj.emissao
        natureza_id = rel_obj.naturezaoperacao_id.id

        rel = Report('Relatório de Comissoes', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_faturamento_direto_asp.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['CNPJ_CPF'] = rel_obj.company_id.cnpj_cpf
        rel.parametros['EMISSAO'] = emissao
        

        if rel_obj.naturezaoperacao_id.id:
            rel.parametros['NATUREZA_ID'] = str(natureza_id)
        else:
            rel.parametros['NATUREZA_ID'] = '%'

        if rel_obj.product_id.id:
            rel.parametros['PRODUCT_ID'] = str(rel_obj.product_id.id)
        else:
            rel.parametros['PRODUCT_ID'] = '%'

        if rel_obj.modelo:
            rel.parametros['MODELO'] = rel_obj.modelo
        else:
            rel.parametros['MODELO'] = '%'
        
        rel.outputFormat = rel_obj.formato
           
        relatorio = u'Comissoes_ASP_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True
    
    def gera_relatorio_recolhimento_icms(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Recolhimento de Icms', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'asp_notas_emitidas_cfop.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]        

        if rel_obj.cfop_id.id:
            rel.parametros['CFOP'] = str(rel_obj.cfop_id.id)
        else:
            rel.parametros['CFOP'] = '%'

        if rel_obj.product_id.id:
            rel.parametros['PRODUCT_ID'] = str(rel_obj.product_id.id)
        else:
            rel.parametros['PRODUCT_ID'] = '%'

        if rel_obj.ncm_id:
            rel.parametros['NCM'] = str(rel_obj.ncm_id.id)
        else:
            rel.parametros['NCM'] = '%'
        
        rel.outputFormat = rel_obj.formato
           
        relatorio = u'Recolhimento_ICMS_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True
    

sped_relatorio()
