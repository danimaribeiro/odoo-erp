# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
import netsvc
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'


    _columns = {
                'finan_sale_ids': fields.one2many('finan.sale', 'order_id', u'Pagamentos'),
                'cheque_ids': fields.one2many('finan.cheque','order_id', u'Orçamento Cheques'),
    }

    _defaults = {
    }

sale_order()
