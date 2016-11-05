# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from osv import osv, fields
from fields import CampoPeso


class sped_documentovolume(osv.Model):
    _description = 'Volumes de documentos SPED'
    _name = 'sped.documentovolume'

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
        'quantidade': fields.integer(u'Quantidade'),
        'especie': fields.char(u'Espécie', size=60),
        'marca': fields.char(u'Marca', size=60),
        'numero': fields.char(u'Número', size=60),
        'peso_liquido': CampoPeso(u'Peso líquido'),
        'peso_bruto': CampoPeso(u'Peso bruto'),
    }

    _defaults = {
        'quantidade': D('0'),
        'peso_liquido': D('0'),
        'peso_bruto': D('0'),
    }


sped_documentovolume()
