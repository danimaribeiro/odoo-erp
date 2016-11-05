# -*- coding: utf-8 -*-

import os
import base64
from osv import fields, osv
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, agora



DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {
    }

    _defaults = {
               
    }
    def gera_relatorio_comissao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
 

        rel = Report('Relatório de Comissões', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'di_comissao_venda.jrxml')
        rel.parametros['PARTNER_ID'] = int(rel_obj.partner_id.id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato
        
        pdf, formato = rel.execute()

        dados = {
            'nome': u'Relatorio_comissões_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

finan_relatorio()
