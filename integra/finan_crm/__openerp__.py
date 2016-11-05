# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - CRM',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro BRASIL',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'crm',
    ],
    'update_xml': [
        'wizard/crm_lancamento_to_phonecall_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
