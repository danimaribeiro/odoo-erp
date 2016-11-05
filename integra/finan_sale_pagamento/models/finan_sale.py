# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D

class CampoDinheiro(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (18, 2)
        super(CampoDinheiro, self).__init__(*args, **kwargs)

class finan_sale(orm.Model):
    _name = 'finan.sale'
    _description = 'Orçamento Pagamentos'
    

    _columns = {
           'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
           'valor': CampoDinheiro(u'Valor do documento'),                 
           'data': fields.date( u'Data'),
           'order_id': fields.many2one('sale.order', u'Orçamento', ondelete='cascade'),
           'create_uid': fields.many2one('res.users', u'Usuário'),
    }
    
    defaults = {
            'valor': D(0),                
            'data': fields.date.today,                
    }

finan_sale()
