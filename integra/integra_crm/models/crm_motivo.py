# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


# from datetime import datetime
from osv import fields, osv


class crm_motivo(osv.Model):
    _description = u'motivo'
    _name = 'crm.motivo'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'codigo, nome'
    _order = 'parent_left'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        nome = conta_obj.nome

        if conta_obj.parent_id:
            nome = self.monta_nome(cr, uid, conta_obj.parent_id.id) + ' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res.append((id, self.monta_nome(cr, uid, id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('nome', 'like', texto),
        ]

        return procura

    def monta_codigo(self, cr, uid, id):
        conta_obj = self.browse(cr, uid, id)

        tamanho_maximo = 1

        if conta_obj.parent_id:
            cr.execute("select max(codigo) from crm_motivo where parent_id = " + str(conta_obj.parent_id.id) + ';')
            res = cr.fetchall()[0][0]
            tamanho_maximo = len(str(res))

        codigo = str(conta_obj.codigo).zfill(tamanho_maximo)

        if conta_obj.parent_id:
            codigo = self.monta_codigo(cr, uid, conta_obj.parent_id.id) + '.' + codigo

        return codigo

    def get_codigo(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_codigo(cr, uid, id))]

        return res

    def _get_codigo_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_codigo(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'nome': fields.char(u'Descrição', size=60, required=True, select=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome),
        'parent_id': fields.many2one('crm.motivo', u'Motivo pai', select=True, ondelete='cascade'),
        'sintetico': fields.boolean(u'Sintético', select=True),
        'parent_left': fields.integer(u'Conta à esquerda', select=1),
        'parent_right': fields.integer(u'Conta a direita', select=1),
        'codigo': fields.integer(u'Código no grupo', select=True),
        'codigo_completo': fields.function(_get_codigo_funcao, type='char', string=u'Código completo'),
        'motivo_filhos_ids': fields.one2many('crm.motivo', 'parent_id', string='Motivos filhos'),
    }

    _defaults = {
        'sintetico': False,
    }

    def _verifica_recursiva(self, cr, uid, ids, context=None):
        nivel_recursao = 100

        while len(ids):
            cr.execute('select distinct parent_id from crm_motivo where id in %s', (tuple(ids),))

            ids = filter(None, map(lambda x: x[0], cr.fetchall()))

            if not nivel_recursao:
                return False

            nivel_recursao -= 1

        return True

    _constraints = [
        (_verifica_recursiva, u'Erro! Não é possível criar centros de custo recursivos', ['parent_id'])
    ]

    def recalcula_ordem_parent_left_parent_right(self, cr, uid, ids, context):
        for obj in self.browse(cr, uid, self.search(cr, uid, [])):
            self.write(cr, uid, obj.id, {'nome': obj.nome + ' '})

        for obj in self.browse(cr, uid, self.search(cr, uid, [])):
            self.write(cr, uid, obj.id, {'nome': obj.nome.strip()})


crm_motivo()
