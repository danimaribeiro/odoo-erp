# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.data import agora, formata_data


class crm_lead(osv.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    _columns = {
        'jah_teve_contato': fields.boolean('O senhor/a senhora já teve contato com algum corretor da nossa empresa?'),
        'hr_department_id': fields.many2one('hr.department', u'Setor'),
        'outro_motivo': fields.char(u'Qual', size=60),
        'outro_canal': fields.char(u'Qual', size=60),
        'corretor_id': fields.many2one('res.partner', u'Corretor'),
        'corretor_repassado_id': fields.many2one('res.partner', u'Repassado para'),
        'corretor_plantao': fields.boolean(u'Corretor de plantão'),

        #
        # Cacacas da ficha de atendimento, totalmente desnecessárias...
        #
        'procura_avaliacao': fields.boolean(u'Avaliação'),
        'procura_morar': fields.boolean(u'Morar'),
        'procura_investir': fields.boolean(u'Investir'),
        'procura_locacao': fields.boolean(u'Locação'),
        'procura_revenda': fields.boolean(u'Revenda'),
        'procura_outro': fields.boolean(u'Outro'),
        'procura_qual': fields.char(u'Qual', size=60),
        'procura_obs': fields.text(u'Obs'),

        'procura_filhos': fields.boolean(u'Tem filhos?'),
        'procura_filhos_quantidade': fields.integer(u'Quantos?'),
        'procura_animais_estimacao': fields.boolean(u'Tem animais de estimação?'),
        'procura_animais_estimacao_quantidade': fields.integer(u'Quantos?'),

        'procura_localizacao': fields.char(u'Qual localização gostaria', size=120),
        'procura_valor': fields.float(u'Valor aproximado que pretende investir', digits=(18, 2)),
        'procura_forma_pagamento': fields.text(u'Forma de pagamento'),

        'atendimento_obs': fields.text(u'Obs'),
    }

    _defaults = {
        'name': lambda self, cr, uid, context={}: formata_data(agora(), '%d/%m/%Y %H:%M:%s'),
    }


crm_lead()
