# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class stock_picking(osv.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'

    def gerar_nota(self, cr, uid, ids, context={}):
        for picking_obj in self.browse(cr, uid, ids):
            if picking_obj.sale_id:
                pedido_obj = picking_obj.sale_id
                #
                # Gera a NF-e correspondente ao pedido vinculado
                #
                pedido_obj.gera_notas(context={'stock_picking_id': picking_obj.id})


stock_picking()
