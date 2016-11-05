# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Balkon',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Campos necessários da Balkon
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'crm',
        'finan_contrato',
        'hr',
        'sale',
    ],
    'update_xml': [
        'views/crm_lead_view.xml',
        'views/crm_opportunity_view.xml',
        'views/hr_department_view.xml',
        'views/sale_order_view.xml',
        'views/res_partner_view.xml',
        'wizards/relatorio_crm_oportunidades.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
}
