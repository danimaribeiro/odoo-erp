# -*- encoding: utf-8 -*-


from osv import osv, fields


class stock_move(osv.Model):
    _inherit = 'stock.move'

    _columns = {
        'orcamento_categoria_id': fields.many2one('orcamento.categoria', u'Categoria do orçamento', ondelete='restrict'),
    }

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,                             loc_dest_id=False, address_id=False, context=None):
        resposta = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id, address_id)

        if not prod_id:
            return resposta

        product_obj = self.pool.get('product.product').browse(cr, uid, prod_id, context=context)

        resposta['value']['orcamento_categoria_id'] = product_obj.orcamento_categoria_id.id

        return resposta


stock_move()
