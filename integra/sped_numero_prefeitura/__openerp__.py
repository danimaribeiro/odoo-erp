# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - NFSE - Número Prefeitura',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''NFSE - Número Prefeitura'
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',        
        'sped_base',
        'sped',        
    ],
    'update_xml': [  
        'views/sped_documento_nfse_emitida.xml',         
        
    ],
    'test': [],
    'installable': True,
    'application': False,
}
