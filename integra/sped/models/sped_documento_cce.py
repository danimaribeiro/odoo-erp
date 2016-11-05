# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import trata_nfe


class sped_documentocce(osv.Model):
    _description = 'CC-e de documentos SPED'
    _name = 'sped.documentocce'
    _order = 'documento_id, sequencia desc'

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
        'sequencia': fields.integer(u'Sequência', required=True),
        'correcao': fields.text(u'Correção', required=True),
    }

    _defaults = {
        'sequencia': 1,
    }

    def gera_carta_correcao(self, cr, uid, ids, context={}):
        for cce_obj in self.browse(cr, uid, ids):
            trata_nfe.corrige_nfe(self, cr, uid, cce_obj, cce_obj.documento_id)


sped_documentocce()
