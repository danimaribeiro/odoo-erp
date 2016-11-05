# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class rh_contabilidade(osv.Model):
    _name = 'rh.contabilidade'
    _description = u'Contabilização da Folha de Pagamento'

    _columns = {
        'slip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='cascade'),
        'data': fields.related('slip_id', 'date_from', type='date', string='Data'),
        'conta_credito_id': fields.many2one('finan.conta', u'Conta creditada'),
        'codigo_reduzido_credito': fields.related('conta_credito_id', 'codigo', type='char', string=u'Cód. Reduz. crédito'),
        'conta_debito_id': fields.many2one('finan.conta', u'Conta debitada'),
        'codigo_reduzido_debito': fields.related('conta_debito_id', 'codigo', type='char', string=u'Cód. Reduz. débito'),
        'valor': fields.float(u'Valor'),
        'codigo_historico': fields.char(u'Cód. Histórico', size=2048),
        'historico': fields.char(u'Complemento', size=2048),
    }


rh_contabilidade()
