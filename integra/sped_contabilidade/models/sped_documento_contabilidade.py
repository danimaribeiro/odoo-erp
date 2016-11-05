# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_documento_contabilidade(osv.Model):
    _name = 'sped.documento.contabilidade'
    _description = u'Contabilização do documento fiscal'

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento fiscal', ondelete='cascade'),
        'documentoitem_id': fields.many2one('sped.documentoitem', u'Item de Documento fiscal', ondelete='cascade'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Documento financeiro', ondelete='cascade'),
        'tipo': fields.char(u'tipo', size=02),
        'data': fields.related('documento_id', 'data_entrada_saida_brasilia', type='date', string='Data'),
        'conta_credito_id': fields.many2one('finan.conta', u'Conta creditada'),
        'codigo_reduzido_credito': fields.related('conta_credito_id', 'codigo', type='char', string=u'Cód. Reduz. crédito'),
        'conta_debito_id': fields.many2one('finan.conta', u'Conta debitada'),
        'codigo_reduzido_debito': fields.related('conta_debito_id', 'codigo', type='char', string=u'Cód. Reduz. débito'),
        'valor': fields.float(u'Valor'),
        'codigo_historico': fields.char(u'Cód. Histórico', size=2048),
        'historico': fields.char(u'Complemento', size=2048),
    }


sped_documento_contabilidade()
