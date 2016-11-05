# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class ordem_servico_acessorio(osv.Model):
    _name = 'ordem.servico.acessorio'
    _description = u'Ordem de Serviço Acessórios'

    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
        'acessorio': fields.char(u'Acessório', size=30),
        'quantidade': fields.integer(u'Quantidade'),        
        
    }

    _defaults = {
             'quantidade': 1,
                     
    }

ordem_servico_acessorio()


