# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_documentoduplicata(osv.Model):
    _inherit = 'sped.documentoduplicata'

    _columns = {
        'pagamento_bloqueado': fields.boolean(u'Pagamento bloqueado?'),
    }

    _defaults = {
        'pagamento_bloqueado': False,
    }


sped_documentoduplicata()
