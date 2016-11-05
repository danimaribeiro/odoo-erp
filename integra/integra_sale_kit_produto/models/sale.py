# -*- encoding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.base import DicionarioBrasil


class sale_order(osv.Model):
    _inherit = 'sale.order'
    
    _columns = {
        'item_principal_ids': fields.one2many('sale.order.line', 'order_id', u'Produtos principais', domain=[('parent_id', '=', False)]),
    }

    def ajusta_acessorios(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('sale.order.line')

        for order_obj in self.browse(cr, uid, ids):
            for item_obj in order_obj.order_line:
                for acessorio_obj in item_obj.itens_acessorios_ids:
                    produto_obj = acessorio_obj.acessorio_id
                    quantidade = acessorio_obj.quantidade

                    contexto_item = {
                        'partner_id': order_obj.partner_id.id,
                        'quantity': quantidade,
                        'product_uom_qty': quantidade,
                        'pricelist': order_obj.pricelist_id.id,
                        'shop': order_obj.shop_id.id,
                        'uom': produto_obj.uom_id.id,
                        'force_product_uom': True,
                        'operacao_fiscal_produto_id': order_obj.operacao_fiscal_produto_id.id,
                        'operacao_fiscal_servico_id': order_obj.operacao_fiscal_servico_id.id,
                        'company_id': order_obj.company_id.id
                    }

                    if acessorio_obj.linha_acessorio_id:
                        if acessorio_obj.linha_acessorio_id.quantidade_manual:
                            continue
                        
                        #
                        # Ajustar a quantidade para ser proporcional
                        #
                        quantidade = D(item_obj.product_uom_qty or 0) * D(acessorio_obj.linha_acessorio_id.quantidade_componente or 0)
                        
                        if quantidade == acessorio_obj.linha_acessorio_id.product_uom_qty:
                            continue
                        
                    dados_item = item_pool.product_id_change(cr, uid, False, order_obj.pricelist_id.id, produto_obj.id, quantidade, False, False, False, False, order_obj.partner_id.id, False, True, order_obj.date_order, False, False, False, contexto_item)

                    dados_item = dados_item['value']
                    dados_item.update({
                        'order_id': order_obj.id,
                        'product_id': acessorio_obj.acessorio_id.id,
                        'item_acessorio_id': acessorio_obj.id,
                        'parent_id': item_obj.id,
                        'quantidade_componente': acessorio_obj.quantidade,
                    })
                    dados = {}
                    for chave in dados_item:
                        if not isinstance(dados_item[chave], DicionarioBrasil):
                            dados[chave] = dados_item[chave]
                    
                    print(dados)        
                    if not acessorio_obj.linha_acessorio_id:
                        item_id = item_pool.create(cr, uid, dados)
                        acessorio_obj.write({'linha_acessorio_id': item_id})
                    else:
                        acessorio_obj.linha_acessorio_id.write(dados)                        
                
                for opcionais_obj in item_obj.itens_opcionais_ids:
                    if opcionais_obj.linha_opcional_id:
                        continue
                                                    
                    produto_obj = opcionais_obj.opcional_id

                    contexto_item = {
                        'partner_id': order_obj.partner_id.id,
                        'quantity': opcionais_obj.quantidade,
                        'product_uom_qty': opcionais_obj.quantidade,
                        'pricelist': order_obj.pricelist_id.id,
                        'shop': order_obj.shop_id.id,
                        'uom': produto_obj.uom_id.id,
                        'force_product_uom': True,
                        'operacao_fiscal_produto_id': order_obj.operacao_fiscal_produto_id.id,
                        'operacao_fiscal_servico_id': order_obj.operacao_fiscal_servico_id.id,
                        'company_id': order_obj.company_id.id
                    }

                    dados_item = item_pool.product_id_change(cr, uid, False, order_obj.pricelist_id.id, produto_obj.id, opcionais_obj.quantidade, False, False, False, False, order_obj.partner_id.id, False, True, order_obj.date_order, False, False, False, contexto_item)

                    dados_item = dados_item['value']
                    dados_item.update({
                        'order_id': order_obj.id,
                        'product_id': opcionais_obj.opcional_id.id,
                        'item_opcional_id': opcionais_obj.id,
                        'eh_opcional': True,
                        'quantidade_componente': opcionais_obj.quantidade,
                        #'parent_id': item_obj.id,
                    })
                    dados = {}
                    for chave in dados_item:
                        if not isinstance(dados_item[chave], DicionarioBrasil):
                            dados[chave] = dados_item[chave]

                    item_id = item_pool.create(cr, uid, dados)
                    opcionais_obj.write({'linha_opcional_id': item_id})                    

    def create(self, cr, uid, dados, context={}):
        res = super(sale_order, self).create(cr, uid, dados, context=context)

        if '__copy_data_seen' not in context:
            self.pool.get('sale.order').ajusta_acessorios(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        if '__copy_data_seen' not in context:
            self.pool.get('sale.order').ajusta_acessorios(cr, uid, ids, context=context)

        return res
    
    def copy(self, cr, uid, id, default={}, context={}):
        res = super(sale_order, self).copy(cr, uid, id, default=default, context=context)
        
        sale_pool = self.pool.get('sale.order')
        item_pool = self.pool.get('sale.order.line')
        
        original_obj = sale_pool.browse(cr, uid, id)
        copiado_obj = sale_pool.browse(cr, uid, res)
        
        #
        # Apagamos os itens copiados
        #
        for item_obj in copiado_obj.order_line:
            item_obj.unlink()

        #
        # E copiamos os itens na ordem certa
        #
        lista_pais = {}
        for item_obj in original_obj.order_line:
            item_novo_id = item_pool.copy(cr, uid, item_obj.id)
            
            if not item_obj.parent_id:
                lista_pais[item_obj.id] = item_novo_id
                item_pool.write(cr, uid, [item_novo_id], {'order_id': copiado_obj.id})
            else:
                item_pool.write(cr, uid, [item_novo_id], {'order_id': copiado_obj.id, 'parent_id': lista_pais[item_obj.parent_id.id]})
                
        return res
                


sale_order()
