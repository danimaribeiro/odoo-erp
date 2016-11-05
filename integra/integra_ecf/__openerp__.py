# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - ECF',
    'version': '1.0',
    'depends': [
        'base',
        'sale',
        'sped',
        #'orcamento',
        'sped_finan',
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - ECF''',
    'init_xml': [],
    'update_xml': [
        #'views/integra_ecf.xml',
        'views/operacao_ecf_emitido.xml',
        'views/operacao_ecf_recebido.xml',

        'views/sped_documento_ecf_emitido.xml',
        'views/sped_documento_ecf_recebido.xml',

        'views/finan_sped_documento_ecf_emitido.xml',
        'views/finan_sped_documento_ecf_recebido.xml',

        'views/company_view.xml',
    ],
    'installable': True,
    'active': False,
}
