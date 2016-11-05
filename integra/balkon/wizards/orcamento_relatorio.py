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
            'user_id': fields.many2one('res.users', u'Usuário'), 
            'oportunidade_id': fields.many2one('crm.lead', u'Oportunidade'),             
        }
    _defaults = {
                 'company_id': '',
          
        }
    
    def gera_relatorio_oportunidades(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        rel = Report('Relatório de Oportunidades', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'crm_oportunidade.jrxml')
        
        if rel_obj.company_id:
            rel.parametros['COMPANY_ID'] = str(rel_obj.company_id.id)
        else: 
            rel.parametros['COMPANY_ID'] = '%'
        
        if rel_obj.company_id:
            rel.parametros['USER_ID'] = str(rel_obj.user_id.id)
        else: 
            rel.parametros['USER_ID'] = '%'
        
        if rel_obj.oportunidade_id:
            rel.parametros['OPORTUNIDADE_ID'] = str(rel_obj.oportunidade_id.id)
        else: 
            rel.parametros['OPORTUNIDADE_ID'] = '%'
            
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Relatorio_oportunidades_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


orcamento_relatorio()