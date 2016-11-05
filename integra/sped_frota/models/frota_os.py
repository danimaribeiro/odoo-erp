# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_os(osv.Model):
    _name = 'frota.os'
    _inherit = 'frota.os'

    _columns = {
        'sped_documento_ids': fields.many2many('sped.documento', 'sped_frota_documento_os', 'frota_os_id', 'sped_documento_id', u'Notas Fiscais'),
    }


frota_os()
