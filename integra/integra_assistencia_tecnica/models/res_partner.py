# -*- coding: utf-8 -*-

from osv import fields, osv

class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'assistencia_tecnica_id': fields.many2one('res.partner', u'Assistência Técnica')
    }


res_partner()
