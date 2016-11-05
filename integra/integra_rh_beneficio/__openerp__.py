

{
    'name': 'ERP Integra - RH Benefícios',
    'version': '1.0',
    'depends': [        
        'integra_rh',
        ],
    'author': 'ERP Integra',
    'category': 'ERP Integra',
    'description': u'''ERP Integra - RH Benefícios''',
    'init_xml': [],
    'update_xml': [    
        'views/hr_contract_view.xml',
        'views/hr_contract_linha_transporte.xml',
        'views/hr_contract_vale_refeicao.xml',
        'views/hr_linha_transporte.xml',
        'views/hr_lote_beneficio.xml',
        'views/hr_salary_rule.xml',
        'views/hr_salary_rule_valor.xml',
        'views/hr_sindicato.xml',
       
        'wizards/hr_relatorio_linha_transporte.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,

}
