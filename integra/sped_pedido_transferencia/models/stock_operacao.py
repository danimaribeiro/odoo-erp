# -*- coding: utf-8 -*-

from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64


TIPO_OPERACAO = (
    ('S', u'Ordem de entrega'),
    ('I', u'Movimentação interna'),
    ('T', u'Transferência'),
)


class stock_operacao(osv.osv):
    _name = 'stock.operacao'
    _inherit = 'stock.operacao'

    _columns = {
        #'tipo': fields.selection(TIPO_OPERACAO, u'Tipo', select=True),
        'remetente_id': fields.many2one('res.company', u'Remetente da NF-e', ondelete='restrict'),
        'sped_operacao_id': fields.many2one('sped.operacao', u'Operação fiscal', ondelete='restrict'),
        'familiatributaria_ids': fields.many2many('sped.familiatributaria', 'stock_operacao_familiatributaria', 'operacao_id', 'familiatributaria_id', u'Famílias tributárias'),
    }


stock_operacao()
