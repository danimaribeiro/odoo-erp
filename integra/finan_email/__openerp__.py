# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Email vencidos',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Emails vencidos',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'finan_contrato',
        'email_template',
    ],
    'update_xml': [
        'views/finan_email.xml',
        'wizard/finan_acoes_demoradas.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
