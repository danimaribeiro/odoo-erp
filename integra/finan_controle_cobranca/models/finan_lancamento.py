# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from finan.models.finan_conta import TIPO_RECEITA_DESPESA
from finan.models.finan_lancamento import *


class finan_lancamento(orm.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'
    
    
    def _cobranca(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        return res
    
    def _search_cobranca(self, cr, uid, lancamento_pool, texto, args, context={}):
        res = {}
                            
        sql = """
            select 
                l.id 
            from finan_lancamento l
                join finan_cobranca_itens ci on ci.lancamento_id = l.id
                join finan_controle_cobranca cb on cb.id = ci.cobranca_id
            where """
        if context['cobranca_hoje'] == True:
            sql += """cb.data = '{data_hoje}'"""
            
        elif context['cobrados'] == True:
            sql += """cb.data < '{data_hoje}'"""
        
        sql = sql.format(data_hoje=hoje())               
        cr.execute(sql)
        dados = cr.fetchall()
        
        if len(dados) == 0:
            return [('id', '=', False)]
        else:
            return  [('id', 'in', dados)]
        
           
    _columns = {
        'cobranca_ids': fields.many2many('finan.controle.cobranca', 'finan_cobranca_itens', 'lancamento_id', 'cobranca_id', string=u'Cobranças'),               
        'cobranca_hoje': fields.function(_cobranca, string=u'Cobrandos Hoje?', method=True, type='boolean', store=False, fnct_search=_search_cobranca),        
        'cobrados': fields.function(_cobranca, string=u'Já Cobrados?', method=True, type='boboolean', store=False, fnct_search=_search_cobranca),        
    }
    
finan_lancamento()

