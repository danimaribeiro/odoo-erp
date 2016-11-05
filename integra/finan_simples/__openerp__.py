# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - simples',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro BRASIL',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'email_template',
        'mail',
        'finan',
        'finan_contrato',
        'sped',
    ],
    'update_xml': [
        'security/groups.xml',

        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_transacao_view.xml',
        'views/sped_documento_nfse_emitida.xml',

    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
}
