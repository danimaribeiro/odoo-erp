# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Cheques',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Administraçaõ de Cheques.',
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
        'security/ir.model.access.csv',

        'views/finan_cheque.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_cheque_deposito.xml',
        'views/finan_cheque_estorno.xml',

        'wizard/finan_relatorio_cheque.xml',
        'wizard/finan_relatorio_movimentacao_versao_2.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
