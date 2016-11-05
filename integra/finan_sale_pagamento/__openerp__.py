# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Pagamentos Pedido de Venda',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Pagamento Pedido de Venda.''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'sale',
        'stock',
        'sped',
        'sped_sale',
        'integra_product',
        'integra_sale',
        'finan_cheque',
    ],
    'update_xml': [
        'views/sale_view.xml',
     
    ],
    'installable': True,
    'application': False,
}
