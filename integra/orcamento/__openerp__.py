# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Orçamentos',
    'version': '1.0',
    'depends': [
        'base',
        'sale',
        'sale_crm',
        'sped_stock',
        'product',
        ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Orçamentos em vendas''',
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',

        'wizard/crm_make_sale_view.xml',
        #'wizard/crm_saleorder_to_phonecall_view.xml',
        #'wizard/sale_nota_wizard.xml',

        'views/orcamento_categoria_view.xml',
        'views/product_view.xml',
        'views/sale_order_line_view.xml',
        'views/orcamento_locacao_view.xml',
        'views/sale_view.xml',
        'views/sale_dinamico_view.xml',
        'views/orcamento_comissao_view.xml',
        'views/orcamento_comissao_venda.xml',
        'views/orcamento_comissao_locacao.xml',
        #'views/orcamento_grupo_aprovacao.xml',
        'views/partner.xml',
        'views/lead.xml',

        ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
