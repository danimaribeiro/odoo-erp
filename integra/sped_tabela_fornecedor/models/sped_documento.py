# -*- encoding: utf-8 -*-

from osv import osv, fields
import base64
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    def importa_arquivo_fornecedor(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        item_pool = self.pool.get('sped.documentoitem')

        for nota_id in ids:
            nota_obj = self.pool.get('sped.documento').browse(cr, uid, nota_id)
            #
            # Marca o documento para não ir para o financeiro, nem para o estoque
            #
            dados = {
                'forma_pagamento': '2',
                'finan_documento_id': False,
                'finan_conta_id': False,
                'finan_centrocusto_id': False,
                'res_partner_bank_id': False,
                'finan_carteira_id': False,
                'payment_term_id': False,
            }
            nota_obj.write(dados)

            anexo_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_model', '=', 'sped.documento'), ('res_id', '=', nota_id), ('name', 'ilike', '.csv')])

            if not anexo_ids:
                print('saiu')
                continue

            print('vai fazer')
            #
            # Exclui todos os itens anteriores, que tenham sido importados sem o custo
            #
            cr.execute('delete from sped_documentoitem where documento_id = ' + str(nota_id) + ' and (vr_custo is null or vr_custo = 0);')
            nota_obj = self.pool.get('sped.documento').browse(cr, uid, nota_id)

            #
            # Abre o arquivo texto, e lê os campos
            #
            anexo_obj = self.pool.get('ir.attachment').browse(cr, uid, anexo_ids[0])
            txt = base64.decodestring(anexo_obj.datas)
            txt = txt.replace('\n\r', '\n')
            linhas = txt.split('\n')

            novos_itens = []

            for linha in linhas:
                if not linha:
                    continue

                campos = linha.split('|')
                codigo, ncm, preco = campos[0], campos[1], campos[2]
                codigo = codigo.strip().replace(' ', ' ')
                ncm = ncm.strip()
                preco = preco.strip()
                preco = D(preco.replace(',', '.'))

                #
                # Busca o id do produto e do NCM, se houver
                #
                sql = """
                select
                    p.id

                from
                    product_product p

                where
                    replace(p.default_code, ' ', ' ') = '{codigo}'

                order by
                    p.id

                limit 1;
                """
                sql = sql.format(codigo=codigo)
                cr.execute(sql)
                produto_ids = cr.fetchall()
                print(produto_ids, codigo)
                #produto_ids = self.pool.get('product.product').search(cr, 1, [('default_code', '=', codigo), '|', ('active', '=', True), ('active', '=', False)])
                ncm_ids = self.pool.get('sped.ncm').search(cr, uid, [('codigo', '=', ncm)])

                #
                # Não encontrou o produto
                #
                if not produto_ids:
                    print('nao achou o produto', codigo, ncm, produto_ids)
                    continue
                print('achou o produto', codigo, ncm)
                produto_ids = produto_ids[0]

                jah_existe = item_pool.search(cr, uid, [('documento_id', '=', nota_obj.id), ('produto_id', '=', produto_ids[0])])

                if len(jah_existe) >= 1:
                    print('ja existe', codigo, ncm)
                    continue

                produto_obj = self.pool.get('product.product').browse(cr, uid, produto_ids[0])
                #
                # Ajusta o novo NCM
                #
                if ncm_ids:
                    if (not produto_obj.ncm_id) or ncm_ids[0] != produto_obj.ncm_id.id:
                        try:
                            produto_obj.write({'ncm_id': ncm_ids[0]})
                        except:
                            pass

                #
                # Agora, vamos inserir o item e apurar o custo
                #
                contexto_item = {}
                print('vai inserir', codigo, ncm)

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
                    'produto_id': produto_obj.id,
                    'quantidade': D(1),
                    'vr_unitario': preco,
                }

                item_id = item_pool.create(cr, uid, dados)
                item_obj = item_pool.browse(cr, uid, item_id)

                dados_item = item_obj.onchange_produto(produto_obj.id, context=contexto_item)


                if (not 'value' in dados_item):
                    raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % codigo)

                #
                # Impede a geração de um movimento de estoque
                #
                dados_item['value']['stock_location_id'] = False
                dados_item['value']['stock_location_dest_id'] = False

                for chave in dados_item['value']:
                    if hasattr(item_obj, chave):
                        setattr(item_obj, chave, dados_item['value'][chave])

                dados_item_novo = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)

                for chave in dados_item_novo['value']:
                    if chave not in dados_item:
                        dados_item['value'][chave] = dados_item_novo['value'][chave]

                print(produto_obj.default_code, dados_item['value'])

                item_pool.write(cr, 1, [item_id], copy(dados_item['value']))
                cr.commit()

            ##
            ## Exclui todos os itens anteriores, que tenham sido importados sem o custo
            ##
            #cr.execute('delete from sped_documentoitem where documento_id = ' + str(nota_id) + ' and (vr_custo is null or vr_custo = 0);')

        return {}

    def atualiza_preco_compra_fornecedor(self, cr, uid, ids, context={}):
        for nota_obj in self.browse(cr, uid, ids):
            for item_obj in nota_obj.documentoitem_ids:
                if not item_obj.produto_id:
                    continue

                #
                # Vamos atualizar a tabela do fornecedor, com o código dele e o preço
                # de compra
                #
                sql = '''
                    select
                        ps.id

                    from
                        product_supplierinfo ps

                    where
                        ps.product_id = {product_id}
                        and ps.name = {partner_id}

                    limit 1;
                '''

                sql = sql.format(product_id=item_obj.produto_id.id, partner_id=nota_obj.partner_id.id)
                cr.execute(sql)
                dados = cr.fetchall()

                if len(dados) == 0:
                    continue

                partnerinfo_id = dados[0][0]

                sql = '''
                    select
                        pf.id

                    from
                        pricelist_partnerinfo pf

                    where
                        pf.min_quantity = 1
                        and pf.suppinfo_id = {partnerinfo_id};
                '''

                sql = sql.format(partnerinfo_id=partnerinfo_id)
                print(sql)
                cr.execute(sql)
                dados = cr.fetchall()

                if len(dados) == 0:
                    dados = {
                        'name': u'Preço de ',
                        'min_quantity': 1,
                        'suppinfo_id': partnerinfo_id,
                        'price': item_obj.vr_unitario,
                    }

                    self.pool.get('pricelist.partnerinfo').create(cr, uid, dados)
                else:
                    print(dados)
                    pricelist_id = dados[0][0]
                    self.pool.get('pricelist.partnerinfo').write(cr, uid, pricelist_id, {'price': item_obj.vr_unitario})

        return {}


sped_documento()
