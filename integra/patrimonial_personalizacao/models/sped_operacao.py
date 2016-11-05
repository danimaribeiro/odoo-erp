# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_operacao(osv.Model):
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'bonifica_pedido': fields.boolean(u'Vincula a orçamento de bonificação?'),
        'nota_locacao_ids': fields.one2many('sped.operacao.nota.locacao', 'operacao_id', u'Configurações para notas de locação'),
        'stock_operacao_id': fields.many2one('stock.operacao', u'Operação de Estoque'),
    }


sped_operacao()


class sped_operacao_nota_locacao(osv.Model):
    _name = 'sped.operacao.nota.locacao'
    _description = u'Configuração de notas de locação'
    _order = 'operacao_id, familiatributaria_id'

    _columns = {
        'operacao_id': fields.many2one('sped.operacao', u'Operação', ondelete='cascade'),
        'location_id': fields.many2one('stock.location', u'Saída de', ondelete='restrict'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária', ondelete='restrict'),
    }


sped_operacao_nota_locacao()

