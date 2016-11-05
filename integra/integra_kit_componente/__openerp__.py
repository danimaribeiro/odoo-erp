# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra Vendas - kit de produtos (construtora)',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Integra Pedidos de Venda',
    'depends': [
        'base',
        'sped_product',
        'construtora',
    ],
    'update_xml' : [
        'views/product_view.xml',
        'views/project_orcamento.xml',
        'views/project_orcamento_medicao.xml',
    ],
    'installable': True,
    'application': False,
}
