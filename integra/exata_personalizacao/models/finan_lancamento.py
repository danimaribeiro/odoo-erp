# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from finan.models.finan_conta import TIPO_RECEITA_DESPESA
from finan.models.finan_lancamento import *


STORE_LIBERA_COMISSAO = {
    'finan.lancamento': (
        lambda self, cr, uid, ids, context={}: [lanc_obj.lancamento_comissao_receber_id.id if lanc_obj.lancamento_comissao_receber_id else False for lanc_obj in self.browse(cr, uid, ids)],
        ['situacao'],
        10  #  Prioridade
    ),
}

STORE_LIBERA_ADMINISTRACAO = {
    'finan.lancamento': (
        lambda self, cr, uid, ids, context={}: [lanc_obj.lancamento_recebimento_imovel_id.id if lanc_obj.lancamento_recebimento_imovel_id else False for lanc_obj in self.browse(cr, uid, ids)],
        ['situacao'],
        10  #  Prioridade
    ),
}


class finan_lancamento(orm.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    def _liberado_pagamento_administracao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids, context=context):
            res[lancamento_obj.id] = False

            if not lancamento_obj.lancamento_recebimento_imovel_id:
                continue

            if lancamento_obj.liberado_pagamento_administracao_gerente:
                res[lancamento_obj.id] = True
                continue

            if lancamento_obj.lancamento_recebimento_imovel_id.situacao in ('Quitado', 'Conciliado'):
                res[lancamento_obj.id] = True
                continue

        return res

    def _search_liberado_pagamento_administracao(self, cr, uid, lancamento_pool, texto, args, context={}):
        res = {}
       
        print(args[0])
        if args[0][1] == '=' and args[0][2] == False:
            busca = [
                ('lancamento_recebimento_imovel_id', '!=', False),
                ('liberado_pagamento_administracao_gerente', '=', False),
                '!', ('lancamento_recebimento_imovel_id.situacao', 'in', ('Quitado', 'Conciliado')),
            ]

        else:
            busca = [
                ('lancamento_recebimento_imovel_id', '!=', False),
                '|',
                ('liberado_pagamento_administracao_gerente', '!=', False),
                ('lancamento_recebimento_imovel_id.situacao', 'in', ('Quitado', 'Conciliado')),
            ]

        print(busca)

        lancamento_ids = lancamento_pool.search(cr, uid, busca)

        print(lancamento_ids)

        if len(lancamento_ids) == 0:
            return [('id', '=', False)]
        else:
            return  [('id', 'in', lancamento_ids)]

    def _liberado_pagamento_comissao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids, context=context):
            res[lancamento_obj.id] = False

            if not lancamento_obj.lancamento_comissao_receber_id:
                continue

            if lancamento_obj.liberado_pagamento_comissao_gerente:
                res[lancamento_obj.id] = True
                continue

            if lancamento_obj.lancamento_comissao_receber_id.situacao in ('Quitado', 'Conciliado'):
                res[lancamento_obj.id] = True
                continue

        return res

    def _search_liberado_pagamento_comissao(self, cr, uid, lancamento_pool, texto, args, context={}):
        res = {}

        
        print(args[0])
        if args[0][1] == '=' and args[0][2] == False:
            busca = [
                ('lancamento_comissao_receber_id', '!=', False),
                ('liberado_pagamento_comissao_gerente', '=', False),
                '!', ('lancamento_comissao_receber_id.situacao', 'in', ('Quitado', 'Conciliado')),
            ]

        else:
            busca = [
                ('lancamento_comissao_receber_id', '!=', False),
                '|',
                ('liberado_pagamento_comissao_gerente', '!=', False),
                ('lancamento_comissao_receber_id.situacao', 'in', ('Quitado', 'Conciliado')),
            ]

        print(busca)

        lancamento_ids = lancamento_pool.search(cr, uid, busca)

        print(lancamento_ids)

        if len(lancamento_ids) == 0:
            return [('id', '=', False)]
        else:
            return  [('id', 'in', lancamento_ids)]

    def _get_soma_pagamento(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        if nome_campo == 'valor_pago':
            nome_campo = 'valor_documento'
        elif nome_campo == 'total_juros':
            nome_campo = 'valor_juros'
        elif nome_campo == 'total_multa':
            nome_campo = 'valor_multa'
        elif nome_campo == 'total_desconto':
            nome_campo = 'valor_desconto'

        for lancamento_obj in self.browse(cr, uid, ids):
            if lancamento_obj.tipo not in [TIPO_LANCAMENTO_A_PAGAR, TIPO_LANCAMENTO_A_RECEBER, TIPO_LANCAMENTO_LOTE_PAGAMENTO, TIPO_LANCAMENTO_LOTE_RECEBIMENTO]:
                res[lancamento_obj.id] = D('0')
            else:
                soma = D('0')
                for pagamento_obj in lancamento_obj.pagamento_ids:
                    soma += D(str(getattr(pagamento_obj, 'valor_documento', 0)))

                soma = soma.quantize(D('0.01'))

                res[lancamento_obj.id] = soma

        return res

    _columns = {
        'valor_pago': fields.function(_get_soma_pagamento, type='float', string=u'Valor quitado', store=False, digits=(18, 2)),
        'tipo_conta': fields.selection(TIPO_RECEITA_DESPESA, u'Tipo', select=True),
        'lancamento_comissao_receber_id': fields.many2one('finan.lancamento', u'Comissão Receber', ondelete='cascade'),
        'liberado_pagamento_comissao': fields.function(_liberado_pagamento_comissao, string=u'Liberado pagamento de comissão?', method=True, type='boolean', store=False, fnct_search=_search_liberado_pagamento_comissao),
        'liberado_pagamento_comissao_gerente': fields.boolean(u'Liberar pagamento de comissão?'),
        'liberado_pagamento_administracao': fields.function(_liberado_pagamento_administracao, string=u'Liberado pagamento de administração?', method=True, type='boolean', store=False, fnct_search=_search_liberado_pagamento_administracao),
        'liberado_pagamento_administracao_gerente': fields.boolean(u'Liberar pagamento de administração?'),
    }

    def liberar_pagamento_comissao(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'liberado_pagamento_comissao_gerente': True})

    def liberar_pagamento_administracao(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'liberado_pagamento_administracao_gerente': True})

    def onchange_data_quitacao(self, cr, uid, ids, data_quitacao, data, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not (data_quitacao):
            return res

        if not data:
            valores['data'] = data_quitacao

        return res


finan_lancamento()


class finan_lancamento_rateio(osv.Model):
    _name = 'finan.lancamento.rateio'
    _inherit = 'finan.lancamento.rateio'

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', select=True, ondelete='set null'),
    }

finan_lancamento_rateio()


