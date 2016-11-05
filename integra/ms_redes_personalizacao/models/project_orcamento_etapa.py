# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D



class project_orcamento_etapa(osv.Model):
    _name = 'project.orcamento.etapa'
    _inherit = 'project.orcamento.etapa'
     
    _columns = {        
        'planejamento_ids': fields.one2many('project.orcamento.item.planejamento', 'etapa_id', u'Planejamento', ondelete='cascade'),
    }   
   
project_orcamento_etapa()



class project_orcamento_item_planejamento(osv.Model):
    _inherit = 'project.orcamento.item.planejamento'
    
    _columns = {        
        'etapa_id': fields.many2one('project.orcamento.etapa', u'Etapa'),
    }
    
project_orcamento_item_planejamento()