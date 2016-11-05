# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class sped_servico(orm.Model):
    _name = 'sped.servico'
    _inherit = 'sped.servico'

    _columns = {
        'cd_servico_barueri': fields.char(u'Código Serviço Barueri', size=9),
    }


sped_servico()
