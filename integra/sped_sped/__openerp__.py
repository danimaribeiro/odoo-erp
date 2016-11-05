# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'SPED - escrituração',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Sistema Publico de Escrituracao Digital
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
    ],
    'update_xml': [
        'views/sped_view.xml',
        'views/sped_sped_fiscal.xml',
        'views/sped_sped_piscofins.xml',
    ],
    'installable': True,
    'application': False,
}
