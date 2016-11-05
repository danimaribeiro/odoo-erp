# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Analise Economica',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Análise Econômica Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'finan',
    ],
    'update_xml': [
        'views/economica_view.xml',
        'views/econo_conta_view.xml',
        'views/econo_analise_view.xml',
        'views/econo_conferencia_view.xml',
        'views/econo_analise_unificada_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
