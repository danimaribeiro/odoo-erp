# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields


class sale_order_referencia(osv.Model):
    _name = 'sale.order.referencia'
    _description = u'Orçamento de referência'

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', u'Tipo de orçamento', ondelete='restrict'),
        'name': fields.char(u'Referência', size=60),

        #
        # Itens para os orçamentos de referência
        #
        'item_produto_ids': fields.one2many('sale.order.line.referencia', 'order_id', string=u'Produtos', domain=[['tipo_item', '=', 'P']]),
        'item_servico_ids': fields.one2many('sale.order.line.referencia', 'order_id', string=u'Serviços', domain=[['tipo_item', '=', 'S']]),
        'item_mensalidade_ids': fields.one2many('sale.order.line.referencia', 'order_id', string=u'Mensalidades', domain=[['tipo_item', '=', 'M']]),
    }

    #_defaults = {
    #}



sale_order_referencia()
