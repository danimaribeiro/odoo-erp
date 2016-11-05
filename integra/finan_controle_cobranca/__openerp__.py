# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Controle de Cobranca',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Controle de Cobrança',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',               
    ],
    'update_xml': [
        'views/finan_controle_cobranca.xml',
        'views/finan_receber_view.xml',
        
        'wizard/finan_relatorio_controle_cobranca.xml',        
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
