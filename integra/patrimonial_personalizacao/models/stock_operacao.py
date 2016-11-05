# -*- coding: utf-8 -*-

from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64


TIPO_OPERACAO = (
    ('S', u'Ordem de entrega'),
    ('I', u'Movimentação interna'),
    ('T', u'Transferência'),
    ('V', u'Entrada de inventário'),
    ('E', u'Ordem de entrega de EPI'),
)


class stock_operacao(osv.osv):
    _name = 'stock.operacao'
    _rec_name = 'nome'
    _order = 'nome'


    _columns = {
        'company_ids': fields.many2many('res.company', 'stock_operacao_company', 'stock_operacao_id', 'company_id', u'Empresas permitidas'),
        'company_id': fields.many2one('res.company', u'Empresa', select=True),
        'nome': fields.char(u'Operação', size=80, select=True, required=True),
        'location_id': fields.many2one('stock.location', u'Saída de', select=True),
        'location_dest_id': fields.many2one('stock.location', u'Entrada em', select=True),
        'obs': fields.text(u'Observações'),

        'traz_custo_medio': fields.boolean(u'Traz custo médio automático?'),
        'local_custo_ids': fields.one2many('stock.operacao.local.custo', 'operacao_id', u'Locais de origem para o custo médio'),
        'nota_locacao_ids': fields.one2many('stock.operacao.nota.locacao', 'operacao_id', u'Configurações para baixas de produtos para locação'),

        'tipo': fields.selection(TIPO_OPERACAO, u'Tipo', select=True),
    }


stock_operacao()


class res_company(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'stock_operacao_ids': fields.many2many('stock.operacao', 'stock_operacao_company', 'company_id', 'stock_operacao_id', u'Operações de estoque permitidas'),
    }


res_company()


class stock_operacao_local_custo(osv.Model):
    _description = u'Locais para custo da operação de estoque'
    _name = 'stock.operacao.local.custo'
    _order = 'operacao_id, ordem'

    _columns = {
        'operacao_id': fields.many2one('stock.operacao', u'Operação', ondelete='cascade'),
        'ordem': fields.integer(u'Ordem de seleção', select=True),
        'stock_location_id': fields.many2one('stock.location', u'Local de origem', ondelete='restrict'),
    }


stock_operacao_local_custo()


class stock_operacao_nota_locacao(osv.Model):
    _name = 'stock.operacao.nota.locacao'
    _description = u'Configuração de baixas de produtos para locação'
    _order = 'operacao_id, familiatributaria_id'

    _columns = {
        'operacao_id': fields.many2one('stock.operacao', u'Operação', ondelete='cascade'),
        'location_id': fields.many2one('stock.location', u'Saída de', ondelete='restrict'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária', ondelete='restrict'),
    }


stock_operacao_nota_locacao()

