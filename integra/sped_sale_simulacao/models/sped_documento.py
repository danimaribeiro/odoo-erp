# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class sped_documento(osv.Model):
    _inherit = 'sped.documento'
    _name = 'sped.documento'

    _columns = {
        'stock_picking_id': fields.many2one('stock.picking', u'Lista de separação'),
    }


sped_documento()
