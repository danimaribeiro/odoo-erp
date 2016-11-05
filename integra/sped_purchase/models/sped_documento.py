# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *


class sped_documento(osv.Model):
    _inherit = 'sped.documento'

    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', u'Pedido de compra'),
        'purchase_order_provisao_excluida': fields.boolean(u'Provisão do pedido compra já excluída?'),

        #
        # Campo pra tapear o open...
        #
        'purchase_order_ids': fields.many2many('purchase.order', 'sped_documento', 'id', 'purchase_order_id', u'Pedido de compra'),
    }

    def onchange_purchase_order_id(self, cr, uid, ids, purchase_order_id, context={}):
        if not purchase_order_id:
            return {}

        valores = {}
        res = {'value': valores}

        order_obj = self.pool.get('purchase.order').browse(cr, uid, purchase_order_id)


        if getattr(order_obj, 'centrocusto_id', False):
            valores['finan_centrocusto_id'] = order_obj.centrocusto_id.id

        if getattr(order_obj, 'rateio_ids', False):
            cc_pool = self.pool.get('finan.centrocusto')
            rateio_ids = [
                (5, False, False),
            ]
            for rateio_obj in order_obj.rateio_ids:
                rateio = {}
                for campo in cc_pool.campos_rateio(cr, uid):
                    rateio[campo] = getattr(rateio_obj, campo, False)
                    if '_id' in campo:

                        if rateio[campo]:
                            rateio[campo] = rateio[campo].id
                        else:
                            rateio[campo] = False

                rateio['porcentagem'] = getattr(rateio_obj, 'porcentagem', 0)
                rateio_ids.append([0, False, rateio])

            valores['rateio_ids'] = rateio_ids

            if len(rateio_ids) and 'conta_id' in rateio_ids[0] and rateio_ids[0]['conta_id']:
                valores['finan_conta_id'] = rateio_ids[0]['conta_id']

        if getattr(order_obj, 'payment_term_id', False):
            valores['payment_term_id'] = order_obj.payment_term_id.id

        if getattr(order_obj, 'partner_bank_id', False):
            valores['res_partner_bank_id'] = order_obj.partner_bank_id.id

        return res

    def cancela_provisao_pedido_compra(self, cr, uid, ids, context={}):
        sql = '''
            select
                distinct pol.order_id
            from
                sped_documento d
                join sped_documentoitem di on di.documento_id = d.id
                join sped_documentoitem_compra dic on dic.documentoiten_id = di.id
                join purchase_order_line pol on pol.id = dic.order_line_id
            where
                d.id = {documento_id}
                and coalesce(d.purchase_order_provisao_excluida, False) = False;
        '''

        lancamento_pool = self.pool.get('finan.lancamento')

        if 'purchase_order_id' not in lancamento_pool._columns:
            return

        for id in ids:
            cr.execute(sql.format(documento_id=id))
            dados = cr.fetchall()
            if not len(dados):
                continue

            for pedido_id, in dados:
                lanc_ids = lancamento_pool.search(cr, 1, [('provisionado', '=', True), ('purchase_order_id', '=', pedido_id)], order='data_vencimento')

                if lanc_ids:
                    lancamento_pool.unlink(cr, 1, [lanc_ids[0]])
                    cr.execute('update sped_documento set purchase_order_provisao_excluida = True where id = ' + str(id))
                #cr.execute('''
                    #delete from finan_lancamento where provisionado = True and purchase_order_id = {pedido_id};
                #'''.format(pedido_id=pedido_id))

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        self.pool.get('sped.documento').cancela_provisao_pedido_compra(cr, uid, ids, context=context)

        return res

    def create(self, cr, uid, dados, context={}):
        res = super(sped_documento, self).create(cr, uid, dados, context=context)

        self.pool.get('sped.documento').cancela_provisao_pedido_compra(cr, uid, [res], context=context)

        return res

    def trata_itens_pedido_compra(self, cr, uid, ids, context={}):
        res = {}
        item_compra_pool = self.pool.get('sped.documentoitem.compra')

        for nota_obj in self.browse(cr, uid, ids, context=context):
            if nota_obj.emissao == TIPO_EMISSAO_PROPRIA:
                continue

            if not nota_obj.operacao_id:
                continue

            if not nota_obj.purchase_order_id:
                continue

            #
            # Vamos analisar cada item da nota, vinculando o produto correto,
            # e apropriando créditos de acordo com a operação ou com a úlitma
            # compra do mesmo produto
            #
            for item_obj in nota_obj.documentoitem_ids:
                if not item_obj.produto_id:
                    continue

                if item_obj.documentoitem_compra_ids:
                    continue

                #
                # Buscamos no pedido de compra o item correspondente ao mesmo
                # produto
                #
                item_pedido_id = False
                for item_pedido_obj in nota_obj.purchase_order_id.order_line:
                    if item_pedido_obj.product_id.id == item_obj.produto_id.id:
                        item_pedido_id = item_pedido_obj.id
                        break

                if not item_pedido_id:
                    continue

                contexto_item = {
                    'default_product_id': item_obj.produto_id.id,
                    'default_partner_id': nota_obj.partner_id.id,
                    'default_data_emissao': nota_obj.data_emissao
                }

                dados = item_compra_pool.onchange_itempredido(cr, uid, False, item_pedido_id, nota_obj.data_emissao, item_obj.vr_unitario, item_obj.quantidade, context=contexto_item)
                dados = dados['value']
                dados['order_line_id'] = item_pedido_id
                dados['documentoiten_id'] = item_obj.id
                dados['product_id'] = item_obj.produto_id.id
                dados['partner_id'] = nota_obj.partner_id.id
                dados['data_emissao'] = nota_obj.data_emissao
                item_compra_pool.create(cr, uid, dados)

        return True

    def lanca_itens_pedido_compra(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('sped.documentoitem')

        for nota_obj in self.browse(cr, uid, ids):
            #
            # Somente notas de entrada de terceiros
            #
            if nota_obj.emissao != '1':
                continue

            #
            # Notas sem vinculo com o pedido de compra
            #
            if not nota_obj.purchase_order_id:
                continue

            #
            # Outros documentos que não NF-e, elimina os itens e relança tudo
            # vindo do pedido de compra
            #
            if nota_obj.modelo == '55':
                continue

            for item_obj in nota_obj.documentoitem_ids:
                item_obj.unlink()

            #
            # Prepara a inclusãos de TODOS os produtos do pedido de compra
            #
            for peditem_obj in nota_obj.purchase_order_id.order_line:
                #
                # Agora, vamos inserir o item e apurar o custo
                #
                contexto_item = {}
                contexto_item['company_id'] = nota_obj.company_id.id
                contexto_item['default_company_id'] = nota_obj.company_id.id
                contexto_item['partner_id'] = nota_obj.partner_id.id
                contexto_item['default_partner_id'] = nota_obj.partner_id.id
                contexto_item['operacao_id'] = nota_obj.operacao_id.id
                contexto_item['default_operacao_id'] = nota_obj.operacao_id.id
                contexto_item['ajusta_valor_venda'] = False
                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao

                #
                # Criando os dados do item
                #
                dados = {
                    'documento_id': nota_obj.id,
                    'produto_id': peditem_obj.product_id.id,
                    'quantidade': D(peditem_obj.product_qty or 0),
                    'vr_unitario': D(peditem_obj.price_unit or 0),
                }

                item_id = item_pool.create(cr, uid, dados)
                item_obj = item_pool.browse(cr, uid, item_id)

                dados_item = item_obj.onchange_produto(peditem_obj.product_id.id, context=contexto_item)


                if (not 'value' in dados_item):
                    raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % peditem_obj.product_id.name)

                for chave in dados_item['value']:
                    if hasattr(item_obj, chave):
                        setattr(item_obj, chave, dados_item['value'][chave])

                dados_item_novo = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)

                for chave in dados_item_novo['value']:
                    if chave not in dados_item:
                        dados_item['value'][chave] = dados_item_novo['value'][chave]

                item_pool.write(cr, 1, [item_id], copy(dados_item['value']))
                cr.commit()

        itemcompra_pool = self.pool.get('sped.documentoitem.compra')

        for nota_obj in self.browse(cr, uid, ids):
            #
            # Somente notas de entrada de terceiros
            #
            if nota_obj.emissao != '1':
                continue

            #
            # Notas sem vinculo com o pedido de compra
            #
            if not nota_obj.purchase_order_id:
                continue

            for peditem_obj in nota_obj.purchase_order_id.order_line:
                for item_obj in nota_obj.documentoitem_ids:
                    if peditem_obj.product_id.id == item_obj.produto_id.id:
                        dados = itemcompra_pool.onchange_itempredido(cr, uid, False, peditem_obj.id, nota_obj.data_emissao, item_obj.vr_unitario, item_obj.quantidade, context={})
                        dados = dados['value']

                        dados.update({
                            'order_line_id': peditem_obj.id,
                            'documentoiten_id': item_obj.id,
                        })
                        itemcompra_pool.create(cr, uid, dados)
                        break

        return {}

sped_documento()
