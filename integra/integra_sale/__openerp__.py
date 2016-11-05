# -*- encoding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'Integra Vendas',
    'version': '1.0',
    'category': 'Integra',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.ERPIntegra.com.br',
    'description': u'Integra Pedidos de Venda',
    'depends': [
                'base',
                'sale',
                'sped',
    ],
    'update_xml' : [
        'security/ir.model.access.csv',

        #'views/sale_order_line_view.xml',
        'wizard/crm_saleorder_to_phonecall_view.xml',
        'wizard/sale_nota_wizard.xml',

        'views/sale_view.xml',
        'views/sale_motivocancelamento_view.xml',
        'views/orcamento_grupo_aprovacao.xml',
    ],
    'installable': True,
    'application': False,
}
