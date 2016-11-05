# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Comissao Vendas',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Comissão nas vendas',
    'depends': [
        'base',
        'sped_sale',
        'crm'
    ],
    'update_xml' : [
        'views/crm_case_section.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    'application': False,
}
