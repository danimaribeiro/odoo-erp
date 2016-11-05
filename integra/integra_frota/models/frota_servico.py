# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_servico(osv.Model):
    _name = 'frota.servico'
    _description = 'Serviços e atividades'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'nome'
    _order = 'parent_left'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        obj = self.browse(cr, uid, id)

        nome = obj.nome

        if obj.parent_id:
            nome = self.monta_nome(cr, uid, obj.parent_id.id) + ' / ' + nome

        return nome

    def get_nome(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_nome(cr, uid, id))]

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_nome(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('nome', 'ilike', texto),
        ]

        return procura

    _columns = {
        'nome': fields.char(u'Nome', size=60, required=True, select=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome),
        'parent_id': fields.many2one('frota.servico', u'Serviço/atividade pai', select=True, ondelete='cascade'),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'ignora_km': fields.boolean(u'Ignonar este serviço na contagem de km'),
        'manutencao_periodica': fields.boolean(u'Serviço de manutenção periódica?'),
        'custo_ativo': fields.boolean(u'Serviço compõe relatório de custo com ativo?'),
    }

    _defaults = {
        'custo_ativo': True,
    }

    def _verifica_recursiva(self, cr, uid, ids, context=None):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from finan_centrocusto where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar centros de custo recursivos', ['parent_id'])
    ]

    _sql_constraints = [
        ('nome_unique', 'unique(nome)',
            u'Não é permitido repetir um mesmo serviço!'),
    ]



frota_servico()
