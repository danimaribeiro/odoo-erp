# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from finan.models.finan_conta import TIPO_RECEITA_DESPESA


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
            res[lancamento_obj.id] = True

            if not lancamento_obj.lancamento_recebimento_imovel_id:
                continue

            if lancamento_obj.liberado_pagamento_administracao_gerente:
                continue

            if lancamento_obj.lancamento_recebimento_imovel_id.situacao not in ('Quitado', 'Conciliado'):
                res[lancamento_obj.id] = False

        return res

    def _liberado_pagamento_comissao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids, context=context):
            res[lancamento_obj.id] = True

            if not lancamento_obj.lancamento_comissao_receber_id:
                continue

            if lancamento_obj.liberado_pagamento_comissao_gerente:
                continue

            if lancamento_obj.lancamento_comissao_receber_id.situacao not in ('Quitado', 'Conciliado'):
                res[lancamento_obj.id] = False

        return res

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
        'lancamento_comissao_receber_id': fields.many2one('finan.lancamento', u'Comissão Receber', ondelete='restrict'),
        'liberado_pagamento_comissao': fields.function(_liberado_pagamento_comissao, string=u'Liberado pagamento de comissão?', method=True, type='boolean', store=False),
        'liberado_pagamento_comissao_gerente': fields.boolean(u'Liberar pagamento de comissão?'),
        'liberado_pagamento_administracao': fields.function(_liberado_pagamento_administracao, string=u'Liberado pagamento de administração?', method=True, type='boolean', store=False),
        'liberado_pagamento_administracao_gerente': fields.boolean(u'Liberar pagamento de administração?'),
    }

    def liberar_pagamento_comissao(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'liberado_pagamento_comissao_gerente': True})

    def liberar_pagamento_administracao(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'liberado_pagamento_administracao_gerente': True})


finan_lancamento()


