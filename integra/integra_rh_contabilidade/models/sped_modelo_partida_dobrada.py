# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor



class sped_modelo_partida_dobrada(osv.Model):
    _inherit = 'sped.modelo_partida_dobrada'
    _name = 'sped.modelo_partida_dobrada'

    _columns = {
                
        #
        # Despesas
        #      
                
        'modelo_folha_despesa_ids': fields.one2many('hr.salary.rule','modelo_folha_despesa_id', u'Item Modelo de Parametrização'),
        'modelo_despesa_ferias_ids': fields.one2many('hr.salary.rule','modelo_folha_despesa_ferias_id', u'Item Modelo de Parametrização'),
        'modelo_despesa_rescisao_ids': fields.one2many('hr.salary.rule','modelo_folha_despesa_rescisao_id', u'Item Modelo de Parametrização'),
        'modelo_despesa_13_ids': fields.one2many('hr.salary.rule','modelo_folha_despesa_13_id', u'Item Modelo de Parametrização'),
        
        
        #
        # Custos
        #
        
        'modelo_custo_ids': fields.one2many('hr.salary.rule','modelo_folha_custo_id', u'Item Modelo de Parametrização'),
        'modelo_custo_ferias_ids': fields.one2many('hr.salary.rule','modelo_folha_custo_ferias_id', u'Item Modelo de Parametrização'),
        'modelo_custo_rescisao_ids': fields.one2many('hr.salary.rule','modelo_folha_custo_rescisao_id', u'Item Modelo de Parametrização'),
        'modelo_custo_13_ids': fields.one2many('hr.salary.rule','modelo_folha_custo_13_id', u'Item Modelo de Parametrização'),
       
    }


sped_modelo_partida_dobrada()


