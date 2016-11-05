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
    _order = 'data desc, product_id, company_id, location_id'

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
        res = False

        if uid == 1:
            res = super(stock_saldo, self).unlink(cr, uid, ids, context=context)

        return res

    #def gera_saldo_estoque_completo(self, cr, uid, ids, context={}):
        #item_pool = self.pool.get('sped.documentoitem')

        #item_pool.ajusta_custo_unitario_estoque(cr, uid, False, context=context)

    def gera_saldo_estoque_completo(self, cr, uid, ids=[], context={}):
        stock_saldo_pool = self.pool.get('stock.saldo')

        cr.execute("delete from stock_saldo where data = '{data}';".format(data=str(hoje())))
        data = hoje() + relativedelta(days=-1)
        cr.execute("delete from stock_saldo where data = '{data}';".format(data=str(data)))

        sql = """
            select
                es.company_id,
                es.location_id,
                es.product_id,
                es.data

            from
                estoque_entrada_saida es
                left join stock_saldo ss on ss.company_id = es.company_id and ss.location_id = es.location_id and ss.product_id = es.product_id and ss.data = es.data

            where
                ss.id is null

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

        SQL_SALDO = """
            select
                coalesce(sum(
                case
                    when es.tipo = 'E' and es.data = '{data}' then coalesce(quantidade, 0)
                else
                    0
                end), 0) as quantidade_entrada,
                coalesce(sum(
                case
                    when es.tipo = 'S' and es.data = '{data}' then coalesce(quantidade, 0)
                else
                    0
                end), 0) as quantidade_saida,
                coalesce(sum(
                case
                    when es.tipo = 'E' then coalesce(quantidade, 0)
                else
                    coalesce(quantidade, 0) * -1
                end), 0) as quantidade

            from estoque_entrada_saida es

            where
                es.data <= '{data}'
                and es.location_id = {location_id}
                and es.company_id = {company_id}
                and product_id = {product_id};
            """

        SQL_CUSTO = """
            select
                coalesce(cm.vr_unitario_custo, 0) as vr_unitario_custo

            from
                custo_medio({company_id}, {location_id}, {product_id}) cm

            where
                cm.data <= '{data}'

            order by
                cm.data desc, cm.entrada_saida desc, cm.move_id desc

            limit 1;
        """

        i = 1
        for company_id, location_id, product_id, data in dados:
            filtro = {
                'company_id': company_id,
                'location_id': location_id,
                'product_id': product_id,
                'data': data,
            }
            sql_saldo = SQL_SALDO.format(**filtro)
            sql_custo = SQL_CUSTO.format(**filtro)

            cr.execute(sql_saldo)
            dados_saldo = cr.fetchall()

            quantidade_entrada = D(dados_saldo[0][0] or 0)
            quantidade_saida = D(dados_saldo[0][1] or 0)
            quantidade = D(dados_saldo[0][2] or 0)

            cr.execute(sql_custo)
            dados_custo = cr.fetchall()
            vr_unitario_custo = D(dados_custo[0][0] or 0)

            saldo = {
                'company_id': company_id,
                'location_id': location_id,
                'product_id': product_id,
                'data': data,
                'vr_unitario_medio': vr_unitario_custo,
                'quantidade_entrada': quantidade_entrada,
                'quantidade_saida': quantidade_saida,
                'quantidade': quantidade,
                'vr_total': quantidade * vr_unitario_custo,
            }
            stock_saldo_pool.create(cr, 1, saldo)
            cr.commit()
            print(i, saldo)
            i += 1

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
                    from stock_move sm
                    where
                        (sm.create_date >= '2016-02-14'
                        or
                        sm.write_date >= '2016-02-14'
                        )
                    group by
                        sm.location_id

                    union all

                    select
                        sm.location_dest_id as local_id ,
                        cast(min(sm.date) as date) as data
                    from stock_move sm
                    where
                        (sm.create_date >= '2016-02-14'
                        or
                        sm.write_date >= '2016-02-14'
                        )
                    group by
                    sm.location_dest_id
                ) as a
                group by
                    a.local_id;"""

        return True

stock_saldo()
