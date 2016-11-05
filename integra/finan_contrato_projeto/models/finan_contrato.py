# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_contrato(osv.Model):
    _description = u'Contrato'
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto', select=True, ondelete='restrict'),
    }


finan_contrato()
