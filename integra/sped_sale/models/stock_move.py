# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class stock_move(osv.Model):
    _inherit = 'stock.move'
    _name = 'stock.move'

    _columns = {
        'sped_documento_id': fields.many2one('sped.documento', u'Nota Fiscal'),
    }


stock_move()
