# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from osv import osv, fields


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'custo_ids': fields.one2many('product.custo', 'product_id', u'Estoques e custo'),
        'sped_documentoitem_ids': fields.one2many('sped.documentoitem', 'produto_id', u'Notas de entrada', domain=['|', ('modelo', '=', 'TF'), '&', ('modelo', 'in', ['01', '55']), '&', ('stock_location_dest_id', '!=', False), ('numero', '>', 0)])
    }

    def copy(self, cr, uid, id, dados, context={}):
        dados['custo_ids'] = False
        dados['sped_documentoitem_ids'] = False

        return super(product_product, self).copy(cr, uid, id, dados, context=context)


product_product()


class product_custo(osv.Model):
    _description = 'Estoque por produto e local'
    _name = 'product.custo'

    _SQL_CUSTO = """
select
coalesce(cm.vr_unitario_custo, 0), coalesce(cm.vr_total, 0), coalesce(cm.quantidade, 0)

from
    custo_medio({company_id}, {location_id}, {product_id}) cm

order by
    cm.data desc,
    cm.entrada_saida desc,
    cm.move_id desc

limit 1;
    """

    def busca_custo(self, cr, uid, company_id, location_id, product_id):
        filtro = {
            'company_id': company_id or -1,
            'location_id': location_id or -1,
            'product_id': product_id or -1,
        }
        sql = self._SQL_CUSTO.format(**filtro)

        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) >= 1:
            vr_unitario, vr_total, quantidade = dados[0]
        else:
            vr_unitario, vr_total, quantidade = 0, 0, 0

        vr_unitario = D(vr_unitario)
        vr_total = D(vr_total)
        quantidade = D(quantidade)

        return vr_unitario, quantidade, vr_total

    def _get_quantidade_custo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        stock_pool = self.pool.get('stock.move')

        for custo_obj in self.browse(cr, uid, ids):
            if not custo_obj.company_id:
                res[custo_obj.id] = D('0')
                continue

            filtro = {
                'company_id': custo_obj.company_id.id,
                'location_id': custo_obj.location_id.id,
                'product_id': custo_obj.product_id.id,
            }
            vr_unitario, quantidade, vr_total = self.busca_custo(cr, uid, **filtro)

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