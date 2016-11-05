# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Empresas de Seguranca - Integracao MONI',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Empresas de Segurança - Integração MONI''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'seguranca',
        'finan_contrato',
    ],
    'update_xml': [
        'views/importa_moni.xml',
        'views/finan_contrato_receber_view.xml',
    ],
    'installable': True,
    'application': False,
}
