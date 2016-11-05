# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Orçamentos',
    'version': '1.0',
    'depends': [
        'orcamento',
        'project',
        'project_long_term',
        'project_mrp',
        ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Orçamentos - integração com projetos''',
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
