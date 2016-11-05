# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED Tabela Fornecedor',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Atualização de tabelas de preço dos fornecedores',
    'depends': ['base', 'product', 'sped'],
    'update_xml' : [
        'views/sped_documento_tabela_fornecedor.xml',
    ],
    'installable': True,
    'application': False,
}
