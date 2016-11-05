# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from project_mrp.project_procurement import *



class procurement_order(osv.Model):
    _name = "procurement.order"
    _inherit = "procurement.order"
    #_columns = {
        #'task_id': fields.many2one('project.task', 'Task'),
        #'sale_line_id': fields.many2one('sale.order.line', 'Sale order line')
    #}

    #def action_check_finished(self, cr, uid, ids):
        #res = super(procurement_order, self).action_check_finished(cr, uid, ids)
        #return res and self.check_task_done(cr, uid, ids)

    #def check_task_done(self, cr, uid, ids, context=None):
        #""" Checks if task is done or not.
        #@return: True or False.
        #"""
        #return all(proc.product_id.type != 'service' or (proc.task_id and proc.task_id.state in ('done', 'cancelled')) \
                    #for proc in self.browse(cr, uid, ids, context=context))

    #def check_produce_service(self, cr, uid, procurement, context=None):
        #return True

    #def _convert_qty_company_hours(self, cr, uid, procurement, context=None):
        #product_uom = self.pool.get('product.uom')
        #company_time_uom_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.project_time_mode_id.id
        #if procurement.product_uom.id != company_time_uom_id:
            #planned_hours = product_uom._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, company_time_uom_id)
        #else:
            #planned_hours = procurement.product_qty
        #return planned_hours

    def _get_project(self, cr, uid, procurement_obj, context=None):
        #project_project = self.pool.get('project.project')
        #project = procurement.product_id.project_id
        #if not project and procurement.sale_line_id:
            ## find the project corresponding to the analytic account of the sale order
            #account = procurement.sale_line_id.order_id.project_id
            #project_ids = project_project.search(cr, uid, [('analytic_account_id', '=', account.id)])
            #projects = project_project.browse(cr, uid, project_ids, context=context)
            #project = projects and projects[0] or False
        #return project
        project_obj = super(procurement_order, self)._get_project(cr, uid, procurement_obj, context)

        #
        # Se o projeto já não vier definido, criar um novo
        #
        if not project_obj:
            project_pool = self.pool.get('project.project')
            dados = {
                'name': 'Projeto: ' + procurement_obj.origin,
                'user_id': 1,
                'parent_id': False,
                'date_start': procurement_obj.move_id.date,
            }
            project_id = project_pool.create(cr, uid, dados, context=context)
            project_obj = project_pool.browse(cr, uid, project_id, context=context)

        return project_obj

    def _get_phase(self, cr, uid, procurement_obj, project_obj, context=None):
        phase_pool = self.pool.get('project.phase')

        dados = {
            'name': '%s: %s' % (procurement_obj.origin or '', procurement_obj.product_id.name),
            'project_id': project_obj and project_obj.id or False,
            'duration': procurement_obj.product_qty,
            'product_uom': procurement_obj.product_uom.id,
        }

        phase_id = phase_pool.create(cr, uid, dados, context=context)
        phase_obj = phase_pool.browse(cr, uid, phase_id, context=context)

        return phase_obj

    def action_produce_assign_service(self, cr, uid, ids, context=None):
        project_task_pool = self.pool.get('project.task')

        for procurement_obj in self.browse(cr, uid, ids, context=context):
            project_obj = self._get_project(cr, uid, procurement_obj, context=context)
            phase_obj = self._get_phase(cr, uid, procurement_obj, project_obj, context=context)
            planned_hours = self._convert_qty_company_hours(cr, uid, procurement_obj, context=context)

            dados = {
                'name': '%s: %s' % (procurement_obj.origin or '', procurement_obj.product_id.name),
                'date_deadline': procurement_obj.date_planned,
                'planned_hours': planned_hours,
                'remaining_hours': planned_hours,
                'user_id': procurement_obj.product_id.product_manager.id,
                'notes': procurement_obj.note,
                'procurement_id': procurement_obj.id,
                'description': procurement_obj.note,
                'project_id': project_obj and project_obj.id or False,
                'phase_id': phase_obj and phase_obj.id or False,
                'company_id': procurement_obj.company_id.id,
            }

            task_id = project_task_pool.create(cr, uid, dados, context=context)
            self.write(cr, uid, [procurement_obj.id], {'task_id': task_id, 'state': 'running'}, context=context)

        return task_id

procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
