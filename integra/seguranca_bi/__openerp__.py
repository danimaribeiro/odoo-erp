# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Empresas de Seguranca',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Empresas de Segurança - BI''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'seguranca',
    ],
    'update_xml': [
        'wizard/seguranca_bi_acoes_demoradas.xml',
    ],
    'installable': True,
    'application': False,
}
