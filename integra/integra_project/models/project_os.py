# -*- coding: utf-8 -*-

from osv import fields, osv
from pybrasil.data import parse_datetime, mes_passado, primeiro_dia_mes, ultimo_dia_mes
from finan.wizard.finan_relatorio import Report
import os
import base64


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

STATUS = [
          ('A', u'Aberta'),
          ('F', u'Fechada')
]

TIPO = [
        ('S','Simplificada'),
        ('A','Acompanhamento'),
        ('D','Detalhada'),
]


class project_os(osv.osv):
    _name = 'project.os'
    _description = 'Project OS'
    _rec_name = 'name'


    def get_prepara_task_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        task = self.pool.get('project.task')

        for obj_task in self.browse(cr, uid, ids):

            project_id = obj_task.project_id.id
            data_inicial = parse_datetime(obj_task.data_inicial).date()
            date_inicial = str(data_inicial)[:10]
            data_final = parse_datetime(obj_task.data_final).date()
            date_final = str(data_final)[:10]

            task_ids_lista = []
            task_ids_lista = task.search(cr, uid, [('os_id','=', False),('create_date','>=',str(data_inicial)),('create_date','<=',str(data_final)),('project_id','=', project_id)])
            res[obj_task.id] = task_ids_lista

        return res

    #def get_prepara_issue_ids(self, cr, uid, ids, nome_campo, args, context={}):
        #if not len(ids):
            #return {}

        #res = {}

        #issue = self.pool.get('project.issue')

        #for obj_issue in self.browse(cr, uid, ids):

            #project_id = obj_issue.project_id.id
            #data_inicial = parse_datetime(obj_issue.data_inicial).date()
            #date_inicial = str(data_inicial)[:10]
            #data_final = parse_datetime(obj_issue.data_final).date()
            #date_final = str(data_final)[:10]

            #issue_ids_lista = []
            #issue_ids_lista = issue.search(cr, uid, [('os_id','=', False),('create_date','>=',str(data_inicial)),('create_date','<=',str(data_final)),('project_id','=', project_id)])
            #res[obj_issue.id] = issue_ids_lista

        #return res

    def _get_descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for project_obj in self.browse(cr, uid, ids):

            nome = str(project_obj.id)
            nome += u' %s' % project_obj.project_id.name

            res[project_obj.id] = nome

        return res

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto', select=True, ondelete='restrict'),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
        'task_ids': fields.many2many('project.task', 'project_os_task', 'os_id', 'task_id', u'Tarefa'),
        #'issue_ids': fields.many2many('project.issue', 'project_os_issue', 'os_id', 'issue_id', u'Suporte'),
        'status': fields.selection(STATUS, u'Status'),
        #'prepara_task_ids': fields.function(get_prepara_task_ids, type='one2many', relation='project.task', method=True, string=u'Tarefas a incluir'),
        #'prepara_issue_ids': fields.function(get_prepara_issue_ids, type='one2many', relation='project.issue', method=True, string=u'Suportes a incluir'),
        'tipo': fields.selection(TIPO, u'Tipo'),
        #'prepara_task_ids': fields.function(get_prepara_task_ids, type='one2many', relation='project.task', method=True, string=u'Tarefas a incluir'),
        #'prepara_issue_ids': fields.function(get_prepara_issue_ids, type='one2many', relation='project.issue', method=True, string=u'Suportes a incluir'),
        'assinatura': fields.char(u'Assinatura Representante', size=60),
        'name': fields.function(_get_descricao, method=True, type='char', size=128, string=u'Descrição', store=True, select=True),
     }

    _defaults = {
        'status':  'S',
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
     }

    def busca_tarefa_suporte(self, cr, uid, id, context={}):
        return True

    def vincula_tarefa_suporte(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        os_obj = self.browse(cr, uid, id)

        for task_obj in os_obj.prepara_task_ids:
            task_obj.write({'os_id': os_obj.id})

        #for issue_obj in os_obj.prepara_issue_ids:
            #issue_obj.write({'os_id': os_obj.id})

        return True

    def imprimir_os(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        os_obj = self.browse(cr, uid, id)

        rel = Report('Projeto OS', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'project_os.jrxml')
        rel.parametros['OS_IDS'] = '(' + str(id) + ')'
        rel.parametros['TIPO'] = os_obj.tipo
        rel.parametros['USER_ID'] = id
        project_nome = 'project_os_' + str(os_obj.id) + '.pdf'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.os'), ('res_id', '=', id), ('name', '=', project_nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': project_nome,
            'datas_fname': project_nome,
            'res_model': 'project.os',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        #
        # Gera agora pro Word
        #
        project_nome = 'project_os_' + str(os_obj.id) + '.rtf'
        rel = Report('Projeto OS', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'project_os.jrxml')
        rel.parametros['OS_IDS'] = '(' + str(id) + ')'
        rel.parametros['TIPO'] = os_obj.tipo
        rel.parametros['USER_ID'] = id
        rel.outputFormat = 'rtf'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.os'), ('res_id', '=', id), ('name', '=', project_nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': project_nome,
            'datas_fname': project_nome,
            'res_model': 'project.os',
            'res_id': id,
            'file_type': 'application/rtf',
        }
        attachment_pool.create(cr, uid, dados)

        return True


project_os()
