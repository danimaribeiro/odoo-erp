# -*- coding: utf-8 -*-


from osv import fields, osv
from tools.safe_eval import safe_eval as eval
from edi import EDIMixin
import os
from pybrasil.base import tira_acentos
from pybrasil.valor.decimal import Decimal as D
from integra_rh.constantes_rh import *


class hr_salary_rule(osv.Model, EDIMixin):
    _name = 'hr.salary.rule'
    _description = u'Modelo de Integração Rubrica de Salário'
    _inherit = 'hr.salary.rule'
    _order = 'name'
    _rec_name = 'descricao'

    _columns = {
        #
        # Despesas
        #
        'modelo_folha_despesa_id': fields.many2one('sped.modelo_partida_dobrada', u'Folha normal', select=True, ondelete='restrict'),
        'modelo_folha_despesa_rescisao_id': fields.many2one('sped.modelo_partida_dobrada', u'Rescisão', select=True, ondelete='restrict'),
        'modelo_folha_despesa_ferias_id': fields.many2one('sped.modelo_partida_dobrada', u'Aviso de férias', select=True, ondelete='restrict'),
        'modelo_folha_despesa_13_id': fields.many2one('sped.modelo_partida_dobrada', u'Décimo terceiro', select=True, ondelete='restrict'),
        'modelo_folha_despesa_provisao_ferias_id': fields.many2one('sped.modelo_partida_dobrada', u'Provisão de férias', select=True, ondelete='restrict'),
        'modelo_folha_despesa_provisao_13_id': fields.many2one('sped.modelo_partida_dobrada', u'Provisão de décimo terceiro', select=True, ondelete='restrict'),

        #
        # Custos
        #
        'modelo_folha_custo_id': fields.many2one('sped.modelo_partida_dobrada', u'Folha normal', select=True, ondelete='restrict'),
        'modelo_folha_custo_rescisao_id': fields.many2one('sped.modelo_partida_dobrada', u'Rescisão', select=True, ondelete='restrict'),
        'modelo_folha_custo_ferias_id': fields.many2one('sped.modelo_partida_dobrada', u'Aviso de férias', select=True, ondelete='restrict'),
        'modelo_folha_custo_13_id': fields.many2one('sped.modelo_partida_dobrada', u'Décimo terceiro', select=True, ondelete='restrict'),
        'modelo_folha_custo_provisao_ferias_id': fields.many2one('sped.modelo_partida_dobrada', u'Provisão de férias', select=True, ondelete='restrict'),
        'modelo_folha_custo_provisao_13_id': fields.many2one('sped.modelo_partida_dobrada', u'Provisão de décimo terceiro', select=True, ondelete='restrict'),

    }

    _defaults = {

    }


hr_salary_rule()
