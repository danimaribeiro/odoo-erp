# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


#TIPO = (
    #('AUTO', u'Automóvel'),
    #('UTIL', u'Utilitário'),
    #('MOTO', u'Motocicleta'),
    #('CAMI', u'Caminhão/rebocador'),
    #('ONIB', u'Ônibus/micro-ônibus'),
    #('IMPL', u'Implemento rodoviário'),
#)


class frota_modelo(osv.Model):
    _name = 'frota.modelo'
    _description = 'Modelos de veículo'
    _order = 'marca, modelo'
    _rec_name = 'nome'

    def monta_nome(self, cr, uid, id):
        obj = self.browse(cr, uid, id)

        nome = obj.marca or ''
        nome += ' / '
        nome += obj.modelo or ''

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
            '|', ('marca', 'ilike', texto),
            ('modelo', 'ilike', texto),
        ]

        return procura

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome, size=100),
        'marca': fields.char(u'Marca', size=30),
        'modelo': fields.char(u'Modelo', size=30),
        'tipo_id': fields.many2one('frota.tipo', 'Tipo'),
    }

    #_defaults = {
        #'tipo': 'AUTO',
    #}


frota_modelo()
