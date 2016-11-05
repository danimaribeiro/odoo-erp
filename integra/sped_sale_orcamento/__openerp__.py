# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'SPED Vendas - Orçamento',
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
        'sped_sale',
        'orcamento',
    ],
    'update_xml' : [
        'views/sale_view.xml',
    ],
    'installable': True,
    'application': False,
}
