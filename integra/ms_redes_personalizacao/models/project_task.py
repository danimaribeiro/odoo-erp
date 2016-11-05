# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class project_task(osv.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    _columns = {
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do Orçamento'),
        'employee_ids': fields.many2many('hr.employee','hr_task_employee','emloyee_id','task_id', u'Funcionários'),
        'veiculo_ids': fields.many2many('frota.veiculo','frota_task_veiculo','veiculo_id','task_id', u'Veiculos'),
    }


project_task()
