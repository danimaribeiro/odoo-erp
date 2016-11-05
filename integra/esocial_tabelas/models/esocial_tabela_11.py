# -*- coding: utf-8 -*-

from osv import orm, fields, osv
from sped.models.fields import CampoPorcentagem


class esocial_tabela_11(orm.Model):
    _name = 'esocial.tabela_11'
    _description = u'Aliquotas de Outras Entidades e Fundos'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'codigo': fields.integer(u'Código', required=True, select=True),
        'nome': fields.char(u'Sigla', size=30, required=True, select=True),
        'aliquota': CampoPorcentagem(u'Alíquota',required=True),
    }


