# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Pesquisa Fluxo de Caixa',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Pesquisa Fluxo de Caixa',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',        
    ],
    'update_xml': [
        
        #'views/finan_extrato_view.xml',
        'views/finan_lancamento_fluxo_caixa_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
