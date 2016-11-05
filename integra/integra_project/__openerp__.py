# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Projetos',
    'version': '1.0',
    'depends': [
        'project',
        ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Projetos''',
    'init_xml': [
        'groups.xml',
    ],
    'update_xml': [
        'views/project_task_integra_view.xml',
        'views/project_task_clientes_view.xml',
        'views/project_os_view.xml',
        'views/project_project_view.xml',

        'wizard/project_task_relatorio_wizard.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
