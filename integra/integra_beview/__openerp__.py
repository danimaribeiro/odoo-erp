# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Beview',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Integra - Beview',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
        'finan',        
        'construtora'
    ],
    'update_xml': [
        'views/imovel_terreno.xml',        
        
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
