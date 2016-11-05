# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Base Sociedade',
    'version': '1.0',
    'category': 'SPED BASE',
    'description': u'''Cadastro de Sociedade''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'account',
        'sped_base',
    ],
    'update_xml': [
        'views/partner_view.xml',
        
    ],
    'init_xml': [
        
    ],
    'test': [],
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
    'installable': True,
    'application': True,
}
