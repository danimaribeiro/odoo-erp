# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Frota - Integra',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Automotivo INTEGRA',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'sped_base',
        'integra_frota',
        'sale',
        'integra_product',
        'orcamento',
        'integra_caixa',
    ],
    'images': [
        'images/frota.png',
        'images/frota-hover.png'
    ],
    'update_xml': [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        #'views/frota_view.xml',
        #'views/frota_tipo_view.xml',
        #'views/frota_modelo_view.xml',
        'views/frota_veiculo_view.xml',
        #'views/frota_servico_view.xml',
        #'views/frota_odometro_view.xml',
        #'views/frota_os_view.xml',
        'views/product_view.xml',
        'views/partner_view.xml',
        'views/sale_view.xml',
        'views/caixa_item_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
