# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Lançamento Unificado',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Lançamento Unificado',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'product',
        'sped',
    ],
    'update_xml': [
        'views/finan_lanc_unificado_receber.xml',
        'views/finan_lanc_unificado_pagar.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
