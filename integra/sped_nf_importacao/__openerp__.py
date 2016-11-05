# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Importação',
    'version': '1.0',
    'description': u'Sped - Importação NF-e',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',        
    ],
    'update_xml': [
        'views/sped_documento_item.xml',
        #'views/sped_documento_nfe_recebida.xml',
        #'views/sped_documento_nfse_emitida.xml',
        #'views/sped_documento_nfse_recebida.xml',        
    ],
    'installable': True,
    'application': False,
}
