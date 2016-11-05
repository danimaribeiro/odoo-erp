# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Ajustes para o idioma, moeda e tradução para o Brasil',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Ajustes no idioma, moeda e tradução para o Brasil''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        ],
    'update_xml': [],
    'init_xml': [
        'res.currency.csv',
        'res.lang.csv',
        ],
    'test': [],
    'installable': True,
    'application': False,
}
