# -*- coding: utf-8 -*-

from osv import fields, osv


class project_issue(osv.osv):
    _name = "project.issue"
    _inherit = "project.issue"
    _description = "Project Issue"
  

    _columns = {
                'os_id': fields.many2one('project.os', 'Projeto OS'),
                'solucao': fields.text(u'Solução'),
    }


project_issue()
