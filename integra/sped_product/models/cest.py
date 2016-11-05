# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
import time
from sped.models.fields import CampoPorcentagem


class sped_cest(orm.Model):
    _description = u'CEST'
    _name = 'sped.cest'
    _rec_name = 'nome'
    _order = 'codigo'


    def monta_nome(self, cr, uid, id):
        cest_obj = self.browse(cr, uid, id)

        nome = cest_obj.codigo[:2] + '.' + cest_obj.codigo[2:5] + '.' + cest_obj.codigo[5:]

        nome += ' - ' + cest_obj.descricao[:60]

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
            ('codigo', 'ilike', texto),
        ]

        return procura

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Código CEST'),
        'codigo': fields.char(u'Código', size=7, required=True, select=True),
        'descricao': fields.char(u'Descrição', size=1500, required=True),
        'ncm_ids': fields.many2many('sped.ncm', 'sped_ncm_cest', 'cest_id', 'ncm_id', u'NCMs'),
    }

    _defaults = {
        'codigo': '',
        'descricao': '',
    }

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', u'O código não pode se repetir!'),
    ]


sped_cest()
