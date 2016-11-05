# -*- coding: utf-8 -*-sped_finan.sped_gas_recebida_form


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from sped.constante_tributaria import *


class sped_documentoitem(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
        'finan_centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio', ondelete='restrict', select=True),
        'rateio_ids': fields.one2many('finan.rateio', 'sped_documentoitem_id', u'Itens do rateio'),
    }

    def realiza_rateio(self, cr, uid, ids, padrao={}, rateio={}, context={}):
        if not ids:
            return D(0)

        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        rateia_item_projeto = False
        total = D(0)
        for item_obj in self.browse(cr, uid, ids):
            p = copy(padrao)
            p['company_id'] = item_obj.documento_id.company_id.id
            produto_obj = item_obj.produto_id

            if getattr(item_obj.produto_id, 'conta_despesa_id', False):
                conta_entrada_obj = item_obj.produto_id.conta_despesa_id
            elif item_obj.produto_id.categ_id and getattr(item_obj.produto_id.categ_id, 'conta_despesa_id', False):
                conta_entrada_obj = item_obj.produto_id.categ_id.conta_despesa_id
            else:
                conta_entrada_obj = item_obj.documento_id.finan_conta_id

            if getattr(item_obj.produto_id, 'conta_receita_id', False):
                conta_saida_obj = item_obj.produto_id.conta_receita_id
            elif item_obj.produto_id.categ_id and getattr(item_obj.produto_id.categ_id, 'conta_receita_id', False):
                conta_saida_obj = item_obj.produto_id.categ_id.conta_receita_id
            else:
                conta_saida_obj = item_obj.documento_id.finan_conta_id

            #
            # Faz o rateio pelo projeto vinculado à compra
            #
            if getattr(item_obj, 'documentoitem_compra_ids', False) and len(item_obj.documentoitem_compra_ids) > 0:
                for item_compra_obj in item_obj.documentoitem_compra_ids:
                    if item_compra_obj.order_line_id:
                        if getattr(item_compra_obj.order_line_id, 'project_id', False):
                            p['project_id'] = item_compra_obj.order_line_id.project_id.id
                            ##
                            ## Quando houver projeto, a empresa tem que ser a empresa do projeto
                            ##
                            #p['company_id'] = item_compra_obj.order_line_id.project_id.company_id.id

                        if getattr(item_compra_obj.order_line_id, 'centrocusto_id', False):
                            rateia_item_projeto = True
                            p['centrocusto_id'] = item_compra_obj.order_line_id.centrocusto_id.id

                        if getattr(item_compra_obj.order_line_id, 'orcamento_item_id', False):
                            rateia_item_projeto = True
                            p['project_orcamento_item_id'] = item_compra_obj.order_line_id.orcamento_item_id.id

                        if getattr(item_compra_obj.order_line_id, 'orcamento_planejamento_id', False):
                            rateia_item_projeto = True
                            p['project_orcamento_item_planejamento_id'] = item_compra_obj.order_line_id.orcamento_planejamento_id.id

            #
            # Estrutura para determinar qual conta usar quando
            # despesa, custo ou receita no rateio
            #
            if item_obj.documento_id.entrada_saida == '0':
                conta_id = [
                    'tipo_conta',
                    {
                        'D': conta_entrada_obj.id,
                        'C': conta_entrada_obj.id,
                        False: conta_entrada_obj.id,
                    }
                ]

            else:
                conta_id = [
                    'tipo_conta',
                    {
                        'D': conta_saida_obj.id,
                        'C': conta_saida_obj.id,
                        False: conta_saida_obj.id,
                    }
                ]

            #
            # Trata a divisão entre custo de revenda e ativo, de acordo com a CFOP
            #
            if item_obj.cfop_id:
                if item_obj.cfop_id.codigo in CFOPS_COMPRA_COMERCIALIZACAO:
                    if conta_entrada_obj.conta_custo_revenda_id:
                        conta_id[1]['D'] = conta_entrada_obj.conta_custo_revenda_id.id
                        conta_id[1]['C'] = conta_entrada_obj.conta_custo_revenda_id.id
                        conta_id[1][False] = conta_entrada_obj.conta_custo_revenda_id.id

                elif item_obj.cfop_id.codigo in CFOPS_COMPRA_ATIVO:
                    if conta_entrada_obj.conta_custo_ativo_id:
                        conta_id[1]['D'] = conta_entrada_obj.conta_custo_ativo_id.id
                        conta_id[1]['C'] = conta_entrada_obj.conta_custo_ativo_id.id
                        conta_id[1][False] = conta_entrada_obj.conta_custo_ativo_id.id

                elif 'vr_custo_estoque' in context and item_obj.cfop_id.codigo in CFOPS_VENDA_MERCADORIA:
                    if conta_saida_obj.conta_custo_revenda_id:
                        conta_id[1]['D'] = conta_saida_obj.conta_custo_revenda_id.id
                        conta_id[1]['C'] = conta_saida_obj.conta_custo_revenda_id.id
                        conta_id[1][False] = conta_saida_obj.conta_custo_revenda_id.id

                elif 'vr_custo_estoque' in context and item_obj.cfop_id.codigo in CFOPS_VENDA_ATIVO:
                    if conta_entrada_obj.conta_custo_ativo_id:
                        conta_id[1]['D'] = conta_entrada_obj.conta_custo_ativo_id.id
                        conta_id[1]['C'] = conta_entrada_obj.conta_custo_ativo_id.id
                        conta_id[1][False] = conta_entrada_obj.conta_custo_ativo_id.id

                elif item_obj.cfop_id.codigo in CFOPS_VENDA_ATIVO:
                    print('eh venda de ativo', item_obj.cfop_id.codigo, conta_saida_obj.id, conta_saida_obj.conta_receita_ativo_id)
                    if conta_saida_obj.conta_receita_ativo_id:
                        conta_id[1]['D'] = conta_saida_obj.conta_receita_ativo_id.id
                        conta_id[1]['C'] = conta_saida_obj.conta_receita_ativo_id.id
                        conta_id[1][False] = conta_saida_obj.conta_receita_ativo_id.id


            p['conta_id'] = conta_id
            valor = D(item_obj.vr_produtos)

            if valor <= 0:
                continue

            total += valor
            print(item_obj.documento_id.rateio_ids)

            if rateia_item_projeto:
                for item_compra_obj in item_obj.documentoitem_compra_ids:
                    pp = copy(p)
                    if item_compra_obj.order_line_id:
                        item_pedido_compra_obj = item_compra_obj.order_line_id
                        if getattr(item_pedido_compra_obj, 'project_id', False):
                            pp['project_id'] = item_pedido_compra_obj.project_id.id
                            ##
                            ## Quando houver projeto, a empresa tem que ser a empresa do projeto
                            ##
                            #pp['company_id'] = item_pedido_compra_obj.project_id.company_id.id

                        if getattr(item_compra_obj.order_line_id, 'centrocusto_id', False):
                            pp['centrocusto_id'] = item_compra_obj.order_line_id.centrocusto_id.id

                        if getattr(item_pedido_compra_obj, 'orcamento_item_id', False):
                            pp['project_orcamento_item_id'] = item_pedido_compra_obj.orcamento_item_id.id

                        if getattr(item_compra_obj.order_line_id, 'orcamento_planejamento_id', False):
                            rateia_item_projeto = True
                            p['project_orcamento_item_planejamento_id'] = item_compra_obj.order_line_id.orcamento_planejamento_id.id

                        #
                        # Atribui o percentual correto para o item do pedido
                        #
                        valor_parcial = valor * D(item_compra_obj.quantidade_item or 0) / D(item_obj.quantidade or 1)

                        #
                        # Realiza o rateio parcial, do item do projeto, do item do pedido de compra,
                        # de acordo com o centro de custo do pedido de compra
                        #
                        if item_pedido_compra_obj.centrocusto_id:
                            cc_pool.realiza_rateio(cr, uid, [item_pedido_compra_obj.centrocusto_id.id], valor=valor_parcial, padrao=pp, rateio=rateio, context=context)
                        elif item_pedido_compra_obj.order_id.centrocusto_id:
                            cc_pool.realiza_rateio(cr, uid, [item_pedido_compra_obj.order_id.centrocusto_id.id], valor=valor_parcial, padrao=pp, rateio=rateio, context=context)
                        elif item_obj.documento_id.finan_centrocusto_id:
                            cc_pool.realiza_rateio(cr, uid, [item_obj.documento_id.finan_centrocusto_id.id], valor=valor_parcial, padrao=pp, rateio=rateio, context=context)
                        elif item_obj.documento_id.rateio_ids:
                            for rateio_obj in item_obj.documento_id.rateio_ids:
                                ppp = copy(pp)

                                for campo in cc_pool.campos_rateio(cr, uid):
                                    if getattr(rateio_obj, campo, False):
                                        ppp[campo] = getattr(rateio_obj, campo, False)

                                        if '_id' in campo:
                                            if ppp[campo]:
                                                ppp[campo] = ppp[campo].id
                                            else:
                                                ppp[campo] = False

                                valor_parcial_item = valor_parcial * D(rateio_obj.porcentagem) / D(100)
                                cc_pool._realiza_rateio(valor_parcial_item, 100, campos, ppp, rateio)


                        print('rateio depois', rateio)

            elif item_obj.rateio_ids:
                cc_pool.realiza_rateio(cr, uid, [item_obj.id], valor=valor, padrao=p, rateio=rateio, context=context, tabela_pool=self.pool.get('sped.documentoitem'))

            elif item_obj.finan_centrocusto_id:
                cc_pool.realiza_rateio(cr, uid, [item_obj.finan_centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)

            elif getattr(item_obj.documento_id, 'purchase_order_id', False) and getattr(item_obj.documento_id.purchase_order_id, 'rateio_ids', False):
                for rateio_obj in item_obj.documento_id.purchase_order_id.rateio_ids:
                    pp = copy(p)

                    for campo in cc_pool.campos_rateio(cr, uid):
                        if getattr(rateio_obj, campo, False):
                            pp[campo] = getattr(rateio_obj, campo, False)

                            if '_id' in campo:
                                if pp[campo]:
                                    pp[campo] = pp[campo].id
                                else:
                                    pp[campo] = False

                    valor_parcial = valor * D(rateio_obj.porcentagem) / D(100)
                    cc_pool._realiza_rateio(valor_parcial, 100, campos, pp, rateio)

            elif item_obj.documento_id.finan_centrocusto_id:
                cc_pool.realiza_rateio(cr, uid, [item_obj.documento_id.finan_centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)

            elif item_obj.documento_id.rateio_ids:
                for rateio_obj in item_obj.documento_id.rateio_ids:
                    pp = copy(p)

                    for campo in cc_pool.campos_rateio(cr, uid):
                        if getattr(rateio_obj, campo, False):
                            pp[campo] = getattr(rateio_obj, campo, False)

                            if '_id' in campo:
                                if pp[campo]:
                                    pp[campo] = pp[campo].id
                                else:
                                    pp[campo] = False

                    valor_parcial = valor * D(rateio_obj.porcentagem) / D(100)
                    cc_pool._realiza_rateio(valor_parcial, 100, campos, pp, rateio)

                #cc_pool.realiza_rateio(cr, uid, [False], valor=valor, padrao=p, rateio=rateio, context=context, tabela_pool=self.pool.get('sped.documento'))

            else:
                cc_pool._realiza_rateio(valor, 100, campos, p, rateio)

        return total


sped_documentoitem()
