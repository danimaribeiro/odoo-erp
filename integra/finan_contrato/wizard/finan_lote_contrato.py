# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class finan_lote_contrato(osv.osv_memory):
    _description = u'Lote de Contratos'
    _name = 'finan.lote.contrato'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),        
    }

    _defaults = {
                
    }

    def gera_contratos(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        contratos_ids = context['active_ids']       
        contratos_ids = tuple(contratos_ids) 
                 
        rel = Report('Contratos', cr, uid)       
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'contratos.jrxml')
        recibo = 'Contratos.pdf'
        rel.parametros['REGISTRO_IDS'] = str(contratos_ids)
        
        pdf, formato = rel.execute()        
        
        self.write(cr, uid, ids, {'nome': recibo, 'arquivo': base64.encodestring(pdf)})                   

finan_lote_contrato()
