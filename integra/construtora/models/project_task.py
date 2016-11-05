# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class project_task(osv.Model):
    _name = 'project.task'
    _inherit = 'project.task'
    _order = 'codigo'

    _columns = {
        'codigo': fields.integer(u'Código da tarefa'),
        'tarefa_antecessora_id': fields.many2one('project.task', u'Tarefa antecessora'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
    }

#    def copy(self, cr, uid, id, dados, context={}):

    def copy_data(self, cr, uid, id, default={}, context=None):
        
        task_obj = self.browse(cr, uid, id)        
        default['name'] = task_obj.name 
        
        return super(project_task, self).copy_data(cr, uid, id, default, context)

project_task()
