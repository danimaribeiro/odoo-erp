# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Ordem dos prospectos no CRM',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Customização da ordem dos prospectos no CRM''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'crm',
        'sped_base',
        'sale',
        ],
    'update_xml': [
        'views/crm_lead_view.xml',
        'views/crm_motivo_view.xml',
        'views/crm_lead_report_view.xml',
        'views/sale_report_view.xml',
        ],
    #'init_xml': [
        #'data/sped.cnae.csv',
        #'data/res.country.state.csv',
        #'data/sped.pais.csv',
        #'data/sped.estado.csv',
        #'data/sped.municipio.csv',
        #],
    'test': [],
    'installable': True,
    'application': False,
}
