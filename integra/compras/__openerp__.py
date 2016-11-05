# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Compras',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Compras - pedido de compras',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'purchase',
    ],
    'update_xml': [
     'wizard/crm_purchaseorder_to_phonecall_view.xml',
     'wizard/purchase_nota_wizard.xml',

     'views/purchase_order.xml',
     'views/purchase_order_line.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

