# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv, orm
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class finan_fechamento_caixa(osv.osv_memory):
    _description = u'Fechamento de Caixas'
    _name = 'finan.fechamento.caixa'
    _inherit = 'ir.wizard.screen'
    
    _columns = {
        
    }

    _defaults = {

    }

    def gera_fechamento_caixas(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        saldo_pool = self.pool.get('finan.saldo')
        caixas_ids = context['active_ids']
        

        if not caixas_ids:
            return {'type': 'ir.actions.act_window_close'}

        for saldo_obj in saldo_pool.browse(cr, uid, caixas_ids):
            
            if saldo_obj.fechado:
                raise osv.except_osv(u'Erro!', u'Você não pode alterar o movimento já fechado, Caixa: ' + saldo_obj.res_partner_bank_id.nome )
            
            assinatura_pool = self.pool.get('finan.saldo.assinatura')
            
            dados = {
                'saldo_id': saldo_obj.id,
                'user_id': uid,
                'data': fields.datetime.now()
            }
            assinatura_pool.create(cr, uid, dados)
            
            saldo_obj.write({'fechado': True})
        
        return True    
            

finan_fechamento_caixa()
