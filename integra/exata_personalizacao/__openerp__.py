# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra - Exata',
    'version': '1.0',
    'category': 'ERP Integra',
    'description': u'''Personalização Exata''',
    'author': 'ERP Integra',
    'maintainer': 'ERP Integra',
    'website': 'http://www.erpintegra.com.br',
    'depends': [
        'sped',
        'finan',
        'construtora',
        'finan_modelo_lancamento',
    ],
    'update_xml': [
        'views/partner_view.xml',
        'views/purchase_order.xml',
        'views/purchase_order_abastecimento.xml',
        'views/finan_pagar_view.xml',
        'views/finan_receber_view.xml',
        'views/project_view.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/sped_documento_ecf_recebido.xml',
        'views/finan_contrato_receber_view.xml',
        'views/finan_contrato_proposta.xml',

        'views/imovel_casa.xml',
        'views/imovel_apartamento.xml',
        'views/imovel_terreno.xml',
        'views/imovel_chacara.xml',

        'views/cadastro_view.xml',

        'views/crm_lead_prospecto.xml',

        'wizard/finan_relatorio_pagar.xml',
        'wizard/finan_relatorio_receber.xml',
        'wizard/finan_relatorio_fluxo_caixa_analitico.xml',
        'wizard/finan_fechamento_caixa_wizard.xml',
        'wizard/sped_ecd_relatorio_razao_financeiro.xml',
        'wizard/finan_relatorio_segurado.xml',
        'wizard/finan_relatorio_demonstrativo_parcela.xml',
        'wizard/finan_recibos_wizard.xml',
        'wizard/finan_relatorio_lote_recibos.xml',
        'wizard/sale_relatorio_imovel_projeto.xml',

    ],
    'installable': True,
    'application': False,
}
