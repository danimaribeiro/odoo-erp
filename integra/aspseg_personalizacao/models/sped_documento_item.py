# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_documentoitem(osv.Model):
    _description = 'Itens de documentos SPED'
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
        
    }

 
sped_documentoitem()
