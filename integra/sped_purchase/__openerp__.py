# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Compras',
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
        'sped_base',
        'sped',
        'purchase',
        'compras',
    ],
    'update_xml': [
        #'views/operacao_nfe_emitida.xml',
        #'views/sped_operacao_item_simples.xml',
        #'views/sped_operacao_item.xml',
        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_manual.xml',
        'views/purchase_order_line_view.xml',
        'views/purchase_order_view.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/sped_documento_nf_recebida.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfe_recebida_manual.xml',
    ],
    'installable': True,
    'application': False,
}
