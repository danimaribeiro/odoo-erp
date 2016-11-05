# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, mes_passado, primeiro_dia_mes, ultimo_dia_mes, hoje, agora, formata_data
from finan.wizard.relatorio import *
from datetime import date
import csv
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from pybrasil.data.grafico_gantt import tempo_tarefa
from dateutil.relativedelta import relativedelta


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class projeto_relatorio(osv.osv_memory):
    _name = 'projeto.relatorio'
    _inherit = 'projeto.relatorio'    
   

    def gera_relatorio_imovel_projeto(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id, context=context)        
        
        rel = Report('Imoveis por Projeto', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_relatorio_venda_projeto.jrxml')
        rel.outputFormat = rel_obj.formato
        rel.parametros['PROJETO_ID'] = rel_obj.project_id.id        
        pdf, formato = rel.execute()

        dados = {
            'nome': u'Imoveis_' +  rel_obj.project_id.name  + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True
    
projeto_relatorio()
