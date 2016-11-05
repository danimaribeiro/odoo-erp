# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Prottege Personalizacao',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalização da Prottege''',    
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'finan',
    ],
    'update_xml': [
        'views/finan_transacao_transferencia_view.xml',        

    ],
    'test': [],
    'installable': True,
    'application': True,
}
