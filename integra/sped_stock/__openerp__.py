# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Estoque',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Sistema Publico de Escrituracao Digital
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
        'stock',
        'purchase',
        'finan',
    ],
    'update_xml': [
        #'views/operacao_view.xml',
        'views/operacao_nfe_emitida.xml',
        'views/sped_operacao_item_simples.xml',
        'views/sped_operacao_item.xml',
        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_manual.xml',
        'views/stock_location.xml',
        'views/product.xml',

        'views/stock_picking_in.xml',
        'views/stock_picking_internal.xml',
        'views/stock_inventory.xml',
        'views/stock_inventory_line.xml',
        'views/stock_saldo.xml',

        'wizards/estoque_acoes_demoradas.xml',
        'wizards/estoque_view.xml',
        'wizards/estoque_relatorio_movimento_estoque.xml',
        'wizards/estoque_relatorio_posicao_estoque.xml',
        'wizards/estoque_relatorio_listagem_preco_fornecedor.xml',
        'wizards/stock_rastreabilidade_wizard.xml',
        'wizards/estoque_relatorio_panoramico.xml',
        'wizards/relatorio_tabela_preco.xml',
        'wizards/estoque_relatorio_custo_unidade_local.xml',
        'wizards/estoque_relatorio_preco_quantidade.xml',

    ],
    'installable': True,
    'application': False,
}
