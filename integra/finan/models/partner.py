# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


STORE_DEBIT_CREDIT = {
    'finan.lancamento': (
        lambda lanc_pool, cr, uid, ids, context={}: [lanc_obj.partner_id.id if lanc_obj.partner_id else False for lanc_obj in lanc_pool.browse(cr, uid, ids)],
        ['valor', 'situacao', 'provisionado'],
        10  #  Prioridade
    ),
}


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    def __credit_debit_get(self, cr, uid, ids, nome_campo, arg, context=None):
        res = {}

        for id in ids:
            res[id] = D(0)

            sql = """
                select
                    sum(coalesce(l.valor_saldo)) as saldo

                from
                    finan_lancamento l

                where
                    l.tipo = '{tipo}'
                    and l.partner_id = {id}
                    and (l.provisionado is null or l.provisionado = False)
                    and l.situacao in ('Vencido', 'Vence hoje', 'A vencer');
            """

            filtro = {
                'id': id,
            }

            if nome_campo == 'credit':
                filtro['tipo'] = 'R'
            else:
                filtro['tipo'] = 'P'

            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) and len(dados[0]) and dados[0][0]:
                res[id] = D(dados[0][0])

        return res

    #def _credit_search(self, cr, uid, obj, name, args, context=None):
        #return self._asset_difference_search(cr, uid, obj, name, 'receivable', args, context=context)

    #def _debit_search(self, cr, uid, obj, name, args, context=None):
        #return self._asset_difference_search(cr, uid, obj, name, 'payable', args, context=context)

    _columns = {
        'finan_formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'account_payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'account_payment_term_ids': fields.many2many('account.payment.term','partner_payment_term','partner_id','account_payment_term', string=u'Condição de pagamento permitidas'),
        'restricao': fields.text(u'Restricão'),
        #'credit': fields.function(_credit_debit_get, fnct_search=_credit_search, string=u'Total a receber', multi='dc'),
        #'credit': fields.function(_credit_debit_get, string=u'Total a receber', multi='dc', store=STORE_DEBIT_CREDIT),
        #'debit': fields.function(_credit_debit_get, fnct_search=_debit_search, string=u'Total a pagar', multi='dc'),
        #'debit': fields.function(_credit_debit_get, string=u'Total a pagar', multi='dc', store=STORE_DEBIT_CREDIT),
    }


res_partner()
