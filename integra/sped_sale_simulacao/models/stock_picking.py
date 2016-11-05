# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class stock_picking(osv.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'

    _columns = {
        'sped_documento_id': fields.many2one('sped.documento', u'Nota Fiscal'),
    }


stock_picking()
