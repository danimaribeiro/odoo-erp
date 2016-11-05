# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - SESMT',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'integra_rh',
        'web_wysiwyg',
        'product'
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - SESMT''',
    'init_xml': [],
    'images': [
        'images/sesmt.png',
        'images/sesmt-hover.png'
    ],
    'update_xml': [
        'views/sesmt_view.xml',
        'views/sesmt_comprometimento_saude.xml',
        'views/sesmt_dano_saude.xml',
        'views/sesmt_fonte_geradora.xml',
        'views/sesmt_medida_controle.xml',
        'views/sesmt_meio_propagacao.xml',
        'views/sesmt_recomendacao.xml',
        'views/sesmt_restricao.xml',
        'views/sesmt_risco_ergonomico.xml',
        'views/sesmt_risco_acidente.xml',
        'views/sesmt_epi.xml',
        'views/sesmt_treinamento.xml',
        'views/sesmt_fator_risco.xml',
        'views/hr_job.xml',
        'views/product_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
