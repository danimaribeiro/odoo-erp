# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'unidade_contrato_servico_id': fields.many2one('res.company', u'Unidade para geração do contrato de serviços'),
        'operacao_fiscal_remessa_locacao_novo_id': fields.many2one('sped.operacao', u'Operação padrão para remessa de produtos novos em locação'),
        'operacao_fiscal_remessa_locacao_usado_id': fields.many2one('sped.operacao', u'Operação padrão para remessa de produtos usados em locação'),
        
        'operacao_estoque_baixa_locacao_novo_id': fields.many2one('stock.operacao', u'Operação de estoque padrão para baixa de produtos novos em locação'),
        'operacao_estoque_baixa_locacao_usado_id': fields.many2one('stock.operacao', u'Operação de estoque padrão para baixa de produtos usados em locação'),
    }

res_company()
