# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.data import hoje
from pybrasil.valor.decimal import Decimal as D


class product_supplierinfo(osv.Model):
    _name = 'product.supplierinfo'
    _inherit = 'product.supplierinfo'
    _order = 'product_id, preco desc'
    
    def _calcula_totais(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(item_obj.quantidade_cotada or 0) * D(item_obj.preco or 0)
            res[item_obj.id] = valor

        return res
    
    def get_variant(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for item_obj in self.browse(cr, uid, ids):
            sql = """
            select
                p.variants
                 
            from
                product_product p
                
            where
                p.product_tmpl_id = {product_id};
            """
            sql = sql.format(product_id=item_obj.product_id.id)
            cr.execute(sql)
            dados = cr.fetchall()
            
            res[item_obj.id] = False
            if len(dados):
                res[item_obj.id] = dados[0][0]
                
        return res

    _columns = {
        'codigo_cotacao': fields.integer(u'Código da cotação'),
        'condicao_pagamento': fields.char(u'Condição de pagamento', size=60),
        'preco': fields.float(u'Preço unit.'),
        'quantidade_cotada': fields.float(u'Quantidade cotada'),
        'data_atualizacao': fields.date(u'Data atualização'),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unid.'),
        'obs': fields.text(u'Observação'),
        'total': fields.function(_calcula_totais, type='float', method=True, string=u'Total'),
        'variants': fields.function(get_variant, type='char', string=u'Subtipo'),

    }

    def create(self, cr, uid, dados, context={}):
        if 'min_qty' not in dados:
            dados['min_qty'] = 0.00

        if 'preco' in dados and dados['preco']:
            dados['data_atualizacao'] = str(hoje())
        elif 'condicao_pagamento' in dados and dados['condicao_pagamento']:
            dados['data_atualizacao'] = str(hoje())

        res = super(product_supplierinfo, self).create(cr, uid, dados, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if 'preco' in dados and dados['preco']:
            dados['data_atualizacao'] = str(hoje())
        elif 'condicao_pagamento' in dados and dados['condicao_pagamento']:
            dados['data_atualizacao'] = str(hoje())
        elif 'delay' in dados and dados['delay']:
            dados['data_atualizacao'] = str(hoje())

        res = super(product_supplierinfo, self).write(cr, uid, ids, dados, context=context)

        return res
    
    def onchange_preco(self, cr, uid, ids, quantidade_cotada, preco):
        valor = D(quantidade_cotada or 0) * D(preco or 0)
        return {'value': {'total': valor}}


product_supplierinfo()
