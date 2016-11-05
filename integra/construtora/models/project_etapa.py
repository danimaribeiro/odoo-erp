# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv



class project_etapa(orm.Model):
    _name = 'project.etapa'
    _description = u'Etapa do orçamento do projeto'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'nome_completo'
    _order = 'nome_completo'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        nome = conta_obj.nome

        if conta_obj.parent_id:
            nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for obj in self.browse(cr, uid, ids):
            res.append((obj.id, self.monta_nome(cr, uid, obj.id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('nome_completo', 'ilike', texto),
        ]

        return procura

    _columns = {
        'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', store=True, select=True),
        'parent_id': fields.many2one('project.etapa', u'Etapa mãe', select=True, ondelete='cascade'),
        'etapas_filhas_ids': fields.one2many('project.etapa', 'parent_id', string=u'Etapas filhas'),
        'sintetica': fields.boolean(u'Sintética', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=True),
        'parent_right': fields.integer(u'Conta a direita', select=True),
    }

    def _verifica_recursiva(self, cr, uid, ids, context={}):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from project_etapa where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar etapas recursivas', ['parent_id']),
    ]

    def child_get(self, cr, uid, ids):
        return [ids]


project_etapa()
