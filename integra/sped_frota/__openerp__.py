# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


{
    'name': 'SPED - Frota',
    'version': '1.0',
    'description': u'Integração Fiscal - Frota',
    'author': 'Integra',
    'maintainer': 'Integra',
    'website': 'http://www.Integra.inf.br',
    'depends': [
        'base',
        'sped',
        'integra_frota',
    ],
    'update_xml': [
        'views/sped_documento_nfe_emitida.xml',
        'views/sped_documento_nfe_recebida.xml',
        'views/sped_documento_nfse_emitida.xml',
        'views/sped_documento_nfse_recebida.xml',
        'views/frota_os.xml',
        'views/frota_os_veiculo.xml',
        'views/frota_os_locacao_veiculo.xml',
    ],
    'installable': True,
    'application': False,
}
