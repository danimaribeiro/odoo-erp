# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class rh_tipoavaliacao(orm.Model):
    _name = 'rh.tipoavaliacao'
    _description = 'Tipo de avaliação'
    _order = 'nome'
    _rec_name = 'nome'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            carteira_obj = self.browse(cr, uid, id)
            if carteira_obj.res_partner_bank_id:
                texto = carteira_obj.res_partner_bank_id.nome or ''
            else:
                texto = ''

            texto += ' - ' + carteira_obj.carteira or ''

            res += [(id, texto)]

        return dict(res)

    _columns = {
        'nome': fields.char(u'Nome', size=60),
        'tipo': fields.selection((('+', 'Positiva'), ('-', 'Negativa')), u'Tipo'),
        'pontos': fields.integer(u'Pontos'),
        'tratamento': fields.selection((('S', 'Simples'), ('P', 'Projeto'), ('C', 'Correção')), u'Tratamento'),
    }

    _defaults = {
        'tipo': '-',
        'tratamento': 'S',
        'pontos': 0,
    }

    def ajusta_pontos(self, cr, uid):
        cr.execute("update rh_tipoavaliacao set pontos = abs(pontos) * -1 where tipo = '-';")

    def create(self, cr, uid, dados, context=None):
        res = super(rh_tipoavaliacao, self).create(cr, uid, dados, context)
        self.ajusta_pontos(cr, uid)
        return res

    def write(self, cr, uid, ids, dados, context=None):
        res = super(rh_tipoavaliacao, self).write(cr, uid, ids, dados, context)
        self.ajusta_pontos(cr, uid)
        return res


rh_tipoavaliacao()
