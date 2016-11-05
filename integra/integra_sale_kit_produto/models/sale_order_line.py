# -*- encoding: utf-8 -*-


from decimal import Decimal as D
from osv import osv, fields



class sale_order_line_acessorio(osv.Model):
    _name = 'sale.order.line.acessorio'

    def _linha_acessorio_id(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for linha_obj in self.browse(cr, uid, ids):
            sql = """
            select
                oi.id
            from
                sale_order_line oi
            where
                oi.product_id = {product_id}
                and oi.parent_id = {line_id};
            """
            sql = sql.format(product_id=linha_obj.acessorio_id.id, line_id=linha_obj.line_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[linha_obj.id] = False

            if len(dados):
                res[linha_obj.id] = dados[0][0]

        return res

    def _quantidade(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for linha_obj in self.browse(cr, uid, ids):
            sql = """
            select
                pa.quantidade
            from
                product_acessorio_obrigatorio pa
            where
                pa.product_id = {product_id}
                and pa.acessorio_id = {acessorio_id};
            """
            sql = sql.format(product_id=linha_obj.line_id.product_id.id, acessorio_id=linha_obj.acessorio_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[linha_obj.id] = False

            if len(dados):
                res[linha_obj.id] = dados[0][0]

        return res

    _columns = {
        'line_id': fields.many2one('sale.order.line', u'Item', ondelete='cascade'),
        'order_id': fields.related('line_id', 'order_id', type='many2one', relation='sale.order', string=u'Pedido', store=True),
        'acessorio_id': fields.many2one('product.product', u'Acessório', ondelete='restrict'),
        'linha_acessorio_id': fields.function(_linha_acessorio_id, type='many2one', relation='sale.order.line', string=u'Item acessório'),
        'quantidade': fields.function(_quantidade, type='float', string=u'Quantidade'),
    }


sale_order_line_acessorio()


class sale_order_line_produto_opcional(osv.Model):
    _name = 'sale.order.line.produto.opcional'

    def _linha_opcional_id(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for linha_obj in self.browse(cr, uid, ids):
            sql = """
            select
                oi.id
            from
                sale_order_line oi
            where
                oi.product_id = {product_id}
                and oi.parent_id = {line_id};
            """
            sql = sql.format(product_id=linha_obj.opcional_id.id, line_id=linha_obj.line_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[linha_obj.id] = False

            if len(dados):
                res[linha_obj.id] = dados[0][0]

        return res

    def _quantidade(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for linha_obj in self.browse(cr, uid, ids):
            sql = """
            select
                pa.quantidade
            from
                product_acessorio pa
            where
                pa.product_id = {product_id}
                and pa.acessorio_id = {acessorio_id};
            """
            sql = sql.format(product_id=linha_obj.line_id.product_id.id, acessorio_id=linha_obj.opcional_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[linha_obj.id] = False

            if len(dados):
                res[linha_obj.id] = dados[0][0]

        return res

    _columns = {
        'line_id': fields.many2one('sale.order.line', u'Item', ondelete='cascade'),
        'opcional_id': fields.many2one('product.product', u'Opcional', ondelete='restrict'),
        #'linha_opcional_id': fields.function(_linha_opcional_id, type='many2one', relation='sale.order.line', string=u'Item opcional'),
        'quantidade': fields.function(_quantidade, type='float', string=u'Quantidade'),
        'linha_opcional_id': fields.many2one('sale.order.line', u'Item opcional', ondelete='cascade'),
    }


sale_order_line_produto_opcional()


class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _parent_name = 'parent_id'
    _parent_store = True

    def _get_codigo_completo(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            codigo = str(item_obj.id)

            if item_obj.parent_id:
                codigo = str(item_obj.parent_id.id) + '.' + codigo

            res[item_obj.id] = codigo

        return res

    _columns = {
        'codigo_completo': fields.function(_get_codigo_completo, type='char', size=30, string=u'Código', store=True, select=True),
        'product_acessorio_ids': fields.related('product_id', 'acessorio_selecao_ids', type='many2many', relation='product.product', string=u'Acessórios originais', readonly=True),
        'product_acessorio_obrigatorio_ids': fields.related('product_id', 'acessorio_obrigatorio_selecao_ids', type='many2many', relation='product.product', string=u'Acessórios obrigatórios', readonly=True),

        'acessorio_ids': fields.one2many('sale.order.line.acessorio', 'line_id', u'Acessórios'),
        'acessorio_selecao_ids': fields.many2many('product.product', 'sale_order_line_acessorio', 'line_id', 'acessorio_id', u'Acessórios'),

        'opcionais_ids': fields.one2many('sale.order.line.produto.opcional', 'line_id', u'Produtos Opcionais'),
        'opcionais_selecao_ids': fields.many2many('product.product', 'sale_order_line_produto_opcional', 'line_id', 'opcional_id', u'Produtos Opcionais'),

        'eh_opcional': fields.boolean(u'É opcional?'),
        'itens_acessorios_ids': fields.one2many('sale.order.line.acessorio', 'line_id', u'Acessórios'),
        'itens_opcionais_ids': fields.one2many('sale.order.line.produto.opcional', 'line_id', u'Produtos opcionais'),
        'parent_id': fields.many2one('sale.order.line', u'Acessório/Opcional de'),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),

        'quantidade_componente': fields.float(u'Quantidade componente'),
        'quantidade_manual': fields.boolean('Quantidade de acessório em modo manual?')
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):

        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        if product_id and  '__copy_data_seen' not in context:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
            acessorio_ids = []

            if len(product_obj.acessorio_ids):
                for acessorio_obj in product_obj.acessorio_selecao_ids:
                    acessorio_ids.append(acessorio_obj.id)

                res['value']['product_acessorio_ids'] = acessorio_ids

        return res


sale_order_line()
