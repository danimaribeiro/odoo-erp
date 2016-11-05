# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import fields, osv


class finan_formapagamento(osv.Model):
    _name = 'finan.formapagamento'
    _inherit = 'finan.formapagamento'
  
    def id_credito_cobranca(self, cr, uid):
        #
        # Fixa o ID da forma de pagamento 4 - CARTEIRA DE COBRANÇA
        #
        return 38


finan_formapagamento()
