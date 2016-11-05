# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class stock_location(osv.Model):
    _name = 'stock.location'
    _inherit = 'stock.location'

    _columns = {
        'padrao_venda': fields.boolean(u'Local padrão para saídas para venda'),
        'padrao_locacao': fields.boolean(u'Local padrão para saídas para locação'),
        'padrao_contabilidade': fields.boolean(u'Local padrão para contabilidade'),
    }

    def ajusta_local_padrao_venda(self, cr, uid, ids):
        for local_obj in self.browse(cr, uid, ids):
            if local_obj.padrao_venda and local_obj.company_id:
                cr.execute('update stock_location set padrao_venda = False where company_id = %d and id <> %d' % (local_obj.company_id.id, local_obj.id))
            if local_obj.padrao_locacao and local_obj.company_id:
                cr.execute('update stock_location set padrao_locacao = False where company_id = %d and id <> %d' % (local_obj.company_id.id, local_obj.id))

    def create(self, cr, uid, dados, context={}):
        res = super(stock_location, self).create(cr, uid, dados, context=context)
        self.ajusta_local_padrao_venda(cr, uid, [res])
        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(stock_location, self).write(cr, uid, ids, dados, context=context)
        self.ajusta_local_padrao_venda(cr, uid, ids)
        return res


stock_location()

