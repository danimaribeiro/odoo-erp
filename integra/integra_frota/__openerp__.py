# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Frota - Integra',
    'version': '1.0',
    'category': 'Integra',
    'description': u'Controle de Frotas INTEGRA',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'depends': [
        'base',
        'sped_base',
        'hr',
        'finan_contrato',
    ],
    'images': [
        'images/frota.png',
        'images/frota-hover.png'
    ],
    'data': [
        'data/frota.tipo.csv',
    ],
    'update_xml': [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        'views/frota_view.xml',
        'views/frota_tipo_view.xml',
        'views/frota_modelo_view.xml',
        'views/frota_veiculo_view.xml',
        'views/frota_servico_view.xml',
        'views/frota_odometro_view.xml',

        'views/frota_os_view.xml',
        'views/frota_os_veiculo_view.xml',
        'views/frota_os_locacao_veiculo_view.xml',

        'wizard/frota_relatorio_km_rodado.xml',
        'wizard/frota_relatorio_os_veiculo.xml',
        'wizard/frota_relatorio_os_fornecedor.xml',
        'wizard/frota_relatorio_justificativa_km.xml',
        'wizard/frota_relatorio_custo_imobilizado.xml',
        'wizard/frota_relatorio_custo_imobilizado_motorista.xml',
        'wizard/frota_relatorio_veiculo_manutencao.xml',
        'wizard/frota_relatorio_listagem_odometro.xml',
    ],
    'init_xml': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
