# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
import csv
from pybrasil.base import DicionarioBrasil


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class orcamento_relatorio(osv.osv_memory):
    _inherit = 'orcamento.relatorio'
    _name = 'orcamento.relatorio'

    _columns = {        
            'user_id': fields.many2one('res.users', u'Usuário') 
        }
    _defaults = {
          
        }
    
    def gera_relatorio_comissao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Comissão', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_relatorio_comissao_analitico.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        
        if rel_obj.user_id:
            rel.parametros['VENDEDOR_ID'] = str(rel_obj.user_id.id)
        else: 
            rel.parametros['VENDEDOR_ID'] = '%'


        pdf, formato = rel.execute()

        dados = {
            'nome': u'Relatorio_comissao_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


orcamento_relatorio()