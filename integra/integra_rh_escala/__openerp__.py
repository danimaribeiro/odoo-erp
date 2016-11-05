# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - RH - Escalas e turnos',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_payroll',
        #'hr_holidays',
        'integra_rh',
        'finan_contrato',
        #'integra_partner',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - RH''',
    'init_xml': [
        #'data/hr.cbo.csv',
        #'data/res.bank.csv',
    ],
    'update_xml': [
        'views/hr_escalas_view.xml',
        #'views/hr_escala_view.xml',
        'views/hr_horario_contratual_view.xml',
        'views/hr_jornada_view.xml',
        'views/hr_turno_view.xml',
        'views/hr_turno_calendario_view.xml',
        'views/hr_funcionario_calendario_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
