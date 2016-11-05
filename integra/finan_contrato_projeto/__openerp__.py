# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Contratos - Projetos',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro - Contratos - Projetos',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'finan_projeto',
        'finan_contrato',
        #'product',
        #'sped',
        #'hr',
        'project',
    ],
    'update_xml': [
        'views/finan_contrato_receber_view.xml',
        'views/finan_contrato_pagar_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
