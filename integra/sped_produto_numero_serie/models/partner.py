# -*- encoding: utf-8 -*-

from osv import osv, fields


class res_partner(osv.Model):
    _inherit = 'res.partner'

    _columns = {
        'numero_serie_ids': fields.one2many('product.numero.serie', 'partner_id', string=u'Números de série'),
    }


res_partner()