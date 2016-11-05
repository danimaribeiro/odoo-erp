# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields, osv


class finan_conta(orm.Model):
    _name = 'finan.conta'
    _inherit = 'finan.conta'

    _columns = {
        #'user_id': fields.many2one('res.users', u'Setor', ondelete='set null'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
    }


finan_conta()
