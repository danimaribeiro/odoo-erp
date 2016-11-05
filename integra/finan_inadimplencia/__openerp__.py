# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Inadimplencia',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro BRASIL',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'integra_libreoffice',
    ],
    'update_xml': [
        'views/finan_inadimplencia.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
