# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Escalas no RH',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'hr_timesheet',
        'sped_base',
        'project',
        #'integra_partner',
        #'stock',
        'product',
        ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Escalas no RH''',
    'init_xml': [],
    'update_xml': [
        #'security/ir.model.access.csv',
        'views/hr_escala_view.xml',
        'views/hr_timesheet_view.xml',
        #'views/product_view.xml',
        #'views/sale_order_line_view.xml',
        #'views/orcamento_locacao_view.xml',
        #'views/sale_view.xml',
        #'views/sale_dinamico_view.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
