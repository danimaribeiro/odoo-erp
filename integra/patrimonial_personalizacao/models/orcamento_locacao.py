# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class orcamento_locacao(osv.Model):
    _name = 'orcamento.orcamento_locacao'
    _inherit = 'orcamento.orcamento_locacao'

    def on_change_parametro(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, parametro, margem, desconto,  meses_retorno_investimento, context={}):
        dados = super(orcamento_locacao, self).on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, parametro, margem, desconto, meses_retorno_investimento, context=context)

        item_pool = self.pool.get('sale.order.line')
        resumo = item_pool.calcula_resumo_categoria_com_autocalc(cr, uid, sale_order_id)

        if orcamento_categoria_id in resumo:
            dados = resumo[orcamento_categoria_id]
            if meses_retorno_investimento > 0:
                dados['vr_mensal'] = D('%.2f' % dados['vr_total_minimo']) / D(str(meses_retorno_investimento))
                dados['vr_mensal'] = dados['vr_mensal'].quantize(D('0.01'))
            else:
                dados['vr_mensal'] = 0

        else:
            dados = {
                'vr_total_minimo': 0,
                'vr_total_custo': 0,
                'vr_total': 0,
                'vr_total_margem_desconto': 0,
                'vr_mensal': 0,
                'vr_total_venda_impostos': 0,
            }

        return dados

    def on_change_valor_mensal(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, vr_total_margem_desconto, vr_mensal, context):
        if vr_mensal > 0:
            meses_retorno_investimento = D(str(vr_total_margem_desconto)) / D(str(vr_mensal))
        else:
            meses_retorno_investimento = D(0)

        dados = {'meses_retorno_investimento': meses_retorno_investimento}
        avisos = {}
        if meses_retorno_investimento > 0:
            user_pool = self.pool.get('res.users')
            item_comissao_pool = self.pool.get('orcamento.comissao_item')
            usuario_obj = user_pool.browse(cr, 1, uid)
            nivel_usuario = usuario_obj.nivel_aprovacao_comercial or 0

            comissao_pool = self.pool.get('orcamento.categoria')
            categoria_obj = comissao_pool.browse(cr, uid, orcamento_categoria_id)
            comissao_obj = categoria_obj.comissao_locacao_id

            item_comissao_ids = item_comissao_pool.search(cr, uid, [('comissao_id', '=', comissao_obj.id), ('meses_retorno_investimento', '>=', meses_retorno_investimento)], order='meses_retorno_investimento')

            if not len(item_comissao_ids):
                dados = {
                    'meses_retorno_investimento': 1,
                    'vr_mensal': vr_total_margem_desconto
                }
                avisos = {
                    'title':u'Erro',
                    'message': u'A categoria %s tem um número de meses para retorno do investimento inválido!' % categoria_obj.nome
                }

            item_comissao_obj = item_comissao_pool.browse(cr, 1, item_comissao_ids[0])

            if item_comissao_obj.grupo_aprovacao_id and item_comissao_obj.grupo_aprovacao_id.nivel:
                #
                # Se o nível do usuário for menor do que o necessário
                #
                if item_comissao_obj.grupo_aprovacao_id.nivel > nivel_usuario:
                    dados = {
                        'meses_retorno_investimento': 1,
                        'vr_mensal': vr_total_margem_desconto
                    }
                    avisos = {
                        'title':u'Erro',
                        'message': u'Você não tem permissão de realizer essa operação com a categoria %s!' % categoria_obj.nome
                    }

        #dados = self.on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, 'MRI', 0, 0, meses_retorno_investimento)

        return {'value': dados, 'warning': avisos}

    def write(self, cr, uid, ids, vals, context={}):
        res = super(orcamento_locacao, self).write(cr, uid, ids, vals, context)

        if not 'ajusta_locacao_patrimonial' in context and not 'calcula_resumo' in context:
            orcamentos_ajustar = []
            for id in ids:
                locacao_obj = self.pool.get('orcamento.orcamento_locacao').browse(cr, uid, id)
                if locacao_obj.sale_order_id.id not in orcamentos_ajustar:
                    orcamentos_ajustar.append(locacao_obj.sale_order_id.id)
                res = super(orcamento_locacao, self).write(cr, uid, [id], vals, context={'ajusta_locacao_patrimonial': True, 'calcula_resumo': True})

            self.pool.get('sale.order').ajusta_itens_locacao_patrimonial(cr, uid, orcamentos_ajustar)

        return res


orcamento_locacao()
