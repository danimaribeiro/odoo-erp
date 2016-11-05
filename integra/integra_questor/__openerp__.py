# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Integração - Questor',
    'version': '1.0',
    'depends': [
        'base',
        'sped',
        'finan',
        'sped_contabilidade',
        'sped_sped',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Integração - Questor''',
    'init_xml': [],
    'update_xml': [
        'views/questor_view.xml',
        'views/exportacao_contabil.xml',
        'views/exportacao_fiscal.xml',
        'views/exportacao_xml.xml',
        'views/sped_sped_fiscal.xml',
    ],
    'installable': True,
    'active': False,
}
