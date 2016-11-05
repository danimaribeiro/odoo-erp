# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.valor.decimal import Decimal as D

REAIS_ID = 6


class finan_lancamento(orm.Model):
    _inherit = 'finan.lancamento'

    _columns = {
        'currency_id': fields.many2one('res.currency', u'Moeda/Índice de correção'),
        'valor_documento_moeda': fields.float(u'Valor na moeda/sem correção'),
    }

    def atualiza_cotacao_moeda(self, cr, uid, ids=[], context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        currency_pool = self.pool.get('res.currency')

        if ids:
            moeda_ids = lancamento_pool.search(cr, uid, [('tipo', 'in', ('P', 'R')), ('situacao', 'in', ('Vencido', 'Vence hoje', 'A vencer')), ('id', 'in', ids), ('currency_id', '!=', False)])
        else:
            moeda_ids = lancamento_pool.search(cr, uid, [('tipo', 'in', ('P', 'R')), ('situacao', 'in', ('Vencido', 'Vence hoje', 'A vencer')), ('currency_id', '!=', False)])

        for lancamento_obj in lancamento_pool.browse(cr, uid, moeda_ids):
            valor_novo = currency_pool.converte(cr, uid, REAIS_ID, lancamento_obj.currency_id.id, D(lancamento_obj.valor_documento_moeda or 0), data_base=lancamento_obj.data_documento)
            valor_saldo = lancamento_obj.valor_saldo + valor_novo - D(lancamento_obj.valor_documento or 0)
            cr.execute("update finan_lancamento set valor_documento = {valor}, valor_saldo = {valor_saldo} where id = {id};".format(id=lancamento_obj.id, valor=valor_novo, valor_saldo=valor_saldo))

        return True

    def create(self, cr, uid, dados, context={}):
        res = super(finan_lancamento, self).create(cr, uid, dados, context=context)
        self.pool.get('finan.lancamento').atualiza_cotacao_moeda(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_lancamento, self).write(cr, uid, ids, dados, context=context)

        self.pool.get('finan.lancamento').atualiza_cotacao_moeda(cr, uid, ids, context=context)

        return res

    def onchange_valor_documento_moeda(self, cr, uid, ids, currency_id, valor_documento_moeda, data_documento, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        valores['valor_documento'] = valor_documento_moeda

        if not currency_id:
            return res

        if not valor_documento_moeda:
            return res

        currency_pool = self.pool.get('res.currency')
        valor_novo = currency_pool.converte(cr, uid, REAIS_ID, currency_id, D(valor_documento_moeda or 0), data_base=data_documento)
        valor_novo = D(valor_novo or 0)
        valor_novo = valor_novo.quantize(D('0.01'))
        valores['valor_documento'] = valor_novo

        return res

    def acao_demorada_ajusta_situacao_juros(self, cr, uid, ids=[], context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        lancamento_pool.atualiza_cotacao_moeda(cr, uid, ids, context=context)

        return super(finan_lancamento, self).acao_demorada_ajusta_situacao_juros(cr, uid, ids, context=context)


finan_lancamento()
