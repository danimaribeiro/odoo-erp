# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Consulta CEP',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Consulta CEP''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'sale',
        'crm',
        'sped_base',
        #'integra_partner',
        'integra_crm',
        #'construtora',
    ],
    'update_xml': [
        'views/partner_view.xml',
        'views/crm_lead_view.xml',
        'views/hr_employee_view.xml',
        #'views/imovel_apartamento.xml',
        #'views/imovel_terreno.xml',
        #'views/imovel_sala_comercial.xml',
        #'views/imovel_predio.xml',
        #'views/imovel_loja.xml',
        #'views/imovel_galpao.xml',
        #'views/imovel_chacara.xml',
    ],
    'installable': True,
    'application': False,
}
