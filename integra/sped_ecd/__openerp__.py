# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED-ECD',
    'version': '1.0',
    'category': 'SPED-ECD',
    'description': u'''
    SPED - ECD- Escrituração Contábil Digital 
    ''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'account',
        'account_asset',
        'sped_base',
        'sped',
        'finan',
        'integra_rh',
        'sped_contabilidade',
        'sped_sped'
    ],
    'update_xml': [
        'views/ecd_view.xml',
        'views/ecd_finan_conta.xml',
        #'views/ecd_centrocusto.xml',
        'views/ecd_lancamento_contabil.xml',
        'views/ecd_partida_lancamento.xml',
        'views/ecd_lote_contabilidade.xml',
        'views/ecd_plano_conta.xml',
        'views/ecd_estrutura_dre.xml',
        'views/company_view.xml',
        'views/ecd_periodo.xml',
        'views/ecd_recomposicao_saldo.xml',            
        'views/ecd_estrutura_analise_dre.xml',
        'views/ecd_saldo_anterior.xml',
        'views/hr_payslip_view.xml',
        'views/account_asset_view.xml',
        'views/ecd_estrutura_analise_dre_gerencial.xml',
        'views/ecd_saldo_consulta.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'views/finan_lote_pagar_view.xml',
        'views/finan_lote_receber_view.xml',
        'views/sped_sped_ecd.xml',
        
        'views/sped_documento_nfe_emitida.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfse_emitida.xml',
        'views/sped_documento_nfse_recebida.xml',
        
        'wizards/sped_ecd_relatorio_diario.xml',
        'wizards/sped_ecd_relatorio_razao.xml',
        'wizards/sped_ecd_relatorio_balancete.xml',
        'wizards/sped_ecd_relatorio_balanco.xml',
        'wizards/sped_ecd_relatorio_razao_centrocusto.xml',
        #'wizards/sped_ecd_relatorio_dre.xml',
        
    ],
    'init_xml': [        
    ],
    'test': [],
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
    'installable': True,
    'application': True,
}
