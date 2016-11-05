# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Modelos LibreOffice - integração com RH',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Modelos de Impressos no LibreOffice para o RH',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'integra_libreoffice',
        'hr',
        'integra_rh',
    ],
    'update_xml': [
        'views/hr_job_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_payroll_structure_view.xml',
        'views/hr_rescisao_view.xml',
        'views/hr_ferias_view.xml',
        'views/hr_reajuste_cargo_view.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
