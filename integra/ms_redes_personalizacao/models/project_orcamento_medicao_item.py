# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class project_orcamento_medicao_item(osv.Model):
    _name = 'project.orcamento.medicao.item'
    _inherit = 'project.orcamento.medicao.item'


    _columns = {
        'quantidade_referencia': fields.related('orcamento_item_id','quantidade_referencia',  type='float', string=u'Quantidade referência', store=True),
        'quantidade_componente': fields.related('orcamento_item_id','quantidade_componente',  type='float', string=u'Quantidade composição', store=True),

        'quantidade_referencia_medida': fields.float(u'Quantidade referência Medida'),
        'quantidade_componente_medida': fields.float(u'Quantidade composição Medida'),
    }

    def onchange_quantidade_componente(self, cr, uid, ids, quantidade_componente, quantidade):
        if not quantidade_componente:
            quantidade_componente = D('0')
        else:
            quantidade_componente = D(quantidade_componente)

        if not quantidade:
            quantidade = D('0')
        else:
            quantidade = D(quantidade)

        quantidade *= quantidade_componente

        res = {
            'value': {
                'quantidade_medida': quantidade,
            }
        }

        return res


project_orcamento_medicao_item()
