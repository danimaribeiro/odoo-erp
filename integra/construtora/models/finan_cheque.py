# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_cheque(osv.Model):
    _inherit = 'finan.cheque'

    _columns = {
        'condicao_contrato_id': fields.many2one('finan.contrato.condicao', u'Condição Pagamento Contrato', ondelete='cascade'),
    }


finan_cheque()

