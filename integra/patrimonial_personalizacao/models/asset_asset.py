# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import hoje


class asset_asset(osv.Model):
    _name = 'account.asset.asset'
    _inherit = 'account.asset.asset'

    _columns = {
        'setor_id': fields.many2one('patrimonio.setor', u'Setor', ondelete='restrict'),
    }


asset_asset()
