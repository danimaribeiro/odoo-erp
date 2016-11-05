# -*- coding: utf-8 -*-

from osv import fields, osv


class stock_inventory_line(osv.osv):
    _name = 'stock.inventory.line'
    _inherit = 'stock.inventory.line'
    _description = 'Inventory Line'
    _rec_name = 'inventory_id'

    def _vr_total(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.product_qty and obj.vr_unitario:
                res[obj.id] = obj.product_qty * obj.vr_unitario
            else:
                res[obj.id] = 0

        return res


    _columns = {
        #'inventory_id': fields.many2one('stock.inventory', 'Inventory', ondelete='cascade', select=True),
        #'location_id': fields.many2one('stock.location', 'Location', required=True),
        #'product_id': fields.many2one('product.product', 'Product', required=True, select=True),
        #'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
        #'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM')),
        #'company_id': fields.related('inventory_id','company_id',type='many2one',relation='res.company',string='Company',store=True, select=True, readonly=True),
        #'prod_lot_id': fields.many2one('stock.production.lot', 'Production Lot', domain='[('product_id','=',product_id)]'),
        #'state': fields.related('inventory_id','state',type='char',string='State',readonly=True),
        'vr_unitario': fields.float(string=u'Unitário', digits=(21, 10)),
        'vr_total': fields.function(_vr_total, type='float', string=u'Total', digits=(18, 2), store=True),
    }

    def onchange_quantidade_unitario(self, cr, uid, ids, product_qty, vr_unitario, context={}):
        res = {}
        valores = {'vr_total': 0}
        res['value'] = valores

        if product_qty and vr_unitario:
            valores['vr_total'] = product_qty * vr_unitario

        return res

    #def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        #''' Changes UoM and name if product_id changes.
        #@param location_id: Location id
        #@param product: Changed product_id
        #@param uom: UoM product
        #@return:  Dictionary of changed values
        #'''
        #if not product:
            #return {'value': {'product_qty': 0.0, 'product_uom': False}}
        #obj_product = self.pool.get('product.product').browse(cr, uid, product)
        #uom = uom or obj_product.uom_id.id
        #amount = self.pool.get('stock.location')._product_get(cr, uid, location_id, [product], {'uom': uom, 'to_date': to_date, 'compute_child': False})[product]
        #result = {'product_qty': amount, 'product_uom': uom}
        #return {'value': result}

    def write(self, cr, uid, ids, dados, context={}):
        campos_nao_atualiza = [
            'inventory_id',
            'location_id',
            'product_id',
            'product_uom',
            'product_qty',
            'company_id',
            'prod_lot_id',
            'state',
        ]

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.state == 'done':
                for campo in campos_nao_atualiza:
                    if campo in dados:
                        del dados[campo]

        if dados:
            super(stock_inventory_line, self).write(cr, uid, ids, dados, context=context)


stock_inventory_line()
