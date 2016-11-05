# -*- coding: utf-8 -*-


from osv import fields, osv
from tools.safe_eval import safe_eval as eval
from edi import EDIMixin
import os
from pybrasil.base import tira_acentos
from pybrasil.valor.decimal import Decimal as D
from integra_rh.constantes_rh import *


FINAN_AGRUPAMENTO = (
    ('F', u'Funcionário'),
    ('E', u'Empresa/unidade'),
    ('C', u'CNPJ da empresa/unidade'),
    ('S', u'Sindicato'),
)


class hr_salary_rule(osv.Model, EDIMixin):
    _name = 'hr.salary.rule'
    _description = u'Rubrica de salário'
    _inherit = 'hr.salary.rule'
    _order = 'name'
    _rec_name = 'descricao'

    _columns = {
        #
        # Despesas
        #
        'finan_conta_despesa_id': fields.many2one('finan.conta', u'Conta financeira (cálculo normal/padrão)', select=True, ondelete='restrict'),
        'finan_conta_despesa_ferias_id': fields.many2one('finan.conta', u'Conta financeira (quando em cálculo de férias)', select=True, ondelete='restrict'),
        'finan_conta_despesa_rescisao_id': fields.many2one('finan.conta', u'Conta financeira (quando em cálculo de rescisão)', select=True, ondelete='restrict'),
        'finan_conta_despesa_13_id': fields.many2one('finan.conta', u'Conta financeira (quando em 13º)', select=True, ondelete='restrict'),

        #
        # Custos
        #
        'finan_conta_custo_id': fields.many2one('finan.conta', u'Conta financeira (cálculo normal/padrão)', select=True, ondelete='restrict'),
        'finan_conta_custo_ferias_id': fields.many2one('finan.conta', u'Conta financeira (quando em cálculo de férias)', select=True, ondelete='restrict'),
        'finan_conta_custo_rescisao_id': fields.many2one('finan.conta', u'Conta financeira (quando em cálculo de rescisão)', select=True, ondelete='restrict'),
        'finan_conta_custo_13_id': fields.many2one('finan.conta', u'Conta financeira (quando em 13º)', select=True, ondelete='restrict'),
        'finan_agrupamento': fields.selection(FINAN_AGRUPAMENTO, u'Agrupamento', select=True),

        #
        # Convênios
        #
        'partner_id': fields.many2one('res.partner', u'Convênio/beneficiário'),
    }

    _defaults = {
        'finan_agrupamento': 'C',
    }


hr_salary_rule()
