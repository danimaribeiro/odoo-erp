# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - consulta CNPJ',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Sistema Publico de Escrituracao Digital
    Consulta CNPJ na Receita Federal
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'sped_base',
        ],
    'update_xml': [
        'wiz_consulta_cnpj_view.xml',
        'participante_view.xml',
        'partner_view.xml',
        'ir.model.access.csv',
        ],
    'test': [],
    'installable': True,
    'application': True,
}
