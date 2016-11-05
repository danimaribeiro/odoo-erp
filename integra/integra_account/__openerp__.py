# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Contabilidade',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Customização de campos da contabilidade''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'account',
    ],
    'update_xml': [
        'views/account_account.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
}
