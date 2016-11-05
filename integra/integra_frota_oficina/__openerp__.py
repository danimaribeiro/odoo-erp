# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Oficina - Integra',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle de Oficinas INTEGRA',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'integra_frota',
        'product',
        'orcamento',
        'sale',
    ],
    #'data': [
        #'data/frota.tipo.csv',
    #],
    'update_xml': [
        'views/frota_modelo_view.xml',
        'views/frota_veiculo_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/sale_order_line_view.xml',
        #'views/frota_servico_view.xml',
        #'views/frota_odometro_view.xml',
        #'views/frota_os_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
