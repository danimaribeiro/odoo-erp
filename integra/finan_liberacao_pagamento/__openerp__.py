# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Liberacao de pagamento',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Liberacao de pagamento',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'sped_base',
        'finan',
        'purchase',
        'compras_finan',
    ],
    'update_xml': [
        'views/account_payment_term.xml',
        'views/finan_pagar_view.xml',
        'wizard/finan_libera_pagamento_wizard.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
