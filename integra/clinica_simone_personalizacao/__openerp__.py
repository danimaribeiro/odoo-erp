# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Clinica Simone Peres',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalização Clinica Simone Peres''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'sale',
        'stock',
        'crm',
        'sped',
        'finan',
        'finan_contrato',
    ],
    'update_xml': [
        'views/finan_view.xml',
        'views/finan_contrato_view.xml',
        'views/turma_view.xml',
        'views/aula_view.xml',
        
        'wizards/finan_recibos_wizard.xml',        
  
    ],
    'installable': True,
    'application': False,
}
