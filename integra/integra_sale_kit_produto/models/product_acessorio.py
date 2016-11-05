# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D



class product_acessorio(osv.Model):
    _name = 'product.acessorio'    
    _description = u'Acessório do produto'
    
        
    _columns = {                        
        'product_id': fields.many2one('product.product', u'Produto', ondelete='restrict'),
        'acessorio_id': fields.many2one('product.product', u'Acessório'),
        'quantidade': fields.float(u'Quantidade'),                    
    }    
    

product_acessorio()
