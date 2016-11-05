# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - ASP',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalização ASP''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        'product',
        'sale',
        'stock',
        'sped',
        'sped_sale',
        'integra_product',
        'integra_sale',
        'finan_cheque',
        'sped_stock',
        'integra_assistencia_tecnica',
    ],
    'update_xml': [
        'views/sale_view.xml',
        'views/sale_order_line_view.xml',
        #'views/sped_documento_nfe_emitida.xml',
        'views/sped_user_operacao.xml',
        'views/importa_finan.xml',
        'views/stock_picking_out_view.xml',
        'views/purchase_order_view.xml',
        'views/crm_phonecall_view.xml',

        'views/finan_remessa_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_receber_form.xml',

        'wizards/relatorio_estoque_minimo.xml',
        'wizards/finan_boleto_wizard_view.xml',
        'wizards/relatorio_faturamento_direto_asp.xml',
        'wizards/finan_curva_abc_asp.xml',
        'wizards/relatorio_vendedor_produto_asp.xml',
        'wizards/relatorio_recolhimento_icms.xml',
        'wizards/relatorio_cliente_estado.xml',
    ],
    'installable': True,
    'application': False,
}
