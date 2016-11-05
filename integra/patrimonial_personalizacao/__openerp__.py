# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Patrimonial',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Campos necessários da Patrimonial
    ''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'base',
        #'sped_base',
        'sale',
        'stock',
        'orcamento',
        'sped_sale',
        'sped_finan',
        'finan_contrato_checklist',
        'sped_ecd',
        'integra_patrimonio',
        #'sped',
        #'sped_pedido_transferencia',
    ],
    'update_xml': [
        'security/groups.xml',
        'views/company_view.xml',
        'views/partner_view.xml',
        'views/rota_view.xml',
        'views/taxa_administrativa_view.xml',
        #'views/sale_view.xml',
        #'views/user_date_scheduler.xml'
        'views/orcamento_view.xml',
        'views/crm_lead_view.xml',
        'views/crm_claim_view.xml',
        'views/orcamento_locacao_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_picking_out_view.xml',
        'views/stock_operacao_view.xml',
        'views/stock_location.xml',
        'views/stock_picking_pedido_transferencia.xml',

        'views/hr_rescisao_view.xml',
        'views/hr_job_view.xml',

        'views/product_category_view.xml',
        'views/sale_order_line.xml',

        'views/finan_conferencia_fluxo_view.xml',

        'views/finan_contrato_receber_view.xml',
        'views/stock_picking_inventario_cliente.xml',
        'views/finan_pagamento_view.xml',
        'views/finan_contrato_reajuste_view.xml',

        #'views/stock_inventory_view.xml',
        'wizard/hr_relatorio_listagem_seguros_seguranca.xml',
        'wizard/hr_relatorio_listagem_seguros_telma.xml',
        'wizard/hr_relatorio_funcionario_ativos_sexo_categoria.xml',
        'wizard/hr_relatorio_quadro_lotacao.xml',
        'wizard/relatorio_estoque_minimo.xml',
        'wizard/relatorio_estoque_orderm_entrega.xml',

        'wizard/relatorio_movimentacao_operacao.xml',
        'wizard/relatorio_orcamento_comissao.xml',
        'wizard/finan_curva_abc_cliente.xml',
        'wizard/recalcula_holerites.xml',
        'wizard/finan_cobranca_juridica.xml',
        'wizard/sale_libera_faturamento_wizard.xml',
        'wizard/finan_analise_mercado.xml',
        'wizard/sped_ecd_relatorio_razao_financeiro.xml',
        'wizard/sped_ecd_relatorio_balancete_financeiro.xml',
        'wizard/finan_relatorio_fluxo_caixa_analitico.xml',
        'wizard/finan_relatorio_fluxo_caixa_sintetico.xml',
        'wizard/finan_relatorio_receber.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'wizard/finan_relatorio_clientes_duvidosos.xml',
        'wizard/finan_relatorio_contratos_suspensos.xml',


        'wizard/crm_relatorio_atendimento.xml',
        'wizard/listagem_produto_estoque.xml',

        'views/sale_report_view.xml',
        'views/importa_finan.xml',

        'views/product_view.xml',
        'views/sped_operacao.xml',
        'views/purchase_order.xml',

        'views/sale_orcamento_complementar.xml',
        'views/sale_orcamento_complementar_mao_obra.xml',

        'views/hr_contract_view.xml',
        'views/vendedor_meta.xml',
        'views/vendedor_meta_corporativo.xml',
        'views/comercial_meta_faixa.xml',
        'views/comercial_meta_escala.xml',
        'views/finan_transacao_transferencia_view.xml',
        'views/finan_transacao_entrada_view.xml',
        'views/finan_transacao_saida_view.xml',
        'views/finan_conta_view.xml',

        'views/instalacao_equipe.xml',
        'views/crm_meeting_instalacao.xml',
        'wizard/finan_acompanhamento_instalacao.xml',

        #
        # Incluindo rateios nas telas de documentos recebidos no Fiscal
        #
        'views/sped_documento_agua_recebida.xml',
        'views/sped_documento_comunicacao_recebida.xml',
        'views/sped_documento_cte_recebido.xml',
        'views/sped_documento_energia_recebida.xml',
        'views/sped_documento_gas_recebida.xml',
        #'views/sped_documento_nfe_recebida_manual.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nf_recebida.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/sped_documento_telecomunicacao_recebida.xml',

        #
        # Checklist da proposta
        #
        'views/checklist_contrato_item.xml',

        #
        # DRE da Patrimonial
        #
        'views/ecd_estrutura_gerencial_1.xml',
        #'views/ecd_estrutura_analise_gerencial_1.xml',

        'views/account_asset_view.xml',

        'views/mail_server.xml',
    ],
    'test': [],
    'installable': True,
    'application': True,
}
