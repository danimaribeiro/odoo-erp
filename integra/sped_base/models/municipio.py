# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class Municipio(orm.Model):
    _name = 'sped.municipio'
    _description = u'Municípios e Distritos do Brasil - Código do IBGE, SIAFI e ANP'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            retorno[registro.id] = ''

            if registro.id != 0:
                if registro.nome:
                    retorno[registro.id] += registro.nome

                if registro.estado_id:
                    retorno[registro.id] += ' - ' + registro.estado_id.uf

                if registro.pais_id and registro.pais_id.nome != 'Brasil':
                    retorno[registro.id] += ' - ' + registro.pais_id.nome

                #retorno[registro.id] += ' - ' + registro.codigo_ibge_formatado

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('nome', 'ilike', texto),
            ('codigo_ibge', 'ilike', texto),
        ]

        return procura

    def _formata_codigo_ibge(self, codigo):
        if codigo:
            return codigo[:3] + '.' + codigo[3:6] + '-' + codigo[6] + '/' + codigo[7:]
        else:
            return ''

    def _codigo_ibge_formatado(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            retorno[registro.id] = self._formata_codigo_ibge(registro.codigo_ibge)

        return retorno

    _columns = {
        'codigo_ibge': fields.char(u'Código IBGE', size=11, required=True, select=True),
        'codigo_siafi': fields.char(u'Código SIAFI', size=5, select=True),
        'codigo_anp': fields.char(u'Código ANP', size=7),
        'nome': fields.char('Nome', size=80, required=True, select=True),
        'estado_id': fields.many2one('sped.estado', u'Estado', required=True, select=True),
        'estado': fields.related('estado_id', 'uf', type='char', string=u'Estado', store=True),
        'pais_id': fields.many2one('sped.pais', u'País', required=True, select=True),
        'descricao': fields.function(_descricao, string=u'Município', method=True, type='char', fnct_search=_procura_descricao),
        'codigo_ibge_formatado': fields.function(_codigo_ibge_formatado, method=True, type='char'),
        'ddd': fields.char('DDD', size=2),
        'cep_unico': fields.char(u'CEP único', size=8),
        }

    _rec_name = 'descricao'
    _order = 'nome'

    _sql_constraints = [
        ('codigo_ibge_unique', 'unique (codigo_ibge)',
            u'O código IBGE não pode se repetir!'),
        ('nome_estado_pais_unique', 'unique (nome, estado_id, pais_id)',
            u'O nome, estado e país não podem se repetir!'),
        ]

Municipio()