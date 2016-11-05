# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields


class project_project(osv.Model):
    _inherit = 'project.project'
    _name = 'project.project'

    _columns = {
        'versao': fields.char(u'Versão', size=60),
    }


project_project()
