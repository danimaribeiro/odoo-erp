# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import fields, osv


class finan_motivobaixa(osv.Model):
    _name = 'finan.motivobaixa'
    _inherit = 'finan.motivobaixa'

    _columns = {
        'modelo_partida_dobrada_receber_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Baixa Partidas Contas a Receber'),
        'modelo_partida_dobrada_pagar_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Baixa Partidas Contas a Pagar'),
        #'modelo_partida_dobrada_rebimento_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas para Recebimentos'),
        #'modelo_partida_dobrada_pagamento_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas para Pagamentos'),
    }


finan_motivobaixa()
