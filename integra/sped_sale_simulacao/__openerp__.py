# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED Vendas - simulacao de pedidos',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Simulacao nos pedidos de venda',
    'depends': ['base', 'sale', 'sped'],
    'update_xml' : [
        'views/sale_view.xml',
        'views/sale_line_view.xml',
    ],
    'installable': True,
    'application': False,
}
