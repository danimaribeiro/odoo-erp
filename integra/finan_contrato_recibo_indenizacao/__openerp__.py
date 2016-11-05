# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Contrato Recibo Indernizacao',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Financeiro - Contrato Recibo Indernização.',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',        
        'finan',
        'sped_finan',
        'finan_contrato',
        'finan_modelo_lancamento',
    ],
    'update_xml': [
        'views/finan_contrato_recibo_indenizacao.xml',                
                        
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
