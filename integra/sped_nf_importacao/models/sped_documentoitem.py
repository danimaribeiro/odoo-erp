# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from sped.constante_tributaria import *


class sped_documentoitem(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
                'declaracao_ids': fields.one2many('sped.declaracao.importacao', 'documentoitem_id', u'Declarações'),
       
    }

    

sped_documentoitem()
