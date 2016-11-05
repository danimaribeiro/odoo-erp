# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_documentoitem(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
        'produto_nome': fields.related('produto_id', 'name', type='char', string=u'Produto/Serviço'),
        #'asset_id': fields.many2one('account.asset.asset', u'Patrimônio'),
        'asset_ids': fields.many2many('account.asset.asset', 'sped_documentoitem_patrimonio', 'sped_documentoitem_id', 'asset_id', u'Patrimônios'),
    }


sped_documentoitem()
