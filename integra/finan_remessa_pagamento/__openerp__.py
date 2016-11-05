# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Remessa de pagamentos',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro BRASIL',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'finan',
    ],
    'update_xml': [
        'views/finan_remessa_pagamento_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
