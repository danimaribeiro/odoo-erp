# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Modelo Lançamento ',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Modelo Lançamento.',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',        
        'finan',
        'sped_finan',
        'finan_contrato',
    ],
    'update_xml': [
        'views/finan_modelo_receber_view.xml',
        'views/finan_modelo_pagar_view.xml',        
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',        
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
