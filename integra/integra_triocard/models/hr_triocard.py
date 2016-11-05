# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje
import base64
from pybrasil.valor.decimal import Decimal as D

ACAO_ALTERACAO = (
        ('A', u'Alteração de limite e/ou premio'),
        ('B', u'Bloqueio de CPF'),
        ('D', u'Desbloqueio de CPF'),
        ('C', u'Cancelamento de CPF'),
        ('L', u'Alteração de Limite'),
        ('P', u'Alteração de Prêmio'),
        ('S', u'Alteração Sindicato'),
) 


class hr_triocard(osv.Model):
    _name = 'hr.triocard'
    _description = 'Arquivo Trio Card'
    _order = 'data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresas'),        
        'data': fields.date(u'Data do Arquivo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'acao_alteracao': fields.selection(ACAO_ALTERACAO, u'Ação de Alteração'),                
    }

    _defaults = {
        'data': fields.date.today,        
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,        

    }
    
hr_triocard()

    