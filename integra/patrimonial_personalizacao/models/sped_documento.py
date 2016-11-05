# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D
from sped.constante_tributaria import *
from sped.models.sped_documento import GRAVA_RELATED


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    def _get_soma_custo_estoque_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            for item_obj in doc_obj.documentoitem_ids:
                #
                # Para o custo da mercadoria para baixa do custo na venda/devolução
                #
                if nome_campo == 'vr_custo_estoque':
                    if item_obj.cfop_id.codigo in CFOPS_CUSTO_ESTOQUE_VENDA_DEVOLUCAO:
                        soma += D(str(getattr(item_obj, nome_campo, 0) or 0))

                else:
                    soma += D(str(getattr(item_obj, nome_campo, 0) or 0))

            soma = soma.quantize(D('0.01'))

            if nome_campo == 'vr_fatura' and doc_obj.deduz_retencao:
                soma -= D(str(doc_obj.vr_pis_retido))
                soma -= D(str(doc_obj.vr_cofins_retido))
                soma -= D(str(doc_obj.vr_csll))
                soma -= D(str(doc_obj.vr_irrf))
                soma -= D(str(doc_obj.vr_previdencia))
                soma -= D(str(doc_obj.vr_iss_retido))

            if (nome_campo == 'bc_previdencia' or nome_campo == 'vr_previdencia') and doc_obj.deduz_retencao:
                if soma < D('10'):
                    soma = D('0')

            res[doc_obj.id] = soma

        return res

    _columns = {
        #'vr_custo_estoque': fields.function(_get_soma_custo_estoque_funcao, type='float', string=u'Valor Custo Estoque', store=GRAVA_RELATED, digits=(18, 2)),
        'vr_custo_estoque': fields.function(_get_soma_custo_estoque_funcao, type='float', string=u'Valor Custo Estoque', store=True, digits=(18, 2)),
        'stock_picking_id': fields.many2one('stock.picking', u'Lista de separação'),
    }


sped_documento()
