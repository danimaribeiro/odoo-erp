# -*- coding: utf-8 -*-

from osv import fields, osv


class cliente_unidade(osv.osv):
    _name = "cliente.unidade"
    _description = u'Empresa e unidade'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'nome_completo'
    _order = 'nome_completo'
    _rec_name = 'nome_completo'
    
    def monta_nome(self, cr, uid, id):
        cliente_obj = self.browse(cr, uid, id)

        nome = cliente_obj.nome

        if cliente_obj.parent_id:
            nome = self.monta_nome(cr, uid, cliente_obj.parent_id.id) + u' / ' + nome

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
            '|',
            ('nome_completo', 'ilike', texto),
        ]

        return procura

    _columns = {
        'parent_id': fields.many2one('cliente.unidade', u'Cliente', select=True, ondelete='restrict'),
        'child_ids': fields.one2many('cliente.unidade', 'parent_id', string=u'Contas filhas'),
        'parent_left': fields.integer(u'Conta à esquerda', select=True),
        'parent_right': fields.integer(u'Conta a direita', select=True),
        
        'nome': fields.char(u'Nome', size=64, required=True, select=True),
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Descrição', fnct_search=_procura_nome, store=True, select=True),
        
        'project_ids': fields.many2many('project.project', 'cliente_unidade_projeto', 'unidade_id', 'project_id', u'Projetos'),
     }


cliente_unidade()
