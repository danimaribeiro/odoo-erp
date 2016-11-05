# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Importação Cartão Ponto',
    'version': '1.0',
    'depends': [
        'base',
        'sped_base',                
        'integra_rh',        
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra -  Importação Cartão Ponto''',
    'init_xml': [],
    'update_xml': [
        'views/hr_importacao_ponto.xml',        
    ],
    'installable': True,
    'active': False,
}
