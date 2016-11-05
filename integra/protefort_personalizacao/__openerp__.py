# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Protefort',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Campos necessários da Protefort
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        #'sped_base',
        'sale',
        'stock',
        'sped_sale',
        'integra_rh',
    ],
    'update_xml': [
        #'wizard/hr_relatorio_sindicato.xml',
        #'wizard/hr_relatorio_listagem_ferias_vencidas.xml',

    ],
    'test': [],
    'installable': True,
    'application': True,
}
