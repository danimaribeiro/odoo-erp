# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class finan_documento(osv.Model):
    _name = 'finan.documento'
    _inherit = 'finan.documento'

    _columns = {
        'modelo_partida_dobrada_receber_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas Contas Receber'),
        'modelo_partida_dobrada_pagar_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas Contas Pagar'),
        'modelo_partida_dobrada_rebimento_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas para Recebimentos'),
        'modelo_partida_dobrada_pagamento_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas para Pagamentos'),

    }


finan_documento()
