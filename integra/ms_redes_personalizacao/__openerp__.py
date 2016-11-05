# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'MS Redes',
    'version': '1.0',
    'category': 'Integra',
    'description': u'MS Redes',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'crm',
        'sale_crm',
        'integra_rh',
        'construtora',
        'integra_frota',
        'sped_sale',
    ],
    'update_xml': [
        'views/crm_lead.xml',
        'views/project_orcamento.xml',
        'views/project_orcamento_planejamento.xml',
        'views/purchase_orcamento_item.xml',
        'views/project_task.xml',
        'views/project_orcamento_medicao.xml',

        'views/finan_transacao_transferencia_view.xml',
        'views/sale_order_line_view.xml',

    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

