# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_documentoitem(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
         'documentoitem_compra_ids': fields.one2many('sped.documentoitem.compra', 'documentoiten_id',string=u'Item do Pedido'),                  
    }

    
sped_documentoitem()
