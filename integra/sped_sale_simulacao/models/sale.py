# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    _columns = {
        'simulacao': fields.boolean(u'Simulação?'),
        'lista_preco_ajustar_id': fields.many2one('product.pricelist', u'Lista de preços a ajustar'),
    }

    _defaults = {
        'simulacao': False,
    }

    def ajuste_lista_preco(self, cr, uid, ids, context={}):
        #regra_pool = self.pool.get('product.pricelist.version')
        regra_pool = self.pool.get('product.pricelist.item')
        custo_ultima_compra_id = self.pool.get('product.price.type').search(cr, 1, [['field','=','custo_ultima_compra']])

        if custo_ultima_compra_id:
            custo_ultima_compra_id = custo_ultima_compra_id[0]
        else:
            custo_ultima_compra_id = 1

        #
        # Primeiro, eliminamos as regras antigas dos produtos em questão
        #
        produtos_antigos = []
        versao_ativa = None
        for ped_obj in self.browse(cr, uid, ids):
            if not ped_obj.lista_preco_ajustar_id:
                continue

            for versao_obj in ped_obj.lista_preco_ajustar_id.version_id:
                if not versao_obj.active:
                    continue

                if versao_ativa is None:
                    versao_ativa = versao_obj

                for preco_item_obj in versao_obj.items_id:
                    if not preco_item_obj.product_id:
                        continue

                    for ped_item_obj in ped_obj.order_line:
                        if ped_item_obj.product_id.id == preco_item_obj.product_id.id:
                            produtos_antigos += [preco_item_obj.id]

            regra_pool.unlink(cr, uid, produtos_antigos)

            #
            # Agora, criamos as regras novas
            #
            for ped_item_obj in ped_obj.order_line:
                dados = {
                    'name': ped_item_obj.product_id.name,
                    'price_version_id': versao_ativa.id,
                    'product_id': ped_item_obj.product_id.id,
                    'sequence': 1,
                    'base': custo_ultima_compra_id,
                    'price_round': D('0.01'),
                    #
                    # Só Deus sabe porque cargas d'água me foram chamar a margem
                    # de desconto....
                    #
                    'price_discount': D(ped_item_obj.margem_fixa) / D(100),
                }
                regra_pool.create(cr, uid, dados)


sale_order()
