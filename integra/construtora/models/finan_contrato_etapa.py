# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora

TIPO_ETAPA = [
    ('C',u'Corretor'),
    ('A', u'Agenciador'),
    ('G', u'Gerente'),
    ('J', u'Jurídico'),
]


class finan_contrato_etapa(osv.Model):
    _description = u'Finan Contrato Etapa'
    _name = 'finan.contrato.etapa'
    _rec_name = 'nome'
    _order = 'id'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for os_obj in self.browse(cr, uid, ids):
            res[os_obj.id] = str(os_obj.id).zfill(4)

        return res

    def _filtro(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for etapa_obj in self.browse(cr, uid, ids):
            retorno = u''
            for etapa_seguinte_obj in etapa_obj.etapa_seguinte_ids:
                retorno += etapa_seguinte_obj.codigo + '|'

            res[etapa_obj.id] = retorno

        return res


    _columns = {
        'codigo': fields.function(_codigo, type='char', method=True, string=u'Código', size=20, store=False, select=True),
        'filtro_etapa': fields.function(_filtro, type='char', method=True, string=u'Código', size=280, store=True, select=True),
        'nome': fields.char(u'Nome', size=180),
        'etapa_seguinte_ids': fields.many2many('finan.contrato.etapa','finan_contrato_etapa_seguinte', 'etapa_id', 'etapa_seguinte_id', u'Etapa Seguinte'),
        'tipo_proxima_etapa': fields.selection(TIPO_ETAPA, u'Próxima Etapa', select=True),
        #'gera_orcamento': fields.boolean(u'Gera orçamento'),
        'tipo_negociacao': fields.selection([('P', u'Proposta'), ('C', u'Contraproposta')], u'Tipo de negociação'),
        'tipo': fields.selection([('P', u'Proposta'), ('F', u'Análise financeiro'), ('J', u'Análise jurídico'), ('R', u'Contrato')], u'Tipo'),
    }

    _defaults = {
        'tipo_proxima_etapa': 'C',
        'tipo': 'P',
    }

    def verifica_etapa(self, cr, uid, ids, vals, context=None):
        if 'etapa_seguinte_ids' not in vals or not vals['etapa_seguinte_ids']:
            return
        etapa_seguinte_ids = vals['etapa_seguinte_ids']

        for id in ids:

            if id in etapa_seguinte_ids[0][2]:
                raise osv.except_osv(u'Inválido !', u'Etapa seguinte deve ser diferente da atual')

    def create(self, cr, uid, vals, context={}):
        res = super(finan_contrato_etapa, self).create(cr, uid, vals, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        self.verifica_etapa(cr, uid, ids, vals)
        res = super(finan_contrato_etapa, self).write(cr, uid, ids, vals, context)

        return res

finan_contrato_etapa()

