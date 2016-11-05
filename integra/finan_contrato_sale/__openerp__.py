# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Financeiro - Contratos - Vendas',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle Financeiro - Contratos - Vendas',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'finan_contrato',
        'sped_sale',
    ],
    'update_xml': [
        'views/finan_contrato_receber_view.xml',
        'views/finan_contrato_alteracao_vendedor_view.xml',

        'wizard/finan_relatorio_analise_contratos_comercial.xml',
        'wizard/finan_relatorio_evolucao_receita.xml',
        #'wizard/finan_relatorio_aging_receber_grafico.xml',
        'wizard/finan_relatorio_analise_faturamento.xml',
        'wizard/finan_relatorio_curva_abc_contratos.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
