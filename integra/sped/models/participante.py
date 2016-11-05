# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *


class Company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        #'cnae': fields.many2one('sped.cnae', u'CNAE principal'),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário'),
        'ambiente_nfe': fields.selection(AMBIENTE_NFE, u'Ambiente da NF-e'),
        'serie_producao': fields.char(u'Série em produção', size=3),
        'serie_homologacao': fields.char(u'Série em homologação', size=3),
        'tipo_emissao_nfe': fields.selection(TIPO_EMISSAO_NFE, u'Tipo de emissão da NF-e'),
        'serie_scan_producao': fields.char(u'Série emissão SCAN em produção', size=3),
        'serie_scan_homologacao': fields.char(u'Série emissão SCAN em homologação', size=3),
        'al_icms_sn_id': fields.many2one('sped.aliquotaicmssn', u'ICMS SN'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária padrão'),
        }

    _defaults = {
        'regime_tributario': REGIME_TRIBUTARIO_SIMPLES,
        'ambiente_nfe': AMBIENTE_NFE_HOMOLOGACAO,
        'serie_producao': '1',
        'serie_homologacao': '100',
        'tipo_emissao_nfe': TIPO_EMISSAO_NFE_NORMAL,
        'serie_scan_producao': '900',
        'serie_scan_homologacao': '999',
        }

Company()
