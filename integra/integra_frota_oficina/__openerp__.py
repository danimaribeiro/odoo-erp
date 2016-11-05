# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'Integra - Frota - Manutenção e Oficinas',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Integra - Frota - Manutenção e Oficinas',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'integra_frota',
        'seguranca',
    ],
    'update_xml': [
        'views/frota_tipo_view.xml',
        'views/frota_modelo_view.xml',
        'views/frota_veiculo_view.xml',
        'views/frota_manutencao_view.xml',
        #'views/product_view.xml',
        #'views/sale_view.xml',
        #'views/sale_order_line_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
