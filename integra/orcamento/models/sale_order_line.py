# -*- encoding: utf-8 -*-


from datetime import datetime
from decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID
from tools.translate import _
from copy import copy
from pybrasil.base import DicionarioBrasil


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    def _comissao(self, cr, uid, ids, nome_campo, arg=None, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            if nome_campo == 'comissao':
                if item_obj.vr_total_margem_desconto:
                    res[item_obj.id] = item_obj.vr_comissao / item_obj.vr_total_margem_desconto * 100.00
                else:
                    res[item_obj.id] = 0

            elif nome_campo == 'comissao_locacao':
                if item_obj.vr_total_margem_desconto:
                    res[item_obj.id] = item_obj.vr_comissao_locacao / item_obj.vr_total_margem_desconto * 100.00
                else:
                    res[item_obj.id] = 0

        return res

    _columns = {
        #
        # Redefinição do product_id para forçar a execução do evento _
        #
        'product_id': fields.many2one('product.product', u'Product', domain=[('sale_ok', '=', True)], change_default=True),

        'name': fields.char('Description', size=256, required=False, select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'orcamento_categoria_id': fields.many2one('orcamento.categoria', u'Categoria do orçamento', ondelete='restrict'),
        'vr_unitario_custo': fields.float(u'Unitário de custo', digits=(18, 4)),
        'vr_total_custo': fields.float(u'Valor de custo', digits=(18,2)),
        'vr_unitario_minimo': fields.float(u'Unitário mínimo', digits=(21, 10)),
        'vr_total_minimo': fields.float(u'Valor mínimo', digits=(18,2)),
        'vr_unitario_venda': fields.float(u'Unitário venda/sugerido', digits=(21, 10)),
        'usa_unitario_minimo': fields.boolean(u'Usa preço mínimo?'),
        'vr_total': fields.float(u'Valor', digits=(18,2)),
        'margem': fields.float(u'Margem (%)'),
        'desconto': fields.float(u'Desconto (%)'),
        'vr_unitario_margem_desconto': fields.float(u'Unitário margem/desconto', digits=(21, 10)),
        'vr_total_margem_desconto': fields.float(u'Valor total com margem e desconto', digits=(18,2)),
        'order_line_id': fields.many2one('sale.order.line', u'Item pai', ondelete='cascade'),
        'order_line_ids': fields.one2many('sale.order.line', 'order_line_id', u'Itens relacionados'),
        'autoinsert': fields.boolean(u'Autoinsere em todo orçamento'),
        'comissao': fields.function(_comissao, string=u'% comissão', method=True, type='float', store=False),
        'comissao_locacao': fields.function(_comissao, string=u'% comissão locação', method=True, type='float', store=False),
        'vr_comissao': fields.float(u'Valor comissão', digits=(18,2)),
        'vr_comissao_locacao': fields.float(u'Valor comissão locação', digits=(18,2)),
        'comissao_venda_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para venda'),
        'comissao_locacao_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para locação'),
        'vr_unitario_venda_impostos': fields.float(u'Unitário venda'),
        'vr_total_venda_impostos': fields.float(u'Valor venda', digits=(18,2)),
    }

    _defaults = {
        'usa_unitario_minimo': False,
        'type': 'make_to_order',
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        resposta = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context=context)

        if not product_id:
            return resposta

        if 'price_unit' in context:
            return resposta

        #
        # Antes de alterar o produto, deletamos os itens relacionados ao produto anterior, se houver
        #
        item_pool = self.pool.get('sale.order.line')
        for item_id in ids:
            item_obj = item_pool.browse(cr, uid, item_id)
            if item_obj.order_line_ids:
                for item_relacionado in item_obj.order_line_ids:
                    item_relacionado.unlink()

        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)

        resposta['value'].update(
            {
                'name': product_obj.name,
                #'orcamento_categoria_id': product_obj.orcamento_categoria_id.id,
                #'vr_unitario_custo': product_obj.standard_price,
                #'vr_unitario_minimo': product_obj.preco_minimo or product_obj.list_price,
                #'vr_unitario_venda': product_obj.list_price,
                #'usa_unitario_minimo': False,
                'autoinsert': product_obj.autoinsert,
                'type': product_obj.procure_method,
                #'price_unit': product_obj.list_price,
                #'vr_unitario_venda_impostos': product_obj.list_price,
            }
        )

        orcamento_categoria_id = context.get('default_orcamento_categoria_id', False)
        if (not orcamento_categoria_id) and product_obj.orcamento_categoria_id:
            orcamento_categoria_id = product_obj.orcamento_categoria_id.id

        margem = 0
        if orcamento_categoria_id:
            resposta['value']['orcamento_categoria_id'] = orcamento_categoria_id

            categoria_obj = self.pool.get('orcamento.categoria').browse(cr, uid, orcamento_categoria_id)
            margem = categoria_obj.margem

            if categoria_obj.comissao_venda_id:
                resposta['value']['comissao_venda_id'] = categoria_obj.comissao_venda_id.id
            if categoria_obj.comissao_locacao_id:
                resposta['value']['comissao_locacao_id'] = categoria_obj.comissao_locacao_id.id

        if product_obj.autoinsert:
            resposta['value'].update(
                {
                    'product_uom_qty': 1,
                    'vr_unitario_custo': 0,
                    'vr_unitario_minimo': 0,
                    'vr_unitario_venda': 0,
                    'price_unit': 0,
                    'vr_unitario_venda_impostos': 0,
                }
            )
        else:
            resposta['value'].update(
                {
                    'margem': margem
                }
            )

        if partner_id:
            partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

            if partner_obj.comissao_venda_id:
                resposta['value']['comissao_venda_id'] = partner_obj.comissao_venda_id.id
            if partner_obj.comissao_locacao_id:
                resposta['value']['comissao_locacao_id'] = partner_obj.comissao_locacao_id.id

        return resposta

    def on_change_quantidade_margem_desconto(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=0, vr_unitario_minimo=0, vr_unitario_venda=0, margem=0, desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context={}, desconto_direto=False, margem_direta=False):
        if autoinsert:
            return {}

        resposta = {'value': {}}
        valores = resposta['value']

        quantidade = D(qty or 0)
        vr_unitario_custo = D(vr_unitario_custo or 0).quantize(D('0.01'))
        vr_total_custo = quantidade * vr_unitario_custo
        vr_total_custo = vr_total_custo.quantize(D('0.01'))

        vr_unitario_minimo = D(vr_unitario_minimo).quantize(D('0.01'))
        vr_total_minimo = quantidade * vr_unitario_minimo
        vr_total_minimo = vr_total_minimo.quantize(D('0.01'))

        #vr_unitario_venda = resposta['value']['price_unit']

        #vr_unitario_venda = D(vr_unitario_venda or 0).quantize(D('0.01'))
        vr_unitario_venda = D(vr_unitario_venda or 0)

        print('vr_unitario_custo', vr_unitario_custo)

        if usa_unitario_minimo:
            vr_total = quantidade * vr_unitario_minimo
            #vr_total = vr_total.quantize(D('0.01'))
            vr_total_margem_desconto = vr_total
            margem = 0
            desconto = 0

        else:
            vr_total = quantidade * vr_unitario_venda
            #vr_total = vr_total.quantize(D('0.01'))

        margem = D(margem or 0).quantize(D('0.01'))
        desconto = D(desconto or 0).quantize(D('0.01'))

        if not (margem_direta or context.get('margem_direta', False)):
            margem = vr_total * (margem / D('100.00'))
            #margem = margem.quantize(D('0.01'))

        vr_total_margem_desconto = vr_total + margem

        if not(desconto_direto or context.get('margem_direta', False)):
            desconto = vr_total_margem_desconto * (desconto / D('100.00'))
            #desconto = desconto.quantize(D('0.01'))

        #
        # Ajusta o desconto para embutir os impostos
        #
        if ids and desconto:
            if isinstance(ids, (list, tuple)):
                item_id = ids[0]
            else:
                item_id = ids

            item_obj = self.pool.get('sale.order.line').browse(cr, uid, item_id)
            if D(item_obj.vr_total_venda_impostos):
                proporcao_impostos = D(item_obj.vr_total_margem_desconto) / D(item_obj.vr_total_venda_impostos)
            else:
                proporcao_impostos = D(1)

            desconto = D(desconto) * proporcao_impostos
            #desconto = desconto.quantize(D('0.01'))

        vr_total_margem_desconto -= desconto
        #vr_total_margem_desconto = vr_total_margem_desconto.quantize(D('0.01'))

        if product_id:
            produto_obj = self.pool.get('product.product').browse(cr, 1, product_id)
            #if vr_total_margem_desconto < vr_total_minimo:
                #raise osv.except_osv(u'Problema!', u'O produto “{produto}” não pode ser vendido por um preço menor do que o mínimo!'.format(produto=produto_obj.name_template))

        vr_unitario_margem_desconto = vr_total_margem_desconto / quantidade

        if vr_unitario_venda:
            nova_margem = D(vr_unitario_margem_desconto) / D(vr_unitario_venda) * 100
        else:
            nova_margem = D(0)

        nova_margem = nova_margem.quantize(D('0.01'))

        contexto_novo = copy(context)
        contexto_novo['price_unit'] = vr_unitario_margem_desconto

        impostos = self.pool.get('sale.order.line').product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, contexto_novo)

        #valores = impostos['value']
        #valores['vr_unitario_custo'] = vr_unitario_custo
        #valores['vr_total_custo'] = vr_total_custo

        #valores['vr_unitario_margem_desconto'] = vr_unitario_margem_desconto
        #valores['vr_total_margem_desconto'] = vr_total_margem_desconto
        #valores['price_unit'] = vr_unitario_margem_desconto

        if product_id:
            print('valores calculados', produto_obj.name_template, valores)

        #return impostos
        return {}

    #
    # Sempre, ao gravar, recalcular os totais para gravar nos campos
    # somente leitura
    #
    def create(self, cr, uid, dados, context={}):
        if context is None:
            context = {}

        copia = '__copy_data_seen' in context

        #if copia and 'order_line_id' in dados and dados['order_line_id']:
            #return False

        ##
        ## Só faz os cálculos se não estiver copiando o item
        ##
        #if not copia:
            ##
            ## Busca o produto
            ##
            #if dados.get('product_id', False):
                #product_obj = self.pool.get('product.product').browse(cr, uid, dados['product_id'])

                #if dados.get('orcamento_categoria_id', False):
                    #categoria_obj = self.pool.get('orcamento.categoria').browse(cr, uid, dados['orcamento_categoria_id'])
                    #if not dados.get('margem', False):
                        #dados['margem'] = categoria_obj.margem

                #if not dados.get('autoinsert', False):
                    #dados['autoinsert'] = product_obj.autoinsert

                ##
                ## Replica os preços do produto, pois são campos readonly na tela, o valor não vai vir
                ## aqui pra ser salvo no banco de dados
                ##
                #if not 'vr_unitario_custo' in dados:
                    #dados['vr_unitario_custo'] = product_obj.standard_price or 1

                #if not 'vr_unitario_minimo' in dados:
                    #dados['vr_unitario_minimo'] = product_obj.preco_minimo or product_obj.list_price

                #if not 'vr_unitario_venda' in dados:
                    #dados['vr_unitario_venda'] = product_obj.list_price or 1

                #calculo = self.on_change_quantidade_margem_desconto(cr, uid, [], None, None, qty=dados['product_uom_qty'], vr_unitario_custo=dados['vr_unitario_custo'], vr_unitario_minimo=dados['vr_unitario_minimo'], vr_unitario_venda=dados['vr_unitario_venda'], margem=dados['margem'], desconto=dados['discount'], autoinsert=dados['autoinsert'], mudou_quantidade=False, usa_unitario_minimo=dados['usa_unitario_minimo'], context=context)

                #if calculo:
                    #dados['vr_total_custo'] = calculo['value']['vr_total_custo']
                    #dados['vr_unitario_venda'] = calculo['value']['vr_unitario_venda']
                    #dados['vr_total'] = calculo['value']['vr_total']
                    ##dados['price_unit'] = calculo['value']['price_unit']
                    #dados['vr_total_margem_desconto'] = calculo['value']['vr_total_margem_desconto']
                    #dados['vr_total_minimo'] = calculo['value']['vr_total_minimo']
                    #dados['vr_unitario_margem_desconto'] = calculo['value']['vr_unitario_margem_desconto']
                    #dados['vr_unitario_venda_impostos'] = calculo['value']['vr_unitario_venda_impostos']

        res = super(sale_order_line, self).create(
            cr, uid, dados, context=None)

        self.pool.get('sale.order.line').after_insert_update(cr, uid, res, copia, context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        #print('ids a alterar 1', ids, 'dados recebidos', dados)
        res = False
        calculo_resumo = 'calculo_resumo' in context
        for item_obj in self.pool.get('sale.order.line').browse(cr, uid, ids):
            try:
                ##if (not calculo_resumo) and ('state' not in dados):
                    ##quantidade = dados.get('product_uom_qty', item_obj.product_uom_qty or 1)
                    ##vr_unitario_custo = dados.get('vr_unitario_custo', item_obj.vr_unitario_custo or 0)
                    ##vr_unitario_minimo = dados.get('vr_unitario_minimo', item_obj.vr_unitario_minimo or 0)
                    ##vr_unitario_venda = dados.get('vr_unitario_venda', item_obj.vr_unitario_venda or 0)
                    ##usa_unitario_minimo = dados.get('usa_unitario_minimo', item_obj.usa_unitario_minimo or False)
                    ##margem = dados.get('margem', item_obj.margem or 0)
                    ##desconto = dados.get('discount', item_obj.discount or 0)
                    ##autoinsert = dados.get('autoinsert', item_obj.autoinsert or False)

                    ##calculo = self.on_change_quantidade_margem_desconto(cr, uid, [item_obj.id], None, None, qty=quantidade, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=desconto, autoinsert=autoinsert, mudou_quantidade=False, usa_unitario_minimo=usa_unitario_minimo, context=context)

                    ##if calculo:
                        ##dados['vr_total_custo'] = calculo['value']['vr_total_custo']
                        ##dados['vr_unitario_venda'] = calculo['value']['vr_unitario_venda']
                        ##dados['vr_total'] = calculo['value']['vr_total']
                        ###dados['price_unit'] = calculo['value']['price_unit']
                        ##dados['vr_total_margem_desconto'] = calculo['value']['vr_total_margem_desconto']
                        ##dados['vr_total_minimo'] = calculo['value']['vr_total_minimo']
                        ##dados['vr_unitario_margem_desconto'] = calculo['value']['vr_unitario_margem_desconto']
                        ##dados['vr_unitario_venda_impostos'] = calculo['value']['vr_unitario_venda_impostos']
                        ##dados['vem_daqui'] = 'calculou_resumo'

                #if item_obj.product_id:
                    #print('id a ser alterado 2, resumo ', item_obj.id, item_obj.product_id.name_template, 'dados a alterar', dados)
                #else:
                    #print('id a ser alterado 3 resumo ', item_obj.id, 'dados a alterar', dados)
                res = super(sale_order_line, self).write(cr, uid, [item_obj.id], dados, context=context)

            except Exception as inst:
                #print(type(inst))
                #raise inst
                res = False

        if not calculo_resumo:
            for id in ids:
                self.pool.get('sale.order.line').after_insert_update(cr, uid, id, context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        if ids:
            item_obj = self.pool.get('sale.order.line').browse(cr, uid, ids[0])
            sale_order_id = item_obj.order_id.id

        res = super(sale_order_line, self).unlink(cr, uid, ids, context=context)

        calculo_resumo = 'calculo_resumo' in context

        if ids and not calculo_resumo:
            self.pool.get('sale.order.line').calcula_produtos_autocalc(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_resumo_locacao(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_total_orcamento(cr, uid, sale_order_id)

        return res

    def after_insert_update(self, cr, uid, item_id=None, copia=False, sale_order_id=None, context={}):
        if not item_id:
            return

        item_obj = self.pool.get('sale.order.line').browse(cr, uid, item_id)

        if not item_obj or not hasattr(item_obj, 'order_id'):
            return

        sale_order_id = item_obj.order_id.id

        #
        # usamos self.pool.get('sale.order.line'). para considerar
        # customizações de outros módulos
        #
        if not copia:
            #
            # Só ajusta os itens relacionados quando em edição, na confirmação
            # isso causa erro
            #
            if item_obj.state == 'draft':
                self.pool.get('sale.order.line').ajusta_produtos_relacionados(cr, uid, item_obj, context)
            self.pool.get('sale.order.line').calcula_produtos_autocalc(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_resumo_locacao(cr, uid, sale_order_id)
            self.pool.get('sale.order.line').calcula_total_orcamento(cr, uid, sale_order_id)

    def calcula_produtos_autocalc(self, cr, uid, sale_order_id):
        #
        # Buscamos os itens que serão autocalculados
        #
        item_pool = self.pool.get('sale.order.line')
        item_ids = item_pool.search(cr, uid, [('order_id', '=', sale_order_id), ('autoinsert', '=', True)])
        item_objs = item_pool.browse(cr, uid, item_ids)
        resumo = self.calcula_resumo_categoria_sem_autocalc(cr, uid, sale_order_id)

        for item_obj in item_objs:
            vr_total_custo = 0
            vr_total_minimo = 0
            vr_total = 0
            vr_total_margem_desconto = 0
            vr_total_venda_impostos = 0

            #
            # Buscamos as categorias para o autocálculo
            #
            for autocalc_obj in item_obj.product_id.autocalc_orcamento_categoria_ids:
                if autocalc_obj.orcamento_categoria_id.id in resumo:
                    #
                    # Valor total de custo
                    #
                    vr_total_categoria = resumo[autocalc_obj.orcamento_categoria_id.id]['vr_total_custo']
                    vr_total_categoria = D('%.2f' % vr_total_categoria)
                    perc_categoria = D('%.4f' % (autocalc_obj.percentual or 0)) / D('100.00')
                    vr_total_categoria *= perc_categoria
                    vr_total_categoria = vr_total_categoria.quantize(D('0.01'))
                    vr_total_custo += vr_total_categoria

                    #
                    # Valor total de mínimo
                    #
                    vr_total_categoria = resumo[autocalc_obj.orcamento_categoria_id.id]['vr_total_minimo']
                    vr_total_categoria = D('%.2f' % vr_total_categoria)
                    perc_categoria = D('%.4f' % (autocalc_obj.percentual or 0)) / D('100.00')
                    vr_total_categoria *= perc_categoria
                    vr_total_categoria = vr_total_categoria.quantize(D('0.01'))
                    vr_total_minimo += vr_total_categoria

                    #
                    # Valor total
                    #
                    vr_total_categoria = resumo[autocalc_obj.orcamento_categoria_id.id]['vr_total']
                    vr_total_categoria = D('%.2f' % vr_total_categoria)
                    perc_categoria = D('%.4f' % (autocalc_obj.percentual or 0)) / D('100.00')
                    vr_total_categoria *= perc_categoria
                    vr_total_categoria = vr_total_categoria.quantize(D('0.01'))
                    vr_total += vr_total_categoria

                    #
                    # Valor total com margem e desconto
                    #
                    vr_total_categoria = resumo[autocalc_obj.orcamento_categoria_id.id]['vr_total_margem_desconto']
                    vr_total_categoria = D('%.2f' % vr_total_categoria)
                    perc_categoria = D('%.4f' % (autocalc_obj.percentual or 0)) / D('100.00')
                    vr_total_categoria *= perc_categoria
                    vr_total_categoria = vr_total_categoria.quantize(D('0.01'))
                    vr_total_margem_desconto += vr_total_categoria

                    #
                    # Valor total venda com impostos
                    #
                    vr_total_categoria = resumo[autocalc_obj.orcamento_categoria_id.id]['vr_total_venda_impostos']
                    vr_total_categoria = D('%.2f' % vr_total_categoria)
                    perc_categoria = D('%.4f' % (autocalc_obj.percentual or 0)) / D('100.00')
                    vr_total_categoria *= perc_categoria
                    vr_total_categoria = vr_total_categoria.quantize(D('0.01'))
                    vr_total_venda_impostos += vr_total_categoria
            #
            # Gravamos o cálculo no registro
            #
            cr.execute('''
                begin;
                update sale_order_line oi set
                    vr_total_custo = %.2f,
                    vr_total_minimo = %.2f,
                    vr_total = %.2f,
                    vr_total_margem_desconto = %.2f,
                    vr_total_venda_impostos = %.2f
                where oi.id = %d;
                commit work;''' % (vr_total_custo, vr_total_minimo, vr_total, vr_total_margem_desconto, vr_total_venda_impostos, item_obj.id))

    def calcula_resumo_categoria_sem_autocalc(self, cr, uid, sale_order_id):
        cr.execute('''
            select
                oi.orcamento_categoria_id,
                sum(coalesce(oi.vr_total_custo, 0)) as vr_total_custo,
                sum(coalesce(oi.vr_total_minimo, 0)) as vr_total_minimo,
                sum(coalesce(oi.vr_total, 0)) as vr_total,
                sum(coalesce(oi.vr_total_margem_desconto, 0)) as vr_total_margem_desconto,
                sum(coalesce(oi.vr_total_venda_impostos, 0)) as vr_total_venda_impostos
            from
                sale_order_line oi
            where
                oi.order_id = %d
                and oi.autoinsert = False
            group by
                oi.orcamento_categoria_id
            ''' % sale_order_id)

        resumo = {}
        for orcamento_categoria_id, vr_total_custo, vr_total_minimo, vr_total, vr_total_margem_desconto, vr_total_venda_impostos in cr.fetchall():
            resumo[orcamento_categoria_id] = {'vr_total_margem_desconto': vr_total_margem_desconto, 'vr_total': vr_total, 'vr_total_custo': vr_total_custo, 'vr_total_minimo': vr_total_minimo, 'vr_total_venda_impostos': vr_total_venda_impostos}

        return resumo

    def calcula_resumo_categoria_com_autocalc(self, cr, uid, sale_order_id):
        cr.execute('''
            select
                oi.orcamento_categoria_id,
                sum(coalesce(oi.vr_total_custo, 0)) as vr_total_custo,
                sum(coalesce(oi.vr_total_minimo, 0)) as vr_total_minimo,
                sum(coalesce(oi.vr_total,0)) as vr_total,
                sum(coalesce(oi.vr_total_margem_desconto,0)) as vr_total_margem_desconto,
                sum(coalesce(oi.vr_comissao,0)) as vr_comissao,
                sum(coalesce(oi.vr_total_venda_impostos,0)) as vr_total_venda_impostos
            from
                sale_order_line oi
            where
                oi.order_id = %d
            group by
                oi.orcamento_categoria_id
            ''' % sale_order_id)

        resumo = {}
        zeros = {'vr_total_custo': 0, 'vr_total': 0, 'vr_total_margem_desconto': 0, 'vr_comissao': 0, 'vr_total_minimo': 0, 'vr_total_venda_impostos': 0}

        for orcamento_categoria_id, vr_total_custo, vr_total_minimo, vr_total, vr_total_margem_desconto, vr_comissao, vr_total_venda_impostos in cr.fetchall():
            resumo[orcamento_categoria_id] = {'vr_total_custo': vr_total_custo, 'vr_total': vr_total, 'vr_total_margem_desconto': vr_total_margem_desconto, 'vr_comissao': vr_comissao, 'vr_total_minimo': vr_total_minimo, 'vr_total_venda_impostos': vr_total_venda_impostos}

        sale_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        for resumo_obj in sale_obj.orcamento_resumo_ids:
            if resumo_obj.orcamento_categoria_id.id not in resumo:
                resumo[resumo_obj.orcamento_categoria_id.id] = zeros

        return resumo

    def calcula_comissao_itens(self, cr, uid, sale_order_id):
        #
        # Primeiro, recalculamos os itens e as comissões
        #
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        for item_obj in sale_order_obj.order_line:
            bc_comissao = item_obj.vr_total_margem_desconto

            if item_obj.orcamento_categoria_id.abate_impostos_comissao:
                bc_comissao -= item_obj.vr_total_margem_desconto * (item_obj.orcamento_categoria_id.abate_impostos_comissao / 100.00)

            if item_obj.orcamento_categoria_id.abate_custo_comissao:
                bc_comissao -= item_obj.vr_total_custo

            margem_real = item_obj.vr_total_margem_desconto / item_obj.vr_total_custo
            #if item_obj.desconto:
            #    margem_real = item_obj.margem * (1 - (item_obj.desconto / 100))
            #elif item_obj.margem:
            #    margem_real = item_obj.margem

            vr_comissao = 0

            if item_obj.orcamento_categoria_id.considera_venda and sale_order_obj.orcamento_aprovado == 'venda':
                if item_obj.comissao_venda_id:
                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.comissao_venda_id.id), ('margem', '>=', margem_real)], order='margem')

                    if item_comissao_ids:
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])

                        if item_obj.usa_unitario_minimo:
                            vr_comissao = bc_comissao * (item_comissao_obj.comissao_preco_minimo / 100.00)
                        else:
                            vr_comissao = bc_comissao * (item_comissao_obj.comissao / 100.00)

                        item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

            else:
                if item_obj.orcamento_categoria_id.considera_venda:
                    item_obj.write({'vr_comissao': 0}, context={'calculo_resumo': True})

                elif item_obj.comissao_locacao_id:
                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', item_obj.comissao_locacao_id.id), ('meses_retorno_investimento', '>=', 1)], order='meses_retorno_investimento')

                    if item_comissao_ids:
                        item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])
                        vr_comissao = bc_comissao * (item_comissao_obj.comissao / 100.00)
                        item_obj.write({'vr_comissao': vr_comissao}, context={'calculo_resumo': True})

    def calcula_resumo_locacao(self, cr, uid, sale_order_id):
        self.calcula_comissao_itens(cr, uid, sale_order_id)
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        #
        # Agora, faz o resumo por categoria para a locação
        #
        #sale_order_obj.cria_resumo_locacao(cr, uid, sale_order_id)
        resumo = self.calcula_resumo_categoria_com_autocalc(cr, uid, sale_order_id)

        #
        # Primeiro, atualizamos os totais de cada categoria de orçamento na tabela de
        # locação/resumo
        #
        for categoria_id in resumo:
            total = resumo[categoria_id]
            vr_total_custo = total['vr_total_custo']
            if vr_total_custo is None:
                vr_total_custo = 0
            vr_total_minimo = total['vr_total_minimo']
            if vr_total_minimo is None:
                vr_total_minimo = 0
            vr_total = total['vr_total']
            if vr_total is None:
                vr_total = 0
            vr_total_margem_desconto = total['vr_total_margem_desconto']
            if vr_total_margem_desconto is None:
                vr_total_margem_desconto = 0
            vr_comissao = total['vr_comissao']
            if vr_comissao is None:
                vr_comissao = 0
            vr_total_venda_impostos = total['vr_total_venda_impostos']
            if vr_total_venda_impostos is None:
                vr_total_venda_impostos = 0

            resumo_id = self.pool.get('orcamento.orcamento_locacao').search(cr, uid, [('sale_order_id', '=', sale_order_id), ('orcamento_categoria_id', '=', categoria_id)])

            if resumo_id:
                resumo_obj = self.pool.get('orcamento.orcamento_locacao').browse(cr, uid, resumo_id[0])

                comissao_locacao_obj = False
                if sale_order_obj.partner_id.comissao_locacao_id:
                    comissao_locacao_obj = sale_order_obj.partner_id.comissao_locacao_id

                elif resumo_obj.orcamento_categoria_id.comissao_locacao_id:
                    comissao_locacao_obj = resumo_obj.orcamento_categoria_id.comissao_locacao_id

                vr_comissao_locacao = 0
                if comissao_locacao_obj:
                    bc_comissao = resumo_obj.vr_mensal

                    item_comissao_ids = self.pool.get('orcamento.comissao_item').search(cr, uid, [('comissao_id', '=', comissao_locacao_obj.id), ('meses_retorno_investimento', '>=', resumo_obj.meses_retorno_investimento)], order='meses_retorno_investimento')

                    if not item_comissao_ids:
                        raise osv.except_osv(u'Inválido !', u'A categoria %s tem um número inválido de meses para retorno do investimento!' % resumo_obj.orcamento_categoria_id.nome)

                    item_comissao_obj = self.pool.get('orcamento.comissao_item').browse(cr, uid, item_comissao_ids[0])
                    vr_comissao_locacao = bc_comissao * (item_comissao_obj.comissao / 100.00)

                if not resumo_obj.orcamento_categoria_id.considera_venda:
                    vr_total_custo = 0
                    vr_total = 0
                    vr_total_margem_desconto = 0
                    vr_total_minimo = 0
                    vr_comissao = 0
                    vr_total_venda_impostos = 0

                resumo_obj.write({'vr_total_custo': vr_total_custo, 'vr_total': vr_total, 'vr_total_margem_desconto': vr_total_margem_desconto, 'vr_comissao': vr_comissao, 'vr_comissao_locacao': vr_comissao_locacao, 'vr_total_minimo': vr_total_minimo, 'vr_total_venda_impostos': vr_total_venda_impostos}, context={'calcula_resumo': True})

    def calcula_total_orcamento(self, cr, uid, sale_order_id):
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        self.pool.get('sale.order').cria_resumo_locacao(cr, uid, sale_order_id)
        #
        # Reunimos os totais de todas as categorias
        #
        cr.execute('''
            select
              sum(coalesce(case when oc.considera_venda then ol.vr_total_custo else 0 end, 0)) as vr_total_custo,
              sum(coalesce(case when oc.considera_venda then ol.vr_total_minimo else 0 end, 0)) as vr_total_minimo,
              sum(coalesce(case when oc.considera_venda then ol.vr_total else 0 end, 0)) as vr_total,
              sum(coalesce(case when oc.considera_venda then ol.vr_total_margem_desconto else 0 end, 0)) as vr_total_margem_desconto,
              sum(coalesce(ol.vr_mensal, 0)) as vr_mensal,
              sum(coalesce(ol.vr_comissao, 0)) as vr_comissao,
              sum(coalesce(ol.vr_comissao_locacao, 0)) as vr_comissao_locacao,
              max(coalesce(ol.meses_retorno_investimento, 0)) as meses_retorno_investimento,
              sum(coalesce(case when oc.considera_venda then ol.vr_total_venda_impostos else 0 end, 0)) as vr_total_venda_impostos

            from
              orcamento_orcamento_locacao ol
              join orcamento_categoria oc on oc.id = ol.orcamento_categoria_id

            where
              ol.sale_order_id = %d;''' % sale_order_id)

        totais = cr.fetchall()[0]
        totais += (sale_order_id,)

        #
        # Atualizamos o registro mestre, para termos o valor mensal final
        #
        cr.execute('''
            begin;
            update sale_order set
              vr_total_custo = %.2f,
              vr_total_minimo = %.2f,
              vr_total = %.2f,
              vr_total_margem_desconto = %.2f,
              vr_mensal = %.2f,
              vr_comissao = %.2f,
              vr_comissao_locacao = %.2f,
              meses_retorno_investimento = %.2f,
              vr_total_venda_impostos = %.2f
            where
              id = %d;
            commit work;''' % totais)

        return totais

    def ajusta_produtos_relacionados(self, cr, uid, item_pai_obj, context={}):
        #
        # Buscamos os itens que serão relacionados
        #
        item_pool = self.pool.get('sale.order.line')

        if item_pai_obj.order_id.desvincula_itens:
            return

        item_ids = item_pool.search(cr, uid, [('order_id', '=', item_pai_obj.order_id.id), ('order_line_id', '=', item_pai_obj.id)])

        #
        # Excluímos os antigos
        #
        item_pool.unlink(cr, uid, item_ids)

        #
        # Verificamos se o novo produto tem itens relacionados
        #
        if len(item_pai_obj.product_id.relacionado_orcamento_ids):
            for produto_relacionado_obj in item_pai_obj.product_id.relacionado_orcamento_ids:
                vr_unitario_custo = produto_relacionado_obj.produto_relacionado_id.standard_price or produto_relacionado_obj.produto_relacionado_id.preco_minimo

                vr_unitario_minimo = produto_relacionado_obj.produto_relacionado_id.preco_minimo or produto_relacionado_obj.produto_relacionado_id.list_price

                vr_unitario_venda = produto_relacionado_obj.produto_relacionado_id.list_price or produto_relacionado_obj.produto_relacionado_id.preco_minimo

                quantidade = produto_relacionado_obj.quantidade * item_pai_obj.product_uom_qty
                print('quantidade', quantidade)
                print('quantidade', produto_relacionado_obj.quantidade)
                print('quantidade', item_pai_obj.product_uom_qty)

                dados = {
                    'order_id': item_pai_obj.order_id.id,
                    'product_id': produto_relacionado_obj.produto_relacionado_id.id,
                    'name': produto_relacionado_obj.produto_relacionado_id.name,
                    'orcamento_categoria_id': produto_relacionado_obj.produto_relacionado_id.orcamento_categoria_id.id,
                    'product_uom_qty': quantidade,
                    'vr_unitario_custo': vr_unitario_custo,
                    'vr_total_custo': quantidade * vr_unitario_custo,
                    'vr_unitario_minimo': vr_unitario_minimo,
                    'vr_total_minimo': quantidade * vr_unitario_minimo,
                    'vr_unitario_venda': vr_unitario_venda,
                    'vr_total_venda': quantidade * vr_unitario_venda,
                    'price_unit': vr_unitario_venda,
                    #'vr_unitario_venda_impostos': vr_unitario_venda_impostos,
                    'usa_unitario_minimo': False,
                    'margem': produto_relacionado_obj.produto_relacionado_id.orcamento_categoria_id.margem,
                    'discount': 0,
                    'vr_unitario_margem_desconto': 0,
                    'price_subtotal': 0,
                    'order_line_id': item_pai_obj.id,
                    'autoinsert': False,
                }
                #calculo = item_pool.on_change_quantidade_margem_desconto(cr, uid, [], None, None, qty=dados['product_uom_qty'], vr_unitario_custo=dados['vr_unitario_custo'], vr_unitario_minimo=dados['vr_unitario_minimo'], vr_unitario_venda=dados['vr_unitario_venda'], margem=dados['margem'], desconto=dados['discount'], autoinsert=dados['autoinsert'], mudou_quantidade=False, usa_unitario_minimo=dados['usa_unitario_minimo'], context=context)
                #dados['vr_total_custo'] = calculo['value']['vr_total_custo']
                #dados['vr_total_minimo'] = calculo['value']['vr_total_minimo']
                #dados['vr_unitario_venda'] = calculo['value']['vr_unitario_venda']
                ##dados['price_unit'] = calculo['value']['price_unit']
                #dados['vr_total_margem_desconto'] = calculo['value']['vr_total_margem_desconto']
                #dados['vr_unitario_margem_desconto'] = calculo['value']['vr_unitario_margem_desconto']
                #dados['vr_unitario_venda_impostos'] = calculo['value']['vr_unitario_venda_impostos']
                #dados['vr_total_venda_impostos'] = calculo['value']['vr_total_venda_impostos']

                item_id = item_pool.create(cr, uid, dados)
                item_obj = item_pool.browse(cr, uid, item_id)

                contexto_novo = {
                    'company_id': item_obj.order_id.company_id.id,
                    'partner_id': item_obj.order_id.partner_id.id,
                    'operacao_fiscal_produto_id': item_obj.order_id.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': item_obj.order_id.operacao_fiscal_servico_id.id,
                    'orcamento_aprovado': item_obj.order_id.orcamento_aprovado,
                    'quantity': item_obj.product_uom_qty,
                    'pricelist': item_obj.order_id.pricelist_id.id,
                    #'shop': item_obj.order_id.shop_id,
                    'uom': item_obj.product_uom.id,
                    'force_product_uom': True,
                    'price_unit': produto_relacionado_obj.produto_relacionado_id.list_price,
                }

                ##def on_change_quantidade_margem_desconto(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=0, vr_unitario_minimo=0, vr_unitario_venda=0, margem=0, desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context={}, desconto_direto=False, margem_direta=False):


                impostos = item_pool.on_change_quantidade_margem_desconto(cr, uid, [item_obj.id], item_obj.order_id.pricelist_id.id, item_obj.product_id.id, quantidade, item_obj.product_id.uom_id.id, 0, False,  name=item_obj.name, partner_id=item_obj.order_id.partner_id.id, lang=False, update_tax=False, date_order=item_obj.order_id.date_order, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=dados['margem'], desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context=contexto_novo, desconto_direto=False, margem_direta=False)

                valores = impostos['value']

                dados = {}
                for chave in valores:
                    if (not chave.startswith('default_')) and (not isinstance(valores[chave], DicionarioBrasil)):
                        dados[chave] = valores[chave]

                item_pool.write(cr, uid, [item_obj.id], dados, context={'calculo_resumo': True})


    #def copy(self, cr, uid, id, default=None, context=None):
        #if not default:
            #default = {}

        #default.update(
            #{'order_line_ids': []}
        #)

        #return super(sale_order_line, self).copy(cr, uid, id, default, context)

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.invoiced:
                raise osv.except_osv(_('Invalid action !'), _('You cannot cancel a sale order line that has already been invoiced!'))
            for move_line in line.move_ids:
                if move_line.state != 'cancel':
                    raise osv.except_osv(
                            _('Could not cancel sales order line!'),
                            _('You must first cancel stock moves attached to this sales order line.'))
        return self.write(cr, uid, ids, {'state': 'cancel'}, context={'calcula_resumo': True})

    def button_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirmed'}, context={'calcula_resumo': True})

    def button_done(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        res = self.write(cr, uid, ids, {'state': 'done'}, context={'calcula_resumo': True})
        for line in self.browse(cr, uid, ids, context=context):
            wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
        return res


sale_order_line()
