# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from sped.models.sped_documento import GRAVA_RELATED


class sped_documento(osv.Model):
    _description = 'Documentos SPED'
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
        'vr_custo_estoque': fields.function(_get_soma_custo_estoque_funcao, type='float', string=u'Valor Custo Estoque', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_custo_estoque': fields.function(_get_soma_custo_estoque_funcao, type='float', string=u'Valor Custo Estoque', store=False, digits=(18, 2)),
    }

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        if ('nao_calcula' not in context) and ('gera_do_contrato' not in context):
            if ('state' in dados and dados['state'] in ['cancelada','denegada','inutilizada']) or \
                ('situacao' in dados and dados['situacao'] in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO):
                #
                # Exclui movimentações do estoque das notas canceladas
                #
                for doc_obj in self.browse(cr, uid, ids):
                    for item_obj in doc_obj.documentoitem_ids:
                        if item_obj.stock_move_id:
                            cr.execute("update stock_move set state='draft' where id = {move_id};".format(move_id=item_obj.stock_move_id.id))
                            cr.execute('delete from stock_move where id = {move_id}'.format(move_id=item_obj.stock_move_id.id))
            else:
                for doc_obj in self.browse(cr, uid, ids):
                    for item_obj in doc_obj.documentoitem_ids:
                        if (item_obj.documento_id.numero > 0) and (item_obj.documento_id.modelo in ['55', '01', '2D']) and (item_obj.stock_location_id and item_obj.stock_location_dest_id):
                            if item_obj.documento_id.modelo == '55' and item_obj.documento_id.emissao == '0' and item_obj.documento_id.state != 'autorizada':
                                continue

                            if item_obj.documento_id.modelo == '2D' and item_obj.documento_id.emissao == '0' and item_obj.documento_id.state != 'autorizada':
                                continue

                            item_obj.ajusta_estoque()

        return res


sped_documento()
