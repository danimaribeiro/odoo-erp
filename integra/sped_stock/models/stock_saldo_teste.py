# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import hoje
from pybrasil.valor.decimal import Decimal as D
from tools.translate import _
import netsvc
import tools
from tools import float_compare
import decimal_precision as dp
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby


class stock_saldo(osv.Model):
    _name = 'stock.saldo'
    _order = 'data'

    _columns = {
        'data': fields.date(u'Data'),
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'location_id': fields.many2one('stock.location', u'Local de estoque', ondelete='restrict'),
        'product_id': fields.many2one('product.product', u'Produto', ondelete='restrict'),
        'quantidade_entrada': fields.float(u'Quantidade entrada'),
        'quantidade_saida':fields.float(u'Quantidade saída'),
        'quantidade':fields.float(u'Quantidade'),
        'vr_unitario_medio': fields.float(u'custo médio'),
        'vr_total': fields.float(u'Valor Total'),
        'user_id': fields.many2one('res.users', u'Usuário', ondelete='restrict'),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

    def unlink(self, cr, uid, ids, context={}):
        res = {}

        return res

    def gera_saldo_estoque_completo(self, cr, uid, ids, context={}):
        saldo_pool = self.pool.get('stock.saldo')
        move_pool = self.pool.get('stock.move')
        #data = hoje() + relativedelta(days=-1)
        data = hoje()

        sql = """
            select
                es.company_id,
                es.location_id,
                es.product_id,
                es.data

            from
                estoque_entrada_saida es

            group by
                es.company_id,
                es.location_id,
                es.product_id,
                es.data

            order by
                es.data,
                es.product_id,
                es.location_id,
                es.company_id;
        """
        cr.execute(sql)
        dados = cr.fetchall()

        #
        # Busca o último movimento de estoque do dia, para o caso, onde vai ter o custo final do produto para o dia
        #
        sql = """
            select
                ees.move_id

            from
                estoque_entrada_saida ees

            where
                    ees.location_id = {location_id}
                and ees.company_id = {company_id}
                and ees.product_id = {product_id}
                and ees.data = {data}

            order by
                ees.tipo desc,
                ees.move_id desc

            limit 1
        """
        for company_id, location_id, product_id, data in dados:
            filtro = {
                'company_id': company_id,
                'location_id': location_id,
                'product_id': product_id,
                'dada': data,
            }
            cr.execute(sql.format(**filtro))
            dados_move = cr.fetchall()
            move_id = dados_move[0][0]
            move_obj = move_pool.browse(cr, uid, move_id)

            saldo = {
                'company_id': company_id,
                'location_id': location_id,
                'product_id': product_id,
                'data': data,
                'vr_unitario_medio': custo_medio,
                'quantidade_entrada': quantidade_entrada,
                'quantidade_saida': quantidade_saida,
            }
                quantidade =  D(quantidade_entrada) - D(quantidade_saida)
                saldo['quantidade'] = quantidade

                vr_total = D(custo_medio) * quantidade
                saldo['vr_total'] = vr_total

                stock_saldo_pool.create(cr, 1, saldo)

        return True

    def gera_saldo_estoque(self, cr, uid, ids, context={}):
        stock_saldo_pool = self.pool.get('stock.saldo')
        data = hoje() + relativedelta(days=-1)
        location_ids = self.pool.get('stock.location').search(cr, 1, [])

        for location_id in location_ids:
            sql = """
                select
                    a.local_id as local_id,
                    cast(min(a.data) as date) as data
                from (
                    select
                        sm.location_id  as local_id,
                        cast(min(sm.date) as date) as data
                    from
                        stock_move sm
                    where
                        (sm.create_date >= '{data}'
                        or
                        sm.write_date >= '{data}')
                    group by
                        sm.location_id

                    union all

                    select
                        sm.location_dest_id as local_id,
                        cast(min(sm.date) as date) as data
                    from
                        stock_move sm
                    where
                        (sm.create_date >= '{data}'
                        or
                        sm.write_date >= '{data}')
                    group by
                        sm.location_dest_id
                ) as a
                group by
                    a.local_id;
            """
            sql = sql.format(data='2016-01-01')

        return True

stock_saldo()
