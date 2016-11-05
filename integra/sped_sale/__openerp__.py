# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED Vendas',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Emissão de NF-e e NFS-e nos pedidos de venda',
    'depends': [
        'base',
        'sale',
        'sped',
        'finan',
        'integra_product',
    ],
    'update_xml' : [
        'views/sl_view.xml',
        'views/sale_order_line_view.xml',
        'views/sale_order_line_produto_view.xml',
        'views/sale_view.xml',
        'views/consulta_itens_pedido.xml',
        #'views/product_view.xml',
        'wizard/sale_gera_nota.xml',
    ],
    'installable': True,
    'application': False,
}
