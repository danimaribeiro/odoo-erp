# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_operacao(osv.Model):
    _description = u'Operações fiscais'
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'baixa_patrimonio': fields.boolean(u'Baixar patrimônios vinculados a esta nota?'),
    }


sped_operacao()
