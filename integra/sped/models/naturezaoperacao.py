# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields



class NaturezaOperacao(orm.Model):
    _description = u'Naturezas de Operação Fiscal'
    _name = 'sped.naturezaoperacao'
    _columns = {
        'nome': fields.char('Nome', size=60, required=True),
        'codigo': fields.char(u'Código', size=10, required=True),
        'considera_venda': fields.boolean('Considera venda'),
        'considera_devolucao_venda': fields.boolean('Considera devolução de venda'),
        'considera_compra': fields.boolean('Considera compra'),
        'considera_devolucao_compra': fields.boolean('Considera devolução de compra'),
        }

    _rec_name = 'nome'
    _order = 'nome'

    _sql_constraints = [
        ('codigo_unique', 'unique (codigo)',
        u'O código não pode se repetir!'),
        ('nome_unique', 'unique (nome)',
        u'O nome não pode se repetir!'),
        ]

NaturezaOperacao()
