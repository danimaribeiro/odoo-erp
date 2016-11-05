# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class sped_documentoitem(osv.Model):
    _inherit = 'sped.documentoitem'

    _columns = {
        'numero_serie_ids': fields.many2many('product.numero.serie', 'sped_documentoitem_numero_serie', 'item_id', 'numero_serie_id', string=u'Números de série'),
    }


sped_documentoitem()
