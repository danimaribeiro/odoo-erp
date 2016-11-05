# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Frota',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro - Frota',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan',
        'finan_contrato',
        'integra_frota'
    ],
    'update_xml': [
        'views/finan_centrocusto_view.xml',
        'views/frota_veiculo_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_documento_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
