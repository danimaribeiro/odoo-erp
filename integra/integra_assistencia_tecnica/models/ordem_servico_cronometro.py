# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields

ATIVIDADE = [
    ('A', 'Análise'),
    ('R', 'Reparo'),
]            

class ordem_servico_cronometro(osv.Model):
    _name = 'ordem.servico.cronometro'
    _description = u'Ordem de Serviço Cronômetro'
    _order = 'hora_inicial desc'

    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
        'tecnico_id': fields.many2one('res.users', u'Técnico'),
        'hora_inicial': fields.datetime(u'Hora inicial'),
        'hora_final': fields.datetime(u'Hora final'),
        'atividade': fields.selection(ATIVIDADE, u'Atividade'),        
        
    }

    _defaults = {
        'tecnico_id': lambda obj, cr, uid, context: uid,
        'hora_inicial': fields.datetime.now,        
        'atividade': 'A',
    }

ordem_servico_cronometro()

