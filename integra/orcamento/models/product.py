# -*- encoding: utf-8 -*-


from osv import osv, fields


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    _columns = {
        'orcamento_categoria_id': fields.many2one('orcamento.categoria', string=u'Categoria de orçamento'),
        'autoinsert': fields.boolean(u'Calcula automaticamente baseado nos totais de outras categorias de orçamento'),
        'preco_minimo': fields.float(u'Preço mínimo'),
        'autocalc_orcamento_categoria_ids': fields.one2many('product.autocalc_orcamento_categoria', 'product_id', u'Calcular valor no orçamento a partir das seguintes categorias de orçamento'),
        'relacionado_orcamento_ids': fields.one2many('product.relacionado_orcamento', 'product_id', u'Produtos relacionados no orçamento'),
        'produto_faturamento_id': fields.many2one('product.product', u'Item para contrato/faturamento'),
    }

    def _check_preco_minimo(self, cursor, user, ids, context=None):
        for produto in self.browse(cursor, user, ids, context=context):
            if produto.orcamento_categoria_id and produto.orcamento_categoria_id.valida_preco_minimo:
                if produto.product_tmpl_id.standard_price:
                    if produto.preco_minimo < produto.product_tmpl_id.standard_price:
                        return False
                else:
                    return False

        return True

    _constraints = [
        (_check_preco_minimo, u'Erro: O preço mínimo não pode ser menor do que o de custo!', ['preco_minimo']),
    ]


product_product()


class product_autocalc_orcamento_categoria(osv.Model):
    _name = 'product.autocalc_orcamento_categoria'
    _columns = {
        'product_id': fields.many2one('product.product', u'Produto', select=True, ondelete='restrict'),
        'orcamento_categoria_id': fields.many2one('orcamento.categoria', u'Categoria de orçamento'),
        'percentual': fields.float(u'Percentual (%)'),
        'unidade': fields.related('uom_id', 'name', type='char', size=20, string=u'Unidade', select=False, store=False, readonly=True),
    }


product_autocalc_orcamento_categoria()


class product_relacionado_orcamento(osv.Model):
    _name = 'product.relacionado_orcamento'

    _columns = {
        'product_id': fields.many2one('product.product', 'Produto'),
        'produto_relacionado_id': fields.many2one('product.product', 'Produtos relacionados'),
        'quantidade': fields.float('Quantidade'),
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('product_id', False) and vals.get('produto_relacionado_id', False):
            relacionamento_recursivo_ids = self.search(cr, uid, [('product_id', '=', vals['produto_relacionado_id']), ('produto_relacionado_id', '=', vals['product_id'])])

            if relacionamento_recursivo_ids:
                raise osv.except_osv('Erro!', u'Não é permitido relacionar produtos recursivamente (A rel. B, B rel. A)')

            if vals['product_id'] == vals['produto_relacionado_id']:
                raise osv.except_osv('Erro!', u'Não é permitido relacionar um produto a si próprio (A rel. A)')

        return super(product_relacionado_orcamento, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if ids and vals.get('product_id', False):
            relacionado_objs = self.browse(cr, uid, ids)

            for relacionado_obj in relacionado_objs:
                relacionamento_recursivo_ids = self.search(cr, uid, [('product_id', '=', relacionado_obj.id), ('produto_relacionado_id', '=', vals['product_id'])])

                if relacionamento_recursivo_ids:
                    raise osv.except_osv('Erro!', u'Não é permitido relacionar produtos recursivamente (A rel. B, B rel. A)')

                if vals['product_id'] == relacionado_obj.id:
                    raise osv.except_osv('Erro!', u'Não é permitido relacionar um produto a si próprio (A rel. A)')

        return super(product_relacionado_orcamento, self).write(cr, uid, ids, vals, context=None)

product_relacionado_orcamento()
