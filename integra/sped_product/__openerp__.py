# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - produto',
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
        'sped_base',
        'product',
    ],
    'update_xml': [
        'views/product_view.xml',
        'views/sped_fiscal_view.xml',
        'views/aliquota_view.xml',
        'views/familiatributaria_view.xml',
        'views/ncm_view.xml',
        'views/cest_view.xml',
        'views/servico_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
    'data': [
        'data/sped.aliquotaicmssn.csv',
        'data/sped.aliquotaicmsproprio.csv',
        'data/sped.aliquotaiss.csv',
        'data/sped.aliquotaipi.csv',
        'data/sped.aliquotapiscofins.csv',
 #       'data/sped.ncm.csv',
        'data/sped.servico.csv',
    ],
    'test': [],
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
    'installable': True,
    'application': True,
}
