# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Projetos',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro - Projetos',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'project',
    ],
    'update_xml': [
        'views/finan_centrocusto_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}