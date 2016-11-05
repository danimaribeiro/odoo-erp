# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_gera_nota(osv.osv_memory):
    _name = 'finan.gera_nota'
    _inherit = 'finan.gera_nota'

    _columns = {
        'tipo_faturamento_id': fields.many2one('finan.tipo.faturamento', u'Tipo do faturamento', ondelete='restrict'),
    }


finan_gera_nota()

