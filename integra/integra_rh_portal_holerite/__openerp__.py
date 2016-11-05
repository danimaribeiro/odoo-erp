# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - RH - Portal do Funcionario',
    'version': '1.0',
    'depends': [
        'hr_payroll',
        'integra_rh',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - RH''',
    'init_xml': [
    ],
    'update_xml': [
        'views/payslip_view.xml',
        #'views/hr_decimo_terceiro.xml',
        #'views/hr_aviso_ferias_view.xml',
        #'views/hr_rescisao.xml',
        
        'views/payslip_portal.xml',
        'views/hr_lote_portal.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
