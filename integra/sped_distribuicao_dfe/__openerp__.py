# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Distribuicao DF-e',
    'version': '1.0',
    'category': 'SPED',
    'description': 'Distribuicao de DF-e e manifestacao do destinatario',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
    ],
    'update_xml': [
        'views/sped_fiscal_view.xml',
        'views/ultimo_nsu.xml',
        'views/distribuicao_dfe.xml',
        'views/sped_acoes_demoradas.xml',
    ],
    'installable': True,
    'application': False,
}
