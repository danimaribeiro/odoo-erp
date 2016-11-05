# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)

class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
    }

    _defaults = {
    }




res_partner()
