# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class stock_location(osv.Model):
    _name = 'stock.location'
    _inherit = 'stock.location'

    _columns = {
        'name': fields.char(u'Nome do local', size=64, required=True, translate=False, select=True),
        'entrada_padrao': fields.boolean(u'Local padrão para entradas na empresa'),
        'saida_padrao': fields.boolean(u'Local padrão para saídas da empresa'),
        'company_ids': fields.many2many('res.company', 'stock_location_company', 'stock_location_id', 'company_id', u'Empresas permitidas'),
        'location_custo_id': fields.many2one('stock.location', u'Local para Custo Médio'),
    }

    def ajusta_local_padrao(self, cr, uid, ids):
        for local_obj in self.browse(cr, uid, ids):
            if local_obj.entrada_padrao and local_obj.company_id:
                cr.execute('update stock_location set entrada_padrao = False where company_id = %d and id <> %d' % (local_obj.company_id.id, local_obj.id))
            if local_obj.saida_padrao and local_obj.company_id:
                cr.execute('update stock_location set saida_padrao = False where company_id = %d and id <> %d' % (local_obj.company_id.id, local_obj.id))

    def create(self, cr, uid, dados, context={}):
        res = super(stock_location, self).create(cr, uid, dados, context=context)
        self.ajusta_local_padrao(cr, uid, [res])
        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(stock_location, self).write(cr, uid, ids, dados, context=context)
        self.ajusta_local_padrao(cr, uid, ids)
        return res


stock_location()


class res_company(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'stock_location_ids': fields.many2many('stock.location', 'stock_location_company', 'company_id', 'stock_location_id', u'Locais do estoque permitidos'),
    }


res_company()

