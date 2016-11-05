# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_documentoitem(osv.Model):
    _description = 'Itens de documentos SPED'
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    def _get_custo_unitario_estoque(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #for id in ids:
            #res[id] = 0

        #return res

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.operacao_id.traz_custo_medio:
                res[item_obj.id] = D(item_obj.vr_unitario)

            #elif item_obj.stock_location_id:
            elif not item_obj.produto_id:
                res[item_obj.id] = 0

            else:
                location_pool = self.pool.get('stock.location')

                location_ids = location_pool.search(cr, uid, [('padrao_contabilidade', '=', True )])

                quantidade = D(0)
                custo = D(0)

                for location_id in location_ids:
                    sql_saldo = """
                    select
                        coalesce(s.quantidade, 0) as quantidade,
                        coalesce(s.vr_unitario_medio, 0) as vr_unitario_custo

                    from
                        stock_saldo s
                    where
                        s.company_id = {company_id}
                        and s.data = '{data}'
                        and s.product_id = {product_id}
                        and s.location_id = {location_id};
                    """

                    sql_custo = """
                       select
                           coalesce(cm.quantidade, 0) as quantidade,
                           coalesce(cm.vr_unitario_custo, 0) as vr_unitario_custo

                       from
                           custo_medio({company_id}, {location_id}, {product_id}) cm

                       where
                           cm.data <= '{data}'

                       order by
                           cm.data desc, cm.entrada_saida desc, cm.move_id desc

                       limit 1;
                    """

                    if item_obj.company_id.matriz_id:
                        sql_saldo = sql_saldo.format(company_id=item_obj.company_id.matriz_id.id, location_id=location_id, product_id=item_obj.produto_id.id,data=item_obj.data_emissao)
                        sql_custo = sql_custo.format(company_id=item_obj.company_id.matriz_id.id, location_id=location_id, product_id=item_obj.produto_id.id,data=item_obj.data_emissao)

                    else:
                        sql_saldo = sql_saldo.format(company_id=item_obj.company_id.id,location_id=location_id, product_id=item_obj.produto_id.id,data=item_obj.data_emissao)
                        sql_custo = sql_custo.format(company_id=item_obj.company_id.id,location_id=location_id, product_id=item_obj.produto_id.id,data=item_obj.data_emissao)

                    print(sql_saldo)
                    cr.execute(sql_saldo)
                    dados = cr.fetchall()

                    if not len(dados):
                        print(sql_custo)
                        cr.execute(sql_custo)
                        dados = cr.fetchall()

                    if not dados:
                        continue

                    quantidade += D(dados[0][0] or 0)

                    ### 08/04/2016 conforme movimentação de estoque negativas foi alterado para quantidade 01.

                    if quantidade <= 0:
                        quantidade = 1
                        custo += quantidade * D(dados[0][1] or 0)
                    else:
                        custo += D(dados[0][0] or 0) * D(dados[0][1] or 0)

                if quantidade > 0:
                    res[item_obj.id] = custo / quantidade
                else:
                    res[item_obj.id] = 0

                #  20/04 - solicitado para que, caso não haja custo calculado, colocar o custo informado
                if not res[item_obj.id]:
                    res[item_obj.id] = item_obj.produto_id.standard_price or 0

            #else:
                #res[item_obj.id] = 0

        return res

    def _get_custo_estoque(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #for id in ids:
            #res[id] = 0

        #return res

        for item_obj in self.browse(cr, uid, ids):

            vr_custo_estoque = D(0)

            vr_custo_estoque += D(item_obj.vr_unitario_custo_estoque) * D(item_obj.quantidade)

            res[item_obj.id] = vr_custo_estoque

        return res

    _columns = {
        'vr_unitario_custo_estoque': fields.function(_get_custo_unitario_estoque, type='float', string=u'Valor Unitário Estoque', digits=(21, 10), store=True),
        'vr_custo_estoque': fields.function(_get_custo_estoque, type='float', string=u'Valor Custo Estoque', digits=(18, 2), store=True),
    }

    def ajusta_custo(self, cr, uid, ids):
        res = super(sped_documentoitem, self).ajusta_custo(cr, uid, ids)

        produto_pool = self.pool.get('product.product')

        #
        # Atualiza os preços de custo, mínimo e de venda, seguindo
        # as regras internas da Patrimonial
        #
        for obj in self.browse(cr, uid, ids):
            produto_obj = obj.produto_id

            #
            # O preço de partida é o maior custo existente
            # entre todo o histórico de custo do produto
            #
            maior_custo = 0
            if produto_obj.custo_ids:
                for custo_obj in obj.custo_ids:
                    if custo_obj.vr_unitario > maior_custo:
                        maior_custo = custo_obj.vr_unitario

            #
            # Tabela específica da Patrimonial
            # Ponto de partida para o preço mínimo é
            # o maior custo;
            # sobre esse custo, aplica a margem adequada
            # entre 5% e 10%
            #
            preco_minimo = maior_custo
            if maior_custo <= 1000:
                preco_minimo *= 1.1
            elif maior_custo <= 2000:
                preco_minimo *= 1.09
            elif maior_custo <= 3000:
                preco_minimo *= 1.08
            elif maior_custo <= 4000:
                preco_minimo *= 1.07
            elif maior_custo <= 5000:
                preco_minimo *= 1.06
            else:
                preco_minimo *= 1.05

            #
            # Para o preço de venda, são adicionados
            #  3,00% - COFINS
            #  0,65% - PIS
            #  1,20% - IRF
            #  1,08% - CSLL
            #  0,79% - Adic. do imposto renda devido ao faturamento trimestral
            # ------
            #  6,72%
            preco_venda = preco_minimo / (1.00 - 0.0672)

            #
            # Acrescenta, ainda:
            # 10% margem de lucro
            #  6% de comissão
            #
            preco_venda *= 1.1
            preco_venda *= 1.06

            dados = {
                'standard_price': maior_custo,
                'list_price': preco_venda,
                'preco_minimo': preco_minimo,
            }

            produto_pool.write(cr, uid, [produto_obj.id], dados)

        return res

    #def ajusta_custo_unitario_estoque(self, cr, uid, ids, context={}):
        #item_pool = self.pool.get('sped.documentoitem')

        ##ids = item_pool.search(cr, uid, [('documento_id.data_emissao_brasilia', '<=', '2016-05-06')])
        #ids = item_pool.search(cr, uid, [(1, '=', 1)])

        #for item_id in ids:
            #valores = item_pool._get_custo_unitario_estoque(cr, uid, [item_id], '', None, context=context)
            #print(valores)
            #sql = """
            #update sped_documentoitem set
                #vr_unitario_custo_estoque = {vr_unitario_custo_estoque},
                #vr_custo_estoque = {vr_unitario_custo_estoque} * coalesce(quantidade, 0)
            #where
                #id = {id};
            #"""
            #vr_unitario_custo_estoque = valores[item_id]

            #dados = {
                #'id': item_id,
                #'vr_unitario_custo_estoque': vr_unitario_custo_estoque,
            #}

            #sql = sql.format(**dados)
            #cr.execute(sql)
            #cr.commit()
            #print(item_id)

        #nf_pool = self.pool.get('sped.documento')
        #ids = nf_pool.search(cr, uid, [(1, '=', 1)])

        #for nf_id in ids:
            #valores = nf_pool._get_soma_custo_estoque_funcao(cr, uid, [nf_id], 'vr_custo_estoque', None, context=context)
            #print(valores)

            #sql = """
            #update sped_documento set
                #vr_custo_estoque = {vr_custo_estoque}
            #where
                #id = {id};
            #"""
            #vr_custo_estoque = valores[nf_id]

            #dados = {
                #'id': nf_id,
                #'vr_custo_estoque': vr_custo_estoque,
            #}

            #sql = sql.format(**dados)
            #cr.execute(sql)
            #cr.commit()
            #print(nf_id)

        #move_pool = self.pool.get('stock.move')
        #ids = move_pool.search(cr, uid, [(1, '=', 1)])

        #for move_id in ids:
            #valores = move_pool._get_custo_unitario(cr, uid, [move_id], '', None, context)
            #print(valores)

            #sql = """
            #update stock_move set
                #vr_custo_unitario = {vr_custo_unitario}
            #where
                #id = {id};
            #"""
            #vr_custo_unitario = valores[move_id]

            #dados = {
                #'id': move_id,
                #'vr_custo_unitario': vr_custo_unitario,
            #}

            #sql = sql.format(**dados)
            #cr.execute(sql)
            #cr.commit()
            #print(move_id)




sped_documentoitem()
