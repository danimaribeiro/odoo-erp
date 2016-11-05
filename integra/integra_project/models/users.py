# -*- coding: utf-8 -*-

from osv import fields, osv


class res_users(osv.osv):
    _inherit = "res.users"

    _columns = {
        'partner_id': fields.many2one(u'Cliente'),
     }


project_phase()
