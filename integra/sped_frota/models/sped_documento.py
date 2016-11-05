# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'frota_os_ids': fields.many2many('frota.os', 'sped_frota_documento_os', 'sped_documento_id', 'frota_os_id', u'OS Frota'),
    }


sped_documento()
