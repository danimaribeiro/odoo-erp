# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class sped_documento(orm.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'tipo_faturamento_id': fields.related('finan_contrato_id', 'tipo_faturamento_id', type='many2one', relation='finan.tipo.faturamento', string=u'Tipo do faturamento', store=True),
    }


sped_documento()
