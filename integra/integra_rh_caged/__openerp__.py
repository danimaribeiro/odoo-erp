# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - RH - CAGED',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'integra_rh',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - RH - CAGED''',
    'init_xml': [],
    'update_xml': [
        'views/hr_caged.xml',
        'views/hr_esocial_qualificacao.xml',
        'views/hr_sefip.xml',
        'views/hr_grrf.xml',
        #'views/hr_grrf_simulacao.xml',
        'views/hr_rais.xml',
        'views/hr_dirf.xml',
        #'views/hr_seguro_desemprego.xml',
    ],
    'installable': True,
    'active': False,
}
