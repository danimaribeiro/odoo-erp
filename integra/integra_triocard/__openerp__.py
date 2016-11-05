# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Trio Card',
    'version': '1.0',
    'depends': [
        'base',
        'sped_base',    
        'integra_rh',
        
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Trio Card''',
    'init_xml': [],
    'update_xml': [
                   
        'views/hr_triocard.xml',
        
    ],
    'installable': True,
    'active': False,
}
