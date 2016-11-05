# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D

DIAS_VENCIMENTO = [
    #[ '1', ' 1'],
    [ '2', ' 2'],
    #[ '3', ' 3'],
    #[ '4', ' 4'],
    [ '5', ' 5'],
    #[ '6', ' 6'],
    #[ '7', ' 7'],
    #[ '8', ' 8'],
    #[ '9', ' 9'],
    ['10', '10'],
    #['11', '11'],
    #['12', '12'],
    #['13', '13'],
    #['14', '14'],
    ['15', '15'],
    #['16', '16'],
    #['17', '17'],
    #['18', '18'],
    #['19', '19'],
    ['20', '20'],
    #['21', '21'],
    #['22', '22'],
    #['23', '23'],
    #['24', '24'],
    ['25', '25'],
    #['26', '26'],
    #['27', '27'],
    #['28', '28'],
    #['29', '29'],
    ['30', '30']
]


class finan_contrato_alteracao(orm.Model):
    _name = 'finan.contrato.alteracao'
    _inherit = 'finan.contrato.alteracao'

    _columns = {
        'dia_vencimento_anterior': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento anterior'),
        'dia_vencimento_novo': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento novo'),
    }

    def onchange_sale_order_id(self, cr, uid, ids, sale_order_id, contrato_id, valor_mensal_anterior, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not sale_order_id:
            return res

        valor_mensal_anterior = D(valor_mensal_anterior or 0)

        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        sale_order_obj.vr_mensal = D(sale_order_obj.vr_mensal or 0)

        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, contrato_id)

        #
        # Patrimonial Segurança
        #
        mensal_mon_eletronico = D(sale_order_obj.monitoramento_eletronico or 0)
        mensal_mon_eletronico += D(sale_order_obj.posto_movel or 0)
        mensal_mon_eletronico += D(sale_order_obj.ronda or 0)
        #mensal_mon_eletronico += D(sale_order_obj.manutencao_tecnica or 0)
        mensal_mon_eletronico += D(sale_order_obj.qtd_becape_chip or 0) * D(sale_order_obj.vr_becape_chip or 0)

        mensal_mon_imagens = D(sale_order_obj.monitoramento_imagens or 0)
        mensal_mon_garantido = D(sale_order_obj.qtd_monitoramento_garantido or 0) * D(sale_order_obj.vr_monitoramento_garantido or 0)
        mensal_vig_animal = D(sale_order_obj.animal_adestrado or 0)

        mensal_seguranca = mensal_mon_eletronico + mensal_mon_imagens + mensal_mon_garantido + mensal_vig_animal

        print(valor_mensal_anterior, 'vr_mensal_anterior')
        print(sale_order_obj.vr_mensal, 'vr_mensal_antigo')
        print(mensal_seguranca, 'vr_mensal_novo')
        if '82.891.805' in contrato_obj.company_id.partner_id.cnpj_cpf:
            if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                valor_mensal_novo = mensal_seguranca
            else:
                valor_mensal_novo = D(valor_mensal_anterior or 0) + mensal_seguranca

            produtos = []

            for produto_obj in contrato_obj.contrato_produto_ids:
                if produto_obj.data:
                    continue

                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': produto_obj.product_id.id,
                    'quantidade': produto_obj.quantidade,
                    'vr_unitario': produto_obj.vr_unitario,
                    'vr_total': produto_obj.vr_total,
                }

                if produto_obj.product_id.id == 3178:
                    if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                        dados_produto['vr_unitario'] = mensal_mon_eletronico
                        dados_produto['vr_total'] = mensal_mon_eletronico
                    else:
                        dados_produto['vr_unitario'] += mensal_mon_eletronico
                        dados_produto['vr_total'] += mensal_mon_eletronico

                    mensal_mon_eletronico = 0

                elif produto_obj.product_id.id == 3186:
                    if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                        dados_produto['vr_unitario'] = mensal_mon_imagens
                        dados_produto['vr_total'] = mensal_mon_imagens
                    else:
                        dados_produto['vr_unitario'] += mensal_mon_imagens
                        dados_produto['vr_total'] += mensal_mon_imagens

                    mensal_mon_imagens = 0

                elif produto_obj.product_id.id == 3179:
                    if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                        dados_produto['vr_unitario'] = mensal_mon_garantido
                        dados_produto['vr_total'] = mensal_mon_garantido
                    else:
                        dados_produto['vr_unitario'] += mensal_mon_garantido
                        dados_produto['vr_total'] += mensal_mon_garantido

                    mensal_mon_garantido = 0

                elif produto_obj.product_id.id == 3187:
                    if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                        dados_produto['vr_unitario'] = mensal_vig_animal
                        dados_produto['vr_total'] = mensal_vig_animal
                    else:
                        dados_produto['vr_unitario'] += mensal_vig_animal
                        dados_produto['vr_total'] += mensal_vig_animal

                    mensal_vig_animal = 0

                produtos.append([0, False, dados_produto])

            if mensal_mon_eletronico != 0:
                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': 3178,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_eletronico,
                    'vr_total': mensal_mon_eletronico,
                }
                produtos.append([0, False, dados_produto])

            if mensal_mon_imagens != 0:
                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': 3186,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_imagens,
                    'vr_total': mensal_mon_imagens,
                }
                produtos.append([0, False, dados_produto])

            if mensal_mon_garantido != 0:
                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': 3179,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_garantido,
                    'vr_total': mensal_mon_garantido,
                }
                produtos.append([0, False, dados_produto])

            if mensal_vig_animal != 0:
                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': 3187,
                    'quantidade': 1,
                    'vr_unitario': mensal_vig_animal,
                    'vr_total': mensal_vig_animal,
                }
                produtos.append([0, False, dados_produto])

            valores['contrato_produto_novo_ids'] = produtos

        #
        # Patrimonial Comércio
        #
        else:
            mensalidade = (sale_order_obj.vr_mensal or 0)
            mensalidade -= mensal_seguranca

            if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                valor_mensal_novo = mensalidade
            else:
                valor_mensal_novo = D(valor_mensal_anterior or 0) + mensalidade

            produtos = []

            for produto_obj in contrato_obj.contrato_produto_ids:
                if produto_obj.data:
                    continue

                dados_produto = {
                    'novo': 'S',
                    'contrato_id': contrato_obj.id,
                    'product_id': produto_obj.product_id.id,
                    'quantidade': produto_obj.quantidade,
                    'vr_unitario': produto_obj.vr_unitario,
                    'vr_total': produto_obj.vr_total,
                }

                if getattr(sale_order_obj, 'renegociacao', False) or getattr(sale_order_obj, 'eh_mudanca_endereco', False):
                    dados_produto['vr_unitario'] = mensalidade
                    dados_produto['vr_total'] = mensalidade
                else:
                    dados_produto['vr_unitario'] += mensalidade
                    dados_produto['vr_total'] += mensalidade

                produtos.append([0, False, dados_produto])

            valores['contrato_produto_novo_ids'] = produtos

        valores['valor_mensal_novo'] = valor_mensal_novo

        return res


finan_contrato_alteracao()
