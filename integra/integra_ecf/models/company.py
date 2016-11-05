# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *
from openerp import pooler, sql_db




class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'caixa_ecf': fields.char(u'Caixa ECF', size=3),
        
    }

    _defaults = {
        'caixa_ecf': '01',
    }



res_company()
