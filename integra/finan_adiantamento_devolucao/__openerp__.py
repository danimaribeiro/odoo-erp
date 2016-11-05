# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Adiantamento e Devolucão',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Adiantamento e Devolucão.',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'product',
        'sped',
    ],
    'update_xml': [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        #'views/finan_transacao_transferencia_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
    ],
    
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
