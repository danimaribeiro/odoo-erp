# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv



class stock_move(orm.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'sale_order_id': fields.many2one('sale.order', u'Proposta/OS', ondelete='restrict'),
        #'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', size=60, fnct_search=_procura_descricao),
    }



stock_move()
