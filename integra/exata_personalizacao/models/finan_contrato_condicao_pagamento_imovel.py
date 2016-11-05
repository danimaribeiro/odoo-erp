# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report


TIPO_TAXA = [
    ('0', u'Juros simples'),
    ('1', u'Juros compostos'),
    ('2', u'Tabela price'),

    #
    # Essa SACOC é só pra Exata, pelamordedeus
    #
    ('3', u'Tabela SACOC'),
]


class finan_contrato_condicao(osv.Model):
    _name = 'finan.contrato.condicao'
    _inherit = 'finan.contrato.condicao'

    _columns = {
        'tipo_taxa': fields.selection(TIPO_TAXA, string=u'Tipo de juros'),
    }


finan_contrato_condicao()
