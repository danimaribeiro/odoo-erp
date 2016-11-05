# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields

class finan_centrocusto(osv.Model):
    _inherit = 'finan.centrocusto'
    _rec_name = 'nome'


finan_centrocusto()
