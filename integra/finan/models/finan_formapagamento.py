# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import fields, osv


class finan_formapagamento(osv.Model):
    _name = 'finan.formapagamento'
    _description = 'Formas de pagamento'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Forma de pagamento', size=60, required=True, select=True),
        'conciliado': fields.boolean(u'Registrar já conciliado?'),
        'cliente_negativado': fields.boolean(u'Evita quitação de boletos para clientes negativados?'),
        'exige_numero': fields.boolean(u'Exige número doc.?'),
        'payment_term_ids': fields.one2many('account.payment.term', 'formapagamento_id', u'Condições de pagamento'),
    }

    _defaults = {
        'conciliado': False,
        'exige_numero': True,
    }

    def _cria_id(self, cr, uid, nome):
        forma_ids = self.search(cr, uid, [('nome', 'in', [nome.lower(), nome.upper()])])

        if forma_ids:
            return forma_ids[0]

        dados = {
            'nome': nome.upper(),
        }
        forma_id = self.create(cr, uid, dados)
        return forma_id

    def id_credito_cobranca(self, cr, uid):
        return self._cria_id(cr, uid, 'CRÉD. COBRANÇA')


finan_formapagamento()
