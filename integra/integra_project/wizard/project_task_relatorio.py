# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv, orm
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class project_task_relatorio(osv.osv_memory):
    _description = u'Relatório de Tarefas'
    _name = 'project.task.relatorio'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),       
    }

    _defaults = {
        'nome': '',        
    }

    def gerar_relatorio_tarefa(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}
        
        taks_ids = context['active_ids']
        #holerites_ids = tuple(holerites_ids)
        
        print(taks_ids)

        if not taks_ids:
            return {'type': 'ir.actions.act_window_close'}

        holerite_obj = self.pool.get('project.task.relatorio').browse(cr, uid, taks_ids[0])

        rel = Report('Recibo de Pagamento', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'project_task_lista.jrxml')
        recibo = 'chamados_integra.pdf'
        rel.parametros['REGISTRO_IDS'] = str(taks_ids).replace("[","(").replace("]",")")

        pdf, formato = rel.execute()

        self.write(cr, uid, ids, {'nome': recibo, 'arquivo': base64.encodestring(pdf)})

       

project_task_relatorio()
