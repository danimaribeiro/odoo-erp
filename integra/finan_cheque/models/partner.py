# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


STORE_DEBIT_CREDIT = {
    'finan.lancamento': (
        lambda lanc_pool, cr, uid, ids, context={}: [lanc_obj.partner_id.id for lanc_obj in lanc_pool.browse(cr, uid, lanc_pool.search(cr, uid, [('provisionado', '=', False), ('tipo', 'in', ['PR', 'PP', 'R', 'P']), ('id', 'in', ids)]))],
        ['valor', 'situacao', 'provisionado'],
        10  #  Prioridade
    ),
    'finan.cheque': (
        lambda cheque_pool, cr, uid, ids, context={}: [cheque_obj.partner_id.id for lanc_obj in cheque_pool.browse(cr, uid, ids)],
        ['sitacao_cheque'],
        20  #  Prioridade
    )
}


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    def __credit_debit_get(self, cr, uid, ids, nome_campo, arg, context={}):
        res = super(res_partner, self)._credit_debit_get(cr, uid, ids, nome_campo, arg, context=context)

        if nome_campo == 'credit':
            for id in ids:
                cheques = D(0)

                sql = """
                    select
                        sum(coalesce(l.valor)) as saldo

                    from
                        finan_cheque l

                    where
                        l.partner_id = {id}
                        and l.situacao_cheque != 'CP';
                """

                filtro = {
                    'id': id,
                }

                sql = sql.format(**filtro)
                cr.execute(sql)
                dados = cr.fetchall()

                if len(dados) and len(dados[0]) and dados[0][0]:
                    res[id] += D(dados[0][0])

        return res

    #def _credit_search(self, cr, uid, obj, name, args, context=None):
        #return self._asset_difference_search(cr, uid, obj, name, 'receivable', args, context=context)

    #def _debit_search(self, cr, uid, obj, name, args, context=None):
        #return self._asset_difference_search(cr, uid, obj, name, 'payable', args, context=context)

    _columns = {
        #'credit': fields.function(_credit_debit_get, fnct_search=_credit_search, string=u'Total a receber', multi='dc'),
        #'credit': fields.function(_credit_debit_get, string=u'Total a receber', multi='dc', store=STORE_DEBIT_CREDIT),
        #'debit': fields.function(_credit_debit_get, fnct_search=_debit_search, string=u'Total a pagar', multi='dc'),
        #'debit': fields.function(_credit_debit_get, string=u'Total a pagar', multi='dc', store=STORE_DEBIT_CREDIT),
    }


res_partner()
