# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Caixa',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'Caixa',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'sped',
        'finan',
        'sped_sale',
        ],
    'update_xml': [
        'views/caixa_view.xml',
        'views/caixa_caixa_view.xml',
        'views/caixa_movimento_view.xml',
        'views/caixa_item_view.xml',
        'views/caixa_pagamento_view.xml',
        #'views/crm_lead_view.xml',
        #'views/crm_motivo_view.xml',
        ],
    #'init_xml': [
        #'data/sped.cnae.csv',
        #'data/res.country.state.csv',
        #'data/sped.pais.csv',
        #'data/sped.estado.csv',
        #'data/sped.municipio.csv',
        #],
    'installable': True,
    'application': False,
}
