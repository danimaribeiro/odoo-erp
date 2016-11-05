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

    _columns = {
            
    }

    def write(self, cr, uid, ids, vals, context={}):
        
        if not isinstance(ids,list): ids = [ids]
        tasks= self.browse(cr, uid, ids, context=context)    
        for task in tasks:
            if task.user_id:
                if task.user_id.id == uid and task.create_uid.id == uid:
                    continue
                elif task.user_id.id == uid and task.create_uid.id != uid:
                    continue
                elif task.user_id.id != uid and task.create_uid.id == uid:
                    continue
                else:
                    raise osv.except_osv(u'Inválido!', u'Usúario não tem permissão para tarefa!')
                
            elif task.create_uid.id != uid:    
                    raise osv.except_osv(u'Inválido!', u'Usúario não tem permissão para tarefa!')
        
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)        
       
        sql = """select
                    id 
                from res_groups_users_rel ug
                join res_users u on u.id = ug.uid
                where 
                    uid = """ + str(uid) + """
                    and gid = 26"""
                    
        cr.execute(sql)
        dados = cr.fetchall()
        if not dados:
            
            if len(vals) == 1 and not 'work_ids' in vals:      
                raise osv.except_osv(u'Inválido!', u'Não é permitido está alteração! Somente em "Tarefas em execução"')

        res = super(project_task, self).write(cr, uid, ids, vals, context)
        
        return res
    
    def do_open(self, cr, uid, ids, context={}):     
            
        res = super(project_task, self).do_open(cr, uid, ids, context)
        
        return res        
    
project_task()
