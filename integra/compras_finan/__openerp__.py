# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Compras - Financeiro',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Compras - Financeiro''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'sped_purchase',
        'finan',
    ],
    'update_xml': [
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'application': False,
}
