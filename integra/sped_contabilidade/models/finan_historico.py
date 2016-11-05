# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class finan_historico(osv.Model):
    _description = u'Histório - Contabilidade'
    _name = 'finan.historico'
    _rec_name = 'descricao'
        
    
    def _get_nome(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for historico_obj in self.browse(cr, uid, ids):
            res[historico_obj.id] = str(historico_obj.codigo) 
        return res

    _columns = {
        'descricao': fields.function(_get_nome, type='char', string=u'Descrição', method=True, store=True, select=True),
        'nome': fields.char(u'Descrição', size=60),
        'codigo': fields.integer(u'Código'),
    }
    
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)',
            u'O código não pode se repetir!'),
    ]

finan_historico()
