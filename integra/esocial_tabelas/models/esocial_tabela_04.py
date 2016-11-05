# -*- coding: utf-8 -*-

from osv import orm, fields, osv
from sped.models.fields import CampoPorcentagem


class esocial_tabela_04(orm.Model):
    _name = 'esocial.tabela_04'
    _description = u'Código e Alícotas de Fpas/Terceiros'
    _order = 'codigo'
    _rec_name = 'codigo'

    _columns = {
        'codigo': fields.integer(u'Código FPAS', required=True, select=True),
        'descricao': fields.text(u'Situação do Contribuinte',size=40, required=True),
        'codigo_terceiros': fields.char(u'Código de terceiros', size=30, required=True, select=True),
        'aliquota': CampoPorcentagem(u'Alíquota em %', required=True, select=True),
    }


