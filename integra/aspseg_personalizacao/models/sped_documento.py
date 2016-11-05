# -*- coding: utf-8 -*-

from osv import osv, fields
from sped.constante_tributaria import *
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, formata_data


class sped_documento(osv.Model):
    _description = 'Documentos SPED'
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    def buscar_remessa(self, cr, uid, ids, context={}):
        if not len(ids):
            return {}

        res = {}

        ajusta_valor_venda = context.get('ajusta_valor_venda', False)

        for nota_obj in self.browse(cr, uid, ids):

            sped_item_obj = nota_obj.documentoitem_ids


            dados_nota = {
                    'company_id': nota_obj.company_id.id,
                    'partner_id': nota_obj.partner_id.id,
                    'operacao_id': nota_obj.operacao_id.id,
                }
            contexto_item = copy(dados_nota)
            contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
            for chave in dados_nota:
                if 'default_' not in chave:
                    contexto_item['default_' + chave] = contexto_item[chave]

            contexto_item['entrada_saida'] = nota_obj.entrada_saida
            contexto_item['regime_tributario'] = nota_obj.regime_tributario
            contexto_item['emissao'] = nota_obj.emissao
            contexto_item['data_emissao'] = nota_obj.data_emissao
            contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
            contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
            contexto_item['default_emissao'] = nota_obj.emissao
            contexto_item['default_data_emissao'] = nota_obj.data_emissao

            #
            # Busca o Produto e quantidade.
            #

            sql = """
                select
                    pp.id,
                    sum( case when
                    es.tipo = 'S' THEN
                    es.quantidade * -1
                    else
                    es.quantidade
                    end) as quantidade
                from
                    estoque_entrada_saida es
                    join product_product pp on pp.id = es.product_id
                    join product_template pt on pt.id = pp.product_tmpl_id
                    join stock_location sl on sl.id = es.location_id

                where
                    es.location_id = 20 and
                    sl.usage = 'internal'

                group by
                    pp.id
            """

            cr.execute(sql.format())
            dados_select = cr.fetchall()
            dados = {}

            for product_id, quantidade in dados_select:
                #
                # Itens vendidos na totalidade não entram no retorno
                #
                if quantidade <= 0:
                    continue

                dados = {
                         'documento_id': nota_obj.id,
                         'produto_id': product_id,
                         'quantidade': quantidade,
                        }
                #
                # busca o valor unitario do documento.
                #
                sql_opercao = """
                            select
                                coalesce(sdi.vr_unitario,0) as valor
                            from
                                sped_documento sp
                                join sped_documentoitem sdi on sdi.documento_id = sp.id
                            where
                                sp.operacao_id = 5
                                and sp.id < {documento_id}
                                and sdi.produto_id = {produto_id}
                            order by
                                sp.id desc
                                limit 1"""

                cr.execute(sql_opercao.format(documento_id=nota_obj.id, produto_id=product_id))
                operacao = cr.fetchall()
                for valor in operacao:
                    valor = D(valor[0])
                    dados['vr_unitario'] =  valor

                novo = True
                if len(sped_item_obj) > 0:
                    for item_sped in sped_item_obj:
                        if item_sped.produto_id.id == product_id:
                            item_sped.write({'quantidade': quantidade })
                            item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_sped.id)
                            novo = False
                            break

                dados_item = {}
                if novo:
                    item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados, context=contexto_item)
                    item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)
                    dados_item = item_obj.onchange_produto(product_id, context=contexto_item)

                    if not 'value' in dados_item:
                        raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % product_id)

                    for chave in dados_item['value']:
                        if hasattr(item_obj, chave):
                            setattr(item_obj, chave, dados_item['value'][chave])

                dados_item_novo = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                dados_item.update(dados_item_novo['value'])
                item_obj.write(dados_item)

            #
            # Lança nas observações os dados da nota de remessa que está sendo
            # retornada
            #
            sql_remessa_retornada = """
                        select
                            sp.id
                        from
                            sped_documento sp
                        where
                            sp.operacao_id = 5
                            and sp.id < {documento_id}
                        order by
                            sp.id desc
                            limit 1"""
            nota_remessa_ids = self.search(cr, uid, [('operacao_id', '=', 5), ('id', '<', nota_obj.id)], order='id desc')
            nota_remessa_obj = self.browse(cr, uid, nota_remessa_ids[0])

            data = parse_datetime(nota_remessa_obj.data_emissao_brasilia).date()
            data = formata_data(data)
            mensagem = u'Retorno referente à remessa de venda ambulante NF-e nº {numero} do dia {data}'.format(numero=nota_remessa_obj.numero, data=data)
            nota_obj.write({'infcomplementar': mensagem})
            nota_obj.ajusta_impostos_retidos()

            return res

    def buscar_retorno(self, cr, uid, ids, context={}):
            if not len(ids):
                return {}

            res = {}

            ajusta_valor_venda = context.get('ajusta_valor_venda', False)

            for nota_obj in self.browse(cr, uid, ids):

                dados_nota = {
                        'company_id': nota_obj.company_id.id,
                        'partner_id': nota_obj.partner_id.id,
                        'operacao_id': nota_obj.operacao_id.id,
                    }
                contexto_item = copy(dados_nota)
                contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
                for chave in dados_nota:
                    if 'default_' not in chave:
                        contexto_item['default_' + chave] = contexto_item[chave]

                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao

                #
                # Busca o Produto e quantidade.
                #

                sql = """
                select
                    sp.id
                from
                    sped_documento sp
                    join sped_documentoitem sdi on sdi.documento_id = sp.id

                where
                    sp.operacao_id = 6

                order by
                    sp.id desc
                    limit 1
                """

                cr.execute(sql.format())
                dado_select = cr.fetchall()
                dados = {}

                for id in dado_select:
                    id = id[0]

                print(id)

                sped_obj = self.pool.get('sped.documento').browse(cr, uid, id)
                sped_itens = sped_obj.documentoitem_ids

                for itemsped_obj in sped_itens:

                    dados = {
                         'documento_id': nota_obj.id,
                         'produto_id': itemsped_obj.produto_id.id,
                         'quantidade': itemsped_obj.quantidade,
                         'vr_unitario': itemsped_obj.vr_unitario,
                        }

                    item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados, context=contexto_item)
                    item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)

                    dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)

                    if not 'value' in dados_item:
                        raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % item_obj.produto_id.name_template)

                    item_obj.write(dados_item['value'])

                    dados_item = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                    item_obj.write(dados_item['value'])


            nota_obj.ajusta_impostos_retidos()

            return res


    def buscar_itens_retorno(self, cr, uid, ids, context={}):
        if not len(ids):
            return {}

        res = {}

        ajusta_valor_venda = context.get('ajusta_valor_venda', False)

        for nota_obj in self.browse(cr, uid, ids):

            sped_item_obj = nota_obj.documentoitem_ids
            sped_itemreferenciado_objs = nota_obj.documentoreferenciado_ids

            if len(sped_itemreferenciado_objs) == 0:
                raise osv.except_osv(u'Erro!', u' Não existem Notas de Retorno Vinculadas!')

            dados_nota = {
                    'company_id': nota_obj.company_id.id,
                    'partner_id': nota_obj.partner_id.id,
                    'operacao_id': nota_obj.operacao_id.id,
                }
            contexto_item = copy(dados_nota)
            contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
            for chave in dados_nota:
                if 'default_' not in chave:
                    contexto_item['default_' + chave] = contexto_item[chave]

            contexto_item['entrada_saida'] = nota_obj.entrada_saida
            contexto_item['regime_tributario'] = nota_obj.regime_tributario
            contexto_item['emissao'] = nota_obj.emissao
            contexto_item['data_emissao'] = nota_obj.data_emissao
            contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
            contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
            contexto_item['default_emissao'] = nota_obj.emissao
            contexto_item['default_data_emissao'] = nota_obj.data_emissao


            if len(sped_item_obj) > 0:
                for item_sped in sped_item_obj:
                    item_sped.unlink()

            for sped_itemreferenciado_obj in sped_itemreferenciado_objs:
                sql = """
                    select
                        sde.id
                    from
                        sped_documentoitem sde
                        join sped_documento sd on sd.id = sde.documento_id

                    where
                        sd.id = {documento_id}

                """
                cr.execute(sql.format(documento_id=sped_itemreferenciado_obj.documentoreferenciado_id.id))
                documentos = cr.fetchall()
                for id, in documentos:

                    documento_item = self.pool.get('sped.documentoitem').browse(cr, uid, id)

                    if documento_item.produto_id:

                        dados = {
                             'documento_id': nota_obj.id,
                             'produto_id': documento_item.produto_id.id,
                             'quantidade': documento_item.quantidade,
                             'vr_unitario': documento_item.vr_unitario,
                            }

                        item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados, context=contexto_item)
                        item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)
                        dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)

                        if not 'value' in dados_item:
                            raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % item_obj.produto_id.id)

                        item_obj.write(dados_item['value'])

                        dados_item = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                        item_obj.write(dados_item['value'])


            nota_obj.ajusta_impostos_retidos()

            return res

    def action_enviar(self, cr, uid, ids, context=None):
        lancamento_pool = self.pool.get('finan.lancamento')
        order_pool = self.pool.get('sale.order')

        res = super(sped_documento, self).action_enviar(cr, uid, ids, context=None)

        for doc_obj in self.browse(cr, uid, ids, context=context):

            if doc_obj.state == 'autorizada':
                if doc_obj.duplicata_ids and doc_obj.sale_order_ids:
                    duplicata_obj = doc_obj.duplicata_ids[0]
                    order_obj = doc_obj.sale_order_ids[0]

                    if duplicata_obj.finan_lancamento_id and len(order_obj.finan_sale_ids) > 0:

                        lancamento_obj = duplicata_obj.finan_lancamento_id
                        for finan_sale_obj in order_obj.finan_sale_ids:

                            if lancamento_obj.tipo == 'R':
                                tipo = 'PR'
                            else:
                                tipo = 'PP'
                            if lancamento_obj.res_partner_bank_id:
                                banco_id = lancamento_obj.res_partner_bank_id.id
                            else:
                                banco_id = order_obj.operacao_fiscal_produto_id.res_partner_bank_id.id

                            dados_pagamento = {
                                'lancamento_id': lancamento_obj.id,
                                'company_id': lancamento_obj.company_id.id,
                                'formapagamento_id': finan_sale_obj.formapagamento_id.id,
                                'valor_documento': D(finan_sale_obj.valor),
                                'valor': D(finan_sale_obj.valor),
                                'res_partner_bank_id': banco_id,
                                'tipo': tipo,
                                'data_quitacao': finan_sale_obj.data,
                             }

                            user_id = finan_sale_obj.create_uid.id
                            lancamento_pool.create(cr, user_id, dados_pagamento)

                    if order_obj.finan_formapagamento_id:
                        for dup_obj in doc_obj.duplicata_ids:
                            lancamento_pool.write(cr, uid, [dup_obj.finan_lancamento_id.id], {'formapagamento_id': order_obj.finan_formapagamento_id.id})

                    if duplicata_obj.finan_lancamento_id and len(order_obj.cheque_ids) > 0:

                        lancamento_obj = duplicata_obj.finan_lancamento_id

                        for cheque_obj in order_obj.cheque_ids:

                            user_id = cheque_obj.create_uid.id
                            sql = """
                            insert into finan_cheques_itens (cheque_id, lancamento_id ) values ( {cheque_id} , {lancamento_id} )
                            """
                            sql = sql.format(cheque_id=cheque_obj.id, lancamento_id=lancamento_obj.id)
                            print(sql)
                            cr.execute(sql)

                        lancamento_obj.quitar_titulo()

        return res


sped_documento()
