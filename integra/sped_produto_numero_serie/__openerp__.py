# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Numero de serie nos produtos',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Sistema Publico de Escrituracao Digital
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
        'product',
        'sped_product',
        'stock',
        'sped_stock',
    ],
    'update_xml': [
        'views/product_view.xml',
        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_manual.xml',
        'views/operacao_nfe_emitida.xml',
        'views/partner_view.xml',
        'views/numero_serie_view.xml',
    ],
    'installable': True,
    'application': False,
}
