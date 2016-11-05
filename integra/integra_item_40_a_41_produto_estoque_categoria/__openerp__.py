# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - item 40 a 41 - Estoque de produtos por categoria',
    'version': '1.0',
    'depends': [
        'base',
        'stock'
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - item 40 a 41 - Estoque de produtos por categoria''',
    'init_xml': [],
    'update_xml': [
        'report.xml',
        'wizard/wiz_stock_prod_cate_view.xml',
        'stock_by_category.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
