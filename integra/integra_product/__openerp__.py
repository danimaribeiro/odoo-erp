# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Campos dos produtos',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Customização de campos no cadastro de produto''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'account',
        'finan',
    ],
    'update_xml': [
        'views/product_view.xml',
        'views/product_category_view.xml',
        'views/account_product_view.xml',
        'views/pricelist.xml',
    ],
    #'init_xml': [
        #'data/sped.cnae.csv',
        #'data/res.country.state.csv',
        #'data/sped.pais.csv',
        #'data/sped.estado.csv',
        #'data/sped.municipio.csv',
        #],
    'test': [],
    'installable': True,
    'application': True,
}
