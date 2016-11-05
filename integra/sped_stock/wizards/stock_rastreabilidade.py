# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv, orm
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class stock_rastreabilidade(osv.osv_memory):
    _name = 'stock.rastreabilidade'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'descricao'
    _description = u'Holerites de funcionários'
    _order = 'nome'


    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),        
    }

    _defaults = {
                
    }

    def gera_movimento(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        move_ids = context['active_ids']       
        #holerites_ids = tuple(holerites_ids)            
          
                 
        rel = Report('Movimento de estoque', cr, uid)       
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'stock_rastreabilidade_movimentacao.jrxml')
        recibo = 'Movimento_estoque.pdf'
        rel.parametros['REGISTRO_IDS'] = str(move_ids).replace("[","(").replace("]",")")
        
        pdf, formato = rel.execute()        
        
        self.write(cr, uid, ids, {'nome': recibo, 'arquivo': base64.encodestring(pdf)})                   

stock_rastreabilidade()
