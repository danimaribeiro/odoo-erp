# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - NFSE Manual',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u''' NFSE Manual
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',        
        'sped_base',
        'sped',
        'sale',        

    ],
    'update_xml': [
        'views/sped_documento_nfse_emitida.xml',    
        'views/retorno_nfse_manual.xml',    
        'wizard/lote_nfse_manual_wizard.xml',    
        
    ],
    'test': [],
    'installable': True,
    'application': False,
}
