# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.base import DicionarioBrasil


#STORE_TOTAL = {
    #'sale.order.line': (
        #lambda docitem_pool, cr, uid, ids, context={}:
            #[order_obj.orcamento_locacao_ids.id
             #for order_obj in docitem_pool.pool.get('sale.order').browse(cr, uid, [item_obj.order_id.id for item_obj in docitem_pool.browse(cr, uid, ids)])], [],
        #10  #  Prioridade
    #),
    #'sale.order': (
        #lambda docitem_pool, cr, uid, ids, context={}:
            #ol_obj.id  order_obj.orcamento_locacao_ids in
             #[order_obj for order_obj in docitem_pool.browse(cr, uid, ids)], [],
        #20  #  Prioridade
    #),
    #'orcamento.orcamento_locacao': (
        #lambda docitem_pool, cr, uid, ids, context={}: ids, [],
        #30  #  Prioridade
    #),
#}
STORE_TOTAL = True


class orcamento_locacao(osv.Model):
    _name = 'orcamento.orcamento_locacao'
    _description = u'Resumo do orçamento - Locação'
    _rec_name = 'orcamento_categoria_id'
    _order = 'sale_order_id, ordem'

    def _calcula_totais(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for ol_obj in self.browse(cr, uid, ids):
            valor = D(0)

            sql = """
                select
                    sum(coalesce(oi.{campo}, 0)) as vr_total
                from
                    sale_order_line oi
                    join orcamento_categoria c on c.id= oi.orcamento_categoria_id
                where
                    oi.order_id = {orc_id}
                    and oi.orcamento_categoria_id = {categoria_id}
            """

            if '_sem_autocalc' in nome_campo:
                sql += """
                    and (oi.autoinsert = False or oi.autoinsert is null)
                """

            nome_campo_real = nome_campo.replace('_sem_autocalc', '')

            sql = sql.format(campo=nome_campo_real, categoria_id=ol_obj.orcamento_categoria_id.id, orc_id=ol_obj.sale_order_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                valor = D(dados[0][0] or 0)

            if ol_obj.sale_order_id.orcamento_aprovado != 'venda' and nome_campo == 'vr_comissao':
                valor = D(0)

            res[ol_obj.id] = valor

        return res

    _columns = {
        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
        'sale_order_id': fields.many2one('sale.order', u'Orçamento', ondelete='cascade', select=True),
        'orcamento_categoria_id': fields.many2one('orcamento.categoria', u'Categoria do orçamento', ondelete='restrict', select=True),
        'ordem': fields.related('orcamento_categoria_id', 'ordem', type='integer', string=u'Ordem', store=True, select=True),
        'margem': fields.float('Margem (%)'),
        'desconto': fields.float('Desconto (%)'),
        'meses_retorno_investimento': fields.float('Meses retorno investimento'),
        'vr_mensal': fields.float('Valor mensal'),
        'vr_comissao': fields.float(u'Valor comissão venda'),
        'vr_comissao_locacao': fields.float(u'Valor comissão locação'),
        'considera_venda': fields.related('orcamento_categoria_id', 'considera_venda', type='boolean', string=u'Considera venda?', store=True),
        'vr_total_custo': fields.float('Valor total de custo'),
        'vr_total_minimo': fields.float('Total para locação'),
        'vr_total': fields.float('Valor'),
        'vr_total_margem_desconto': fields.float('Valor + Margem - Desconto'),
        'vr_total_venda_impostos': fields.float(u'Valor venda'),
        'vr_total_custo': fields.function(_calcula_totais, string=u'Valor total de custo', type='float', method=True, store=STORE_TOTAL),
        'vr_total_minimo': fields.function(_calcula_totais, string=u'Total para locação', type='float', method=True, store=STORE_TOTAL),
        'vr_total': fields.function(_calcula_totais, string=u'Total', type='float', method=True, store=STORE_TOTAL),
        'vr_total_margem_desconto': fields.function(_calcula_totais, string=u'Total + margem - desconto', type='float', method=True, store=STORE_TOTAL),
        'vr_total_venda_impostos': fields.function(_calcula_totais, string=u'Valor venda', type='float', method=True, store=STORE_TOTAL),
        'vr_comissao': fields.function(_calcula_totais, string=u'Valor comissão venda', type='float', method=True, store=STORE_TOTAL),

        'vr_total_custo_sem_autocalc': fields.function(_calcula_totais, string=u'Valor total de custo', type='float', method=True),
        'vr_total_minimo_sem_autocalc': fields.function(_calcula_totais, string=u'Total para locação', type='float', method=True),
        'vr_total_sem_autocalc': fields.function(_calcula_totais, string=u'Total', type='float', method=True),
        'vr_total_margem_desconto_sem_autocalc': fields.function(_calcula_totais, string=u'Total + margem - desconto', type='float', method=True),
        'vr_total_venda_impostos_sem_autocalc': fields.function(_calcula_totais, string=u'Valor venda', type='float', method=True),
    }

    def on_change_parametro(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, parametro, margem, desconto,  meses_retorno_investimento, context={}):
        item_pool = self.pool.get('sale.order.line')
        item_ids = item_pool.search(cr, uid, [('order_id', '=', sale_order_id), ('orcamento_categoria_id', '=', orcamento_categoria_id), ('autoinsert', '=', False)])

        if not item_ids:
            return {'vr_total_custo': 0, 'vr_total': 0, 'vr_total_margem_desconto': 0, 'vr_mensal': 0, 'vr_total_minimo': 0, 'vr_total_venda_impostos': 0}

        meses_retorno_investimento = D('%.4f' % (meses_retorno_investimento or 0))

        if parametro in ('M', 'D'):
            for item_id in item_ids:
                item_obj = item_pool.browse(cr, uid, item_id)

                parametros = {
                    'qty': item_obj.product_uom_qty,
                    'partner_id': item_obj.order_id.partner_id.id,
                    'vr_unitario_custo': item_obj.vr_unitario_custo,
                    'vr_unitario_minimo': item_obj.vr_unitario_minimo,
                    'vr_unitario_venda': item_obj.vr_unitario_venda,
                    'margem': item_obj.margem,
                    'desconto': item_obj.desconto,
                    'autoinsert': item_obj.autoinsert,
                    'usa_unitario_minimo': item_obj.usa_unitario_minimo,
                    'context': context,
                }

                if parametro == 'M':
                    parametros['margem'] = margem
                    calculo = item_obj.on_change_quantidade_margem_desconto(item_obj.order_id.pricelist_id.id, item_obj.product_id.id, **parametros)

                elif parametro == 'D':
                    parametros['desconto'] = desconto
                    calculo = item_obj.on_change_quantidade_margem_desconto(item_obj.order_id.pricelist_id.id, item_obj.product_id.id, **parametros)

                parametros['vr_unitario_venda_impostos'] = item_obj.vr_unitario_venda_impostos,
                valores = calculo['value']

                dados = {}
                for chave in valores:
                    if (not chave.startswith('default_')) and (not isinstance(valores[chave], DicionarioBrasil)):
                        dados[chave] = valores[chave]

                if parametro == 'M':
                    dados['margem'] = margem
                elif parametro == 'D':
                    dados['desconto'] = desconto

                item_pool.write(cr, uid, [item_id], dados, context={'calculo_resumo': True})
                #item_pool.write(cr, uid, [item_id], dados, context=context)

        resumo = item_pool.calcula_resumo_categoria_com_autocalc(cr, uid, sale_order_id)

        if orcamento_categoria_id in resumo:
            dados = resumo[orcamento_categoria_id]
            if meses_retorno_investimento > 0:
                dados['vr_mensal'] = D('%.2f' % dados['vr_total_margem_desconto']) / meses_retorno_investimento
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

    def on_change_margem(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, margem,  meses_retorno_investimento, context={}):
        dados = self.on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, 'M', margem, 0, meses_retorno_investimento, context=context)

        return {'value': dados}

    def on_change_desconto(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, desconto,  meses_retorno_investimento, context={}):
        dados = self.on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, 'D', 0, desconto, meses_retorno_investimento, context=context)

        return {'value': dados}

    def on_change_meses_retorno_investimento(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, meses_retorno_investimento, context={}):
        #if not meses_retorno_investimento:
            #raise osv.except_osv(u'Inválido!', u'Número inválido de meses para retorno do investimento!')

        dados = self.on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, 'MRI', 0, 0, meses_retorno_investimento, context=context)

        return {'value': dados}

    def on_change_valor_mensal(self, cr, uid, ids, sale_order_id, orcamento_categoria_id, vr_total_margem_desconto, vr_mensal, context={}):
        if vr_mensal > 0:
            meses_retorno_investimento = D(str(vr_total_margem_desconto)) / D(str(vr_mensal))
        else:
            meses_retorno_investimento = D(0)

        dados = self.on_change_parametro(cr, uid, ids, sale_order_id, orcamento_categoria_id, 'MRI', 0, 0, meses_retorno_investimento, context=context)
        dados['meses_retorno_investimento'] = meses_retorno_investimento

        return {'value': dados}

    #
    # Sempre, ao gravar, recalcular os totais para gravar nos campos
    # somente leitura
    #
    def create(self, cr, uid, vals, context={}):
        dados = self.on_change_parametro(cr, uid, [], vals['sale_order_id'], vals['orcamento_categoria_id'], 'MRI', 0, 0, vals['meses_retorno_investimento'])

        vals['vr_total_custo'] = dados['vr_total_custo']
        vals['vr_total_minimo'] = dados['vr_total_minimo']
        vals['vr_total'] = dados['vr_total']
        vals['vr_total_margem_desconto'] = dados['vr_total_margem_desconto']
        vals['vr_mensal'] = dados['vr_mensal']
        vals['vr_total_venda_impostos'] = dados['vr_total_venda_impostos']

        res = super(orcamento_locacao, self).create(
            cr, uid, vals, context=None)

        vals['id'] = res

        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = True

        for locacao_obj in self.pool.get('orcamento.orcamento_locacao').browse(cr, uid, ids):
            sale_order_id = vals.get('sale_order_id', locacao_obj.sale_order_id.id or False)
            orcamento_categoria_id = vals.get('orcamento_categoria_id', locacao_obj.orcamento_categoria_id.id or False)
            meses_retorno_investimento = vals.get('meses_retorno_investimento', locacao_obj.meses_retorno_investimento or 0)

            dados = self.on_change_parametro(cr, uid, [locacao_obj.id], sale_order_id, orcamento_categoria_id, '', 0, 0, meses_retorno_investimento)

            vals['vr_total_custo'] = dados['vr_total_custo']
            vals['vr_total_minimo'] = dados['vr_total_minimo']
            vals['vr_total'] = dados['vr_total']
            vals['vr_total_margem_desconto'] = dados['vr_total_margem_desconto']
            vals['vr_mensal'] = dados['vr_mensal']
            vals['vr_total_venda_impostos'] = dados['vr_total_venda_impostos']

            res = super(orcamento_locacao, self).write(
                cr, uid, [locacao_obj.id], vals, context=None)

            vals['id'] = locacao_obj.id

        #
        # Recalcula os totais do orçamento
        #
        if 'calcula_resumo' not in context:
            self.pool.get('sale.order.line').calcula_resumo_locacao(cr, uid, sale_order_id)
            #self.pool.get('sale.order.line').calcula_total_orcamento(cr, uid, sale_order_id)

        return res


orcamento_locacao()
