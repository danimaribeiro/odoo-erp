# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Manufatura',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Integra - Manufatura''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'mrp',        
        'sped_base',
    ],
    'update_xml': [
        'views/lista_materiais_view.xml',     
    ],
    'installable': True,
    'application': False,
}
