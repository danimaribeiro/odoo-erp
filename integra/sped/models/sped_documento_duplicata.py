# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from osv import osv, fields
from fields import CampoDinheiro


class sped_documentoduplicata(osv.Model):
    _description = 'Duplicatas de documentos SPED'
    _name = 'sped.documentoduplicata'

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
        'numero': fields.char(u'Número da duplicata/parcela', size=60, select=True),
        'data_vencimento': fields.date(u'Data de vencimento', select=True),
        'valor': CampoDinheiro(u'Valor da duplicata/parcela'),
    }

    _defaults = {
        'valor': D('0'),
    }


sped_documentoduplicata()
