# -*- coding: utf-8 -*-


{
    'name': 'ERP Integra - Assistência Técnica',
    'version': '1.0',
    'depends': [
        'base',
        'sped_base',        
        'sped',        
        'sped_produto_numero_serie',        
    ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - Assistência Técnica''',
    'init_xml': [],
    'update_xml': [
        'security/groups.xml',      
        
        'wizard/OS_nota_wizard.xml',
        'wizard/OS_to_phonecall_view.xml',
        'wizard/OS_gera_nota.xml',

        'views/assistencia_view.xml',
        'views/ordem_servico_view.xml',
        'views/ordem_servico_tecnico_view.xml',
        'views/os_reparo_view.xml',
        'views/ordem_servico_etapa.xml',
        
        'views/res_partner.xml',
        'views/operacao_nfe_emitida.xml',
        'views/sped_documento_item.xml',
        'views/sped_documento_item_entrada.xml',
        
    ],
    'installable': True,
    'active': False,
}
