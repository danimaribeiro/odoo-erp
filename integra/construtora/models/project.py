# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class project(osv.osv):
    _name = "project.project"
    _description = "Project"
    _inherit = 'project.project'

    _columns = {
        'project_copy_id': fields.many2one('project.project', u'Projeto Cópia'),
        'eh_condominio': fields.boolean(u'É condomínio?'),
        'sindico_id': fields.many2one('res.partner', u'Síndico', ondelete='restrict'),
        'imovel_ids': fields.one2many('const.imovel', 'project_id', u'Imóveis'),
        'comissao_id': fields.many2one('finan.comissao', u'Comissão'),
        'checklist_id': fields.many2one('checklist.contrato', u'Check-list' ),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira' ),
        'indice_segurado': fields.float(u'Índice Segurado', digits=(10,4)),

        'modelo_comissao_total_receber_id': fields.many2one('finan.lancamento', u'Recebimento Comissão Total', ondelete="restrict", domain=[('tipo','=','MR')]),
        'modelo_comissao_total_pagar_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Total', ondelete="restrict", domain=[('tipo','=','MP')]),
        'modelo_comissao_pagar_empresa_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Empresa', ondelete="restrict", domain=[('tipo','=','MP')]),
        'modelo_comissao_pagar_agenciador_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Agenciador', ondelete="restrict", domain=[('tipo','=','MP')]),
        'modelo_comissao_pagar_corretor_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Corretor', ondelete="restrict", domain=[('tipo','=','MP')]),
        'modelo_comissao_pagar_gerente_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Gerente', ondelete="restrict", domain=[('tipo','=','MP')]),
        'modelo_comissao_pagar_outros_id': fields.many2one('finan.lancamento', u'Pagamento Comissão Outros', ondelete="restrict", domain=[('tipo','=','MP')]),

        'modelo_administracao_venda_pagar_id': fields.many2one('finan.lancamento', u'Pagamento administração venda', ondelete="restrict", domain=[('tipo','=','MP')]),

        'modelo_terceiro_associado_receber_id': fields.many2one('finan.lancamento', u'Recebimento Terceiro', ondelete="restrict", domain=[('tipo','=','MR')]),
        'modelo_terceiro_associado_pagar_id': fields.many2one('finan.lancamento', u'Pagamento Terceiro', ondelete="restrict", domain=[('tipo','=','MP')]),

    }

    _defaults = {
        'eh_condominio': False,
    }

    def copy_tasks(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        map_task_id = {}
        task_obj = self.pool.get('project.task')
        proj_copy = self.pool.get('project.project')
        for proj_obj in self.browse(cr, uid, ids):

            if not proj_obj.project_copy_id:
                raise osv.except_osv(u'Erro!', u'Selecione o Projeto!')

            new_project_id = proj_obj.id
            old_project_id = proj_obj.project_copy_id.id

            proj = proj_copy.browse(cr, uid, old_project_id, context=context)
            for task in proj.tasks:
                map_task_id[task.id] = task_obj.copy(cr, uid, task.id, {}, context=context)
            proj_obj.write({'tasks':[(6,0, map_task_id.values())]})
            task_obj.duplicate_task(cr, uid, map_task_id, context=context)

        return True

project()
