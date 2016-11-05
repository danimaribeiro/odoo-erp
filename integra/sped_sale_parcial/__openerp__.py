# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED Vendas - faturamento parcial de pedidos',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Emissão de NF-e e NFS-e nos pedidos de venda',
    'depends': ['base', 'sale', 'sped', 'stock'],
    'update_xml' : [
        'wizard/sale_gera_nota.xml',
    ],
    'installable': True,
    'application': False,
}
