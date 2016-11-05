# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from caixa_movimento_base import caixa_movimento_base
from pybrasil.data import parse_datetime, formata_data, data_hora_horario_brasilia
import tools


class caixa_movimento_pagamento(orm.Model):
    _name = 'caixa.movimento_pagamento'
    _auto = False

    _columns = {
        'movimento_id': fields.many2one('caixa.movimento', u'Movimento'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', select=True),
        'valor': fields.float(u'Valor'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'caixa_movimento_pagamento')
        cr.execute("""
            create or replace view caixa_movimento_pagamento as (
                select
                    p.movimento_id as id,
                    p.movimento_id,
                    p.formapagamento_id,
                    sum(coalesce(p.valor, 0)) as valor

                from
                    caixa_pagamento p

                group by
                    p.movimento_id,
                    p.formapagamento_id

                order by
                    p.movimento_id,
                    p.formapagamento_id
            )
        """)


caixa_movimento_pagamento()
