# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': u'SPED - Parametrização Contabilidade',
    'version': '1.0',
    'category': 'SPED',
    'description': u'''
    SPED - Parametrização Contabilidade''',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'account',
        'sped',
        'sped_base',
        'finan',
        'finan_contrato'
    ],
    'update_xml': [
        'views/account_view.xml',
        'views/operacao_view.xml',
        'views/sped_modelo_partida_dobrada.xml',
        'views/finan_historico.xml',
        'views/finan_documento.xml',
        'views/finan_contrato_pagar_view.xml',
        'views/finan_motivobaixa_view.xml',
        'views/plano_conta_referencial_view.xml',
        'views/finan_receber_view.xml',
        'views/finan_pagar_view.xml',
        'views/sped_documento_nfe_emitida.xml',
        'views/sped_documento_nfse_emitida.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/sped_documento_item.xml',
    ],
    'installable': True,
    'application': True,
}
