# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields

class ecd_lancamento_excluido(osv.Model):
    _description = u'Ecd Lançamento Excluido'
    _name = 'ecd.lancamento.excluido'
    _rec_name = 'lancamento_id'
    _order = 'data desc'

    _columns = {        
        'company_id': fields.many2one('res.company',u'Empresas', ondelete='restrict'),
        'cnpj_cpf': fields.char(u'Cnpj',size=18),        
        'data': fields.date(u'Data'),
        'create_date': fields.datetime(u'Data de exclusão'),
        'lancamento_id': fields.integer(u'Lançamento Contabil'),
        'finan_lancamento_id': fields.integer(u'Lançamento financeiro'),
        'sped_documento_id': fields.integer(u'Documento fiscal'),   
        'lote_id': fields.integer(u'Lote'),
        'usuario_id': fields.many2one('res.users', u'Excluido por'),                             
        'valor': fields.float(u'Valor'),                             
    }

    _defaults = {           
            
    }
    
   
ecd_lancamento_excluido()


