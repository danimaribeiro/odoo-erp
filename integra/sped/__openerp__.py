# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED',
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
        'sped_base',
        'sped_product',
        'account',
        #'document_lock',
    ],
    'update_xml': [
        'views/company_view.xml',
        'views/sped_view.xml',
        'views/naturezaoperacao_view.xml',
        'views/cfop_view.xml',
        'views/veiculo_view.xml',
        'views/partner_view.xml',

        'views/sped_operacao_item_simples.xml',
        'views/sped_operacao_item.xml',

        'views/operacao_nfe_emitida.xml',
        'views/operacao_nfse_emitida.xml',
        'views/operacao_recibo_locacao_emitido.xml',

        'views/operacao_nfe_recebida.xml',
        'views/operacao_nfse_recebida.xml',
        'views/operacao_cte_recebido.xml',
        'views/operacao_agua_recebida.xml',
        'views/operacao_gas_recebida.xml',
        'views/operacao_energia_recebida.xml',
        'views/operacao_nf_recebida.xml',
        'views/operacao_comunicacao_recebida.xml',
        'views/operacao_telecomunicacao_recebida.xml',

        'views/sped_documento_item.xml',
        'views/sped_documento_referenciado.xml',
        'views/sped_documento_nfe_emitida.xml',
        'views/sped_documento_nfse_emitida.xml',
        'views/sped_documento_recibo_locacao_emitido.xml',

        'views/sped_documento_item_entrada.xml',
        'views/sped_documento_item_entrada_simples.xml',
        'views/sped_documento_item_entrada_manual.xml',

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

        'views/ajuste_pis_cofins_view.xml',

        'wizard/sped_nfse_agendamento.xml',
        'wizard/sped_nfse_consulta.xml',
        'wizard/sped_nfse_envio.xml',
        'wizard/sped_nfse_envio_email.xml',
        'wizard/sped_nfse_pdf_wizard.xml',
        #'wizard/sped_recibo_locacao_pdf_wizard.xml',
        'wizard/sped_relatorio_retencao_inss.xml',
        'wizard/sped_relatorio_notas_emitidas.xml',
        'wizard/sped_relatorio_notas_canceladas.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
    'init_xml': [
        #'data/sped.cfop.csv',
        #'data/sped.cfop-relacionados.csv',
    ],
    'js': ['static/src/js/lib.js'],
    'qweb': ['static/src/xml/lib.xml'],
    'installable': True,
    'application': True,
}
