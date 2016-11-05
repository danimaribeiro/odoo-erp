# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from finan.models.finan_conta import TIPO_RECEITA_DESPESA
from finan.models.finan_lancamento import *

class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'
   
    _columns = {
        'recibo_indenizacao_id': fields.many2one('finan.recibo.indenizacao', u'Recibo Indenizacao', ondelete='cascade'),
    }
    

finan_lancamento()
