# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - DI Distribuidora',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalizacao DI Distribuidora
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'sped_base',
        'sped',
        'sale',
        'purchase',
        'sped_purchase',
        'integra_product',
        'finan',
        'sped_produto_numero_serie',
    ],
    'update_xml': [
        'views/purchase_order_view.xml',
        'views/servico_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/sale_order_line_view.xml',
        'views/res_users.xml',
        'views/pricelist.xml',
        'views/partner_view.xml',
        
        'wizards/finan_relatorio_comissao.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
}
