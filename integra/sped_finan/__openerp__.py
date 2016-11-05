# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Financeiro',
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
        'finan',
        'finan_contrato',
        'purchase',
    ],
    'update_xml': [
        'views/operacao_view.xml',
        'views/sped_documento_duplicata.xml',
        'views/sped_documento_nfe_emitida.xml',
        'views/sped_documento_nfse_emitida.xml',
        'views/sped_documento_recibo_locacao_emitido.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfe_recebida_manual.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/sped_documento_cte_recebido.xml',
        'views/sped_documento_agua_recebida.xml',
        'views/sped_documento_gas_recebida.xml',
        'views/sped_documento_energia_recebida.xml',
        'views/sped_documento_comunicacao_recebida.xml',
        'views/sped_documento_telecomunicacao_recebida.xml',
        'views/sped_documento_nf_recebida.xml',

        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_manual.xml',
        'views/sped_documento_item_entrada_simples.xml',

        'views/finan_pagar_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_centrocusto_view.xml',
    ],
    'installable': True,
    'application': False,
}
