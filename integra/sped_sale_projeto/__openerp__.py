# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integracao do Projeto em Vendas',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Comissão nas vendas',
    'depends': [
        'base',
        'sped_sale',
        'project',
        'crm',
    ],
    'update_xml' : [
        'views/sale_view.xml',
        'views/crm_lead_view.xml',
    ],
    'installable': True,
    'application': False,
}
