# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Solicitação Numerário',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro Numerário',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'construtora'
    ],
    'update_xml': [
        'views/finan_numerario.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
