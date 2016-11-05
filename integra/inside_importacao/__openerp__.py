# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Importacao INSIDE',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Importacao INSIDE''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'finan',
    ],
    'update_xml': [
        'views/importa_finan.xml',
    ],
    'installable': True,
    'application': False,
}
