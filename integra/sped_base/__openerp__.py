# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - base',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Sistema Publico de Escrituracao Digital
    Dados como CNPJ/CPF e inscrição estadual dos participantes/partners
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'account',
        'crm',
        #'project',
    ],
    'update_xml': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sped_fiscal_view.xml',
        'views/partner_view.xml',
        'views/res_partner_address_view.xml',
        'views/cnae_view.xml',
        'views/sped_user_fone.xml',
        'views/account_payment_term.xml',
    ],
    'init_xml': [
        #'data/sped.cnae.csv',
        #'data/res.country.state.csv',
        #'data/sped.pais.csv',
        #'data/sped.estado.csv',
        #'data/sped.municipio.csv',
    ],
    'test': [],
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
    'installable': True,
    'application': True,
}
