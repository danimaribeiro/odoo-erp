# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class CNAE(orm.Model):
    _description = u'CNAE'
    _name = 'sped.cnae'

    def monta_nome(self, cr, uid, id):
        cnae_obj = self.browse(cr, uid, id)

        nome = cnae_obj.codigo[:4] + '-' + cnae_obj.codigo[4] + '/' + cnae_obj.codigo[5:]
        nome += ' - ' + cnae_obj.descricao

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
            '|',
            ('codigo', 'ilike', texto),
            ('descricao', 'ilike', texto)
        ]

        return procura

    _columns = {
        'codigo': fields.char('Código', size=7, required=True, select=True),
        'descricao': fields.char('Descrição', size=255, required=True, select=True),
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome, store=False),
    }

    _rec_name = 'nome'
    _order = 'codigo'

    _sql_constraints = [
        ('codigo_unique', 'unique (codigo)', u'O código não pode se repetir!'),
        #('descricao_unique', 'unique (descricao)',
        #u'A descrição não pode se repetir!'),
        ]

CNAE()
