# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'Integra - Patrimônio'.encode('utf-8'),
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'Customização do patrimônio',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'account_asset',
        'sped',
    ],
    'update_xml': [
        'views/asset_asset.xml',
        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_manual.xml',
        'views/sped_operacao.xml',

        'wizard/patrimonio_relatorio.xml',
        'wizard/patrimonio_relatorio_patrimonio.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
}
