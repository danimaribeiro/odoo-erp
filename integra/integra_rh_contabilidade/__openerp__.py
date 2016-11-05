# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - RH - Contabilidade',
    'version': '1.0',
    'depends': [
        'base',
        'integra_rh',
        'finan',
        'sped_contabilidade',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Contabilidade''',
    'update_xml': [
        'views/hr_salary_rule.xml',
        #'views/hr_rescisao_view.xml',
        #'views/hr_ferias_view.xml',
        #'views/hr_payslip_view.xml',
        'views/sped_modelo_partida_dobrada.xml',
        'views/sped_modelo_partida_dobrada_rh.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
