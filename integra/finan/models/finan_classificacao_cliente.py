# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


SQL_AJUSTA_CLASSIFICACAO_CLIENTE = """
update res_partner p set
    classificacao_cliente_id = (
        select
            c.id

        from
            finan_classificacao_cliente c

        where
            coalesce(c.dias_atraso, 0) >=
                coalesce((
                    select
                        max(case
                            when l.data_quitacao <= l.data_vencimento then 0
                            when l.data_quitacao > l.data_vencimento then l.data_quitacao - l.data_vencimento
                            when l.data_quitacao is null then current_date - l.data_vencimento
                            when l.data <= l.data_vencimento then 0
                            when l.data_baixa <= l.data_vencimento then 0
                            else 0
                        end) as dias

                    from
                        finan_lancamento l
                    where
                        l.partner_id = p.id
                        and l.tipo = 'R'
                        and l.data_vencimento < current_date
                ), 0)

        order by
            coalesce(c.dias_atraso, 0)

        limit 1
    )
"""


class finan_classificacao_cliente(orm.Model):
    _name = 'finan.classificacao.cliente'
    _description = u'Classificação dos clientes'

    _columns = {
        'nome': fields.char(u'Nome', size=30, required=True, select=True),
        'dias_atraso': fields.integer(u'Máximo de dias de atraso na quitação'),
        'peso': fields.float(u'Peso'),
    }


finan_classificacao_cliente()


class res_partner(orm.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'

    _columns = {
        'classificacao_cliente_id': fields.many2one('finan.classificacao.cliente', u'Classificação financeira'),
    }


res_partner()
