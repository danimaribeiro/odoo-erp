# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'numerario_item_id': fields.many2one('finan.numerario.valor', u'Item de numerário', ondelete='cascade'),
    }


finan_lancamento()
