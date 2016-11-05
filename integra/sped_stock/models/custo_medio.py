# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from osv import osv, fields


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'custo_ids': fields.one2many('product.custo', 'product_id', u'Estoques e custo'),
        'sped_documentoitem_ids': fields.one2many('sped.documentoitem', 'produto_id', u'Notas de entrada', domain=[('stock_location_dest_id', '!=', False)])
    }


product_product()


class product_custo(osv.Model):
    _description = 'Estoque por produto e local'
    _name = 'product.custo'

    _SQL_CUSTO = """
select
coalesce(cm.vr_unitario_custo, 0), coalesce(cm.vr_total, 0), coalesce(cm.quantidade, 0)

from
    custo_medio() cm
    join stock_move m on m.id = cm.move_id
    join res_company c on c.id = m.company_id

where
        cm.product_id = {produto_id}
    and cm.location_id = {location_id}
    and c.id = {company_id}

order by
    cm.data desc,
    cm.entrada_saida desc,
    cm.move_id desc

limit 1;
    """

    def _get_quantidade_custo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        stock_pool = self.pool.get('stock.move')

        for custo_obj in self.browse(cr, uid, ids):
            filtro = {
                'company_id': custo_obj.company_id.id,
                'location_id': custo_obj.product_id.id,
                'location_id': custo_obj.location_id.id,
            }
            sql = self._SQL_CUSTO.format(**filtro)

            print(sql)

            cr.execute(sql)
            dados = cr.fetchall()

            vr_unitario, vr_total, quantidade = dados[0]

            if nome_campo == 'quantidade':
                res[custo_obj.id] = D(quantidade)
            elif nome_campo == 'vr_unitario':
                res[custo_obj.id] = D(vr_unitario)
            elif nome_campo == 'vr_total':
                res[custo_obj.id] = D(vr_total)

        return res

    _columns = {
        'data': fields.date(u'Data'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'location_id': fields.many2one('stock.location', u'Local do estoque'),
        'product_id': fields.many2one('product.product', u'Produto'),
        #'quantidade': fields.float(u'Quantidade'),
        #'vr_unitario': fields.float(u'Valor unitário', digits=(21, 10)),
        #'vr_total': fields.float(u'Valor total'),
        'quantidade': fields.function(_get_quantidade_custo, type='float', string=u'Quantidade', digits=(18, 4)),
        'vr_unitario': fields.function(_get_quantidade_custo, type='float', string=u'Unitário', digits=(21, 10)),
        'vr_total': fields.function(_get_quantidade_custo, type='float', string=u'Total', digits=(18, 2)),
    }

    _defaults = {
        'quantidade': 0,
        'vr_unitario': 0,
        'vr_total': 0,
    }


product_custo()