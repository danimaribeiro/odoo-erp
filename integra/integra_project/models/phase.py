# -*- coding: utf-8 -*-

from osv import fields, osv


class project_phase(osv.osv):
    _name = "project.phase"
    _inherit = "project.phase"
    _description = "Project Phase"
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    _columns = {
        'parent_id': fields.many2one('project.phase', u'Fase superior', select=True, ondelete='restrict'),
        'child_ids': fields.one2many('project.phase', 'parent_id', string=u'Contas filhas'),
        'parent_left': fields.integer(u'Conta à esquerda', select=True),
        'parent_right': fields.integer(u'Conta a direita', select=True),
     }


project_phase()
