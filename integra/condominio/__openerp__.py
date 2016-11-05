# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Condominio',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Administração de condomínios',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'finan',
        'finan_contrato',
        'project',
        'construtora',
        'integra_frota',
        'crm',
    ],
    'update_xml': [
        'views/condominio_view.xml',
        'views/project_project.xml',
        'views/partner.xml',
        'views/partner_address.xml',
        'views/frota_veiculo.xml',
        'views/imovel_condominio_unidade.xml',
        'views/condominio_despesa.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

