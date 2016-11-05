# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED Pedido de transferência',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Pedido de transferência entre unidades/filiais',
    'depends': [
        'sped',
        'stock',
        'patrimonial_personalizacao',
    ],
    'update_xml' : [
        'views/stock_picking_pedido_transferencia.xml',
        'views/stock_operacao_view.xml',
    ],
    'installable': True,
    'application': False,
}
