# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Análise Gerencial',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Análise Gerencial.',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'product',
        'sped_base',
        'sped',
        'finan',
        
    ],
    'update_xml': [
        'views/finan_estrutura_dre.xml',        
        'views/finan_estrutura_analise_dre.xml',        
        'views/finan_balanco_gerencial.xml',        

        
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
