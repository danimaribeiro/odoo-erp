# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'RH - Avaliações e campanhas',
    'version': '1.0',
    'category': 'Integra',
    'description': u'RH - Avaliações e campanhas',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'hr',
        'integra_rh',
    ],
    'update_xml': [
        'views/rh_view.xml',
        'views/rh_tipoavaliacao_view.xml',
        'views/rh_avaliacao_view.xml',
        'views/rh_avaliacaoitem_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
