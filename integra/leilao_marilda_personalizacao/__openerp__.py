# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Leilão',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Calcula preço de custo e venda por peso do produto''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'sale',
        'integra_product',
        'sped_sale',
    ],
    'update_xml': [
        'groups.xml',

        'views/integra_product_view.xml',
        'views/sale_view.xml',
        'views/sale_order_line_view.xml',
        'views/partner_view.xml',
        'views/data_hora_leilao_view.xml',
        'views/midia_leilao_view.xml',

        'wizard/leilao_relatorio_fechamento_leilao.xml',
    ],
    'installable': True,
    'application': False,
}
