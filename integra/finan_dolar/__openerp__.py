# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - atualizacao da cotacao do Dolar do BACEN',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro BRASIL',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
    ],
    'update_xml': [
        'views/res_currency.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_pagamento_view.xml',

        'wizard/finan_acoes_demoradas.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
