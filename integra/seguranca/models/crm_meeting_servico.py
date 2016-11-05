# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from sped.models.fields import *


class crm_meeting_servico(orm.Model):
    _name = 'crm.meeting.servico'
    _description = u'Serviços na agenda de OS'

    _columns = {
        'meeting_id': fields.many2one('crm.meeting', u'Agenda', ondelete='cascade'),
        'sale_order_id': fields.related('meeting_id', 'sale_order_id', type='many2one', relation='sale.order', string=u'OS', store=True),
        'product_id': fields.many2one('product.product', string=u'Serviço', ondelete='restrict'),
        'quantidade': CampoQuantidade(u'Quantidade'),
    }

    _defaults = {
        'quantidade': 1,
    }


crm_meeting_servico()
