# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Empresas de Seguranca',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Empresas de Segurança''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'sale',
        'integra_sale',
        'integra_sale_kit_produto',
        'sped_sale',
        'finan',
        'integra_frota',
        'sped_finan',
        'integra_libreoffice',
    ],
    'update_xml': [
        'security/groups.xml',

        'views/integra_mobile.xml',

        'views/operacional_dashboard_view.xml',
        'views/operacional_view.xml',
        'views/sale_dashboard_view.xml',

        'views/finan_pagar_view.xml',
        'views/finan_receber_view.xml',

        'views/sale_agrupamento.xml',
        'views/res_partner_contato_view.xml',
        'views/product_view.xml',
        'views/product_pricelist.xml',

        'views/sale_etapa_prospecto.xml',
        'views/sale_etapa_orcamento.xml',
        'views/sale_etapa_ordem_servico.xml',

        'views/sale_tipo_os.xml',
        'views/sale_prioridade_os.xml',
        'views/sale_defeito_os.xml',

        'views/sale_canal.xml',
        'views/sale_categoria.xml',

        'views/crm_meeting_os_agenda_tecnico.xml',
        'views/crm_meeting_os_agenda_situacao.xml',
        'views/stock_move_os.xml',

        'views/sale_order_line_produto_view.xml',
        'views/sale_order_line_servico_view.xml',
        'views/sale_order_line_mensalidade_view.xml',

        'views/sale_prospecto_view.xml',
        'views/sale_prospecto_dashboard_view.xml',

        'views/sale_orcamento_view.xml',
        'views/sale_orcamento_dashboard_view.xml',

        'views/sale_ordem_servico_view.xml',
        'views/sale_ordem_servico_por_data_dashboard_view.xml',
        'views/sale_ordem_servico_por_etapa_dashboard_view.xml',

        'views/sale_orcamento_referencia_view.xml',

        'views/sale_modelo_os.xml',
        'views/sale_modelo_orcamento.xml',

        'views/finan_contrato_terceirizado_view.xml',
        'views/finan_contrato_receber_view.xml',

        'views/partner_view.xml',
        'views/finan_tipo_faturamento_view.xml',
        'views/finan_contrato_receber_view.xml',
        'views/finan_contrato_receber_novo_view.xml',

        'views/sped_documento_nfse_emitida.xml',

        'views/mail_server.xml',

        'wizards/sale_relatorio_os_data_tipo_orcamento_etapa.xml',
        'wizards/sale_relatorio_venda.xml',
        'wizards/finan_gera_nota.xml',
        'wizards/sale_gera_nota.xml',
    ],
    'installable': True,
    'application': False,
}
