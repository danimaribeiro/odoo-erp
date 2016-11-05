# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - RH - Financeiro',
    'version': '1.0',
    'depends': [
        'base',
        'integra_rh',
        'integra_rh_caged',
        'finan',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - RH''',
    'update_xml': [
        'views/hr_contract_view.xml',
        'views/finan_remessa_folha_view.xml',
        'views/hr_salary_rule.xml',
        'views/hr_sefip.xml',
        'views/finan_centrocusto_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_receber_view.xml',
        #'views/res_partner_bank.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
