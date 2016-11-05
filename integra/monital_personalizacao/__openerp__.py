# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Monital Personalizacao',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalização da Monital''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'seguranca',
        'finan',
        'finan_cheque',
        'finan_contrato',
    ],
    'update_xml': [
        'wizards/finan_relatorio_posicao_receber.xml',
    ],
    'test': [],
    'installable': True,
    'application': True,
}
