# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class ordem_servico_historico(osv.Model):
    _description = u'Ordem de Serviço Histórico'
    _name = 'ordem.servico.historico'
    _rec_name = 'data'
    _order = 'data'
    
   
    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
        'user_id': fields.many2one('res.users', u'Usuários'),
        'data': fields.datetime(u'Data'),
        'etapa_id': fields.many2one('ordem.servico.etapa', u'Etapa'),                        
    }

    _defaults = {
        'data': fields.datetime.now,
        
    }
    
ordem_servico_historico()