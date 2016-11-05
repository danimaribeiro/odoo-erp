# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Eytan Magal - Personalizacao',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Eytan Magal - Personalizacao''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'project',
    ],
    'update_xml': [
        'views/project_project_view.xml',
        'views/project_task_view.xml',

        'wizard/bi_acoes_demoradas.xml',
    ],
    'installable': True,
    'application': False,
}
