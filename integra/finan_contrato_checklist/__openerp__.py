# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Checklist do contrato',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Construção civil',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'finan_contrato',
        'project',
        'sale',
    ],
    'update_xml': [
        'views/checklist_contrato.xml',
        'views/checklist_contrato_item.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

