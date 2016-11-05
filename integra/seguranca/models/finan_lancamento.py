# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class finan_lancamento(orm.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'tipo_faturamento_id': fields.related('contrato_id', 'tipo_faturamento_id', type='many2one', relation='finan.tipo.faturamento', string=u'Tipo do faturamento', store=True),
    }


finan_lancamento()
