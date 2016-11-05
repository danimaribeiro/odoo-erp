# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D

DEPARTAMENTO = [
    ('CO', u'Comercial'),
    ('JU', u'Jurídico'),
    ('FI', u'Financeiro'),
    ('CB', u'Contabilidade'),
    ('AD', u'Adm'),
    
]

class checklist_contrato(osv.Model):
    _description = u'check-list Contrato'
    _name = 'checklist.contrato'
    _rec_name = 'nome'

    _columns = {                
        'data': fields.date(u'Data'),
        'nome': fields.char(u'Nome', size=60),
        'item_ids': fields.one2many('checklist.contrato.item', 'clecklist_id', u'check-list Contrato Item' )
    }
    
    _defaults = {
        'data': fields.datetime.now,
    }
            
checklist_contrato()

class checklist_contrato_item(osv.Model):
    _description = u'check-list Contrato Item'
    _name = 'checklist.contrato.item'
    _rec_name = 'ordem'
    _order = 'ordem, atividade'

    _columns = { 
        'clecklist_id': fields.many2one('checklist.contrato', u'check-list Contrato', ondelete='restrict'),                   
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'project_id': fields.many2one('project.project', u'Projeto', ondelete='restrict'),
        'sale_order_id': fields.many2one('sale.order', u'Proposta', ondelete='restrict'),
        'ordem': fields.char(u'Ordem', size=64, select=True),
        'atividade': fields.char(u'Atividade', size=120),
        'departamento': fields.selection(DEPARTAMENTO, u'Departamento'),
        'cargo': fields.char(u'Cargo', size=30),
        'grupo_id': fields.many2one('res.groups', u'Cargo/Grupo'),
        'data_conclusao': fields.date(u'Data conclusão'),
        'user_id': fields.many2one('res.users', u'Usuário'),   
        'obs': fields.text(u'Observação'),     
    }
    
    
checklist_contrato_item()
