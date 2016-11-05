#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
from osv import fields, osv


class hr_horario_contratual(osv.Model):
    _name = 'hr.horario.contratual'
    _description = u'Horario de Contratual'    
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Nome', size=100),
        'tipo': fields.selection([('1', u'Semanal'), ('2', u'Variável')], u'Tipo Contratação'),
        'quantidade_horas_semana': fields.integer(u'Qtd.horas semanais)'),              
        'item_ids': fields.one2many('hr.horario.contratual.item','horario_id', u'Horario de Contratual Itens'),                 
    }

    _defaults = {
         'tipo': '1',
    }

hr_horario_contratual()

class hr_horario_contratual_item(osv.Model):
    _name = 'hr.horario.contratual.item'
    _description = u'Horario de Contratual Item'    
    
    _columns = {
        'horario_id': fields.many2one('hr.horario.contratual.item', u'Horario de Contratual'),
        'dia': fields.selection([
                            ('1', u'Segunda'),
                            ('2', u'Terça'),
                            ('3', u'Quarta'),
                            ('4', u'Quinta'),
                            ('5', u'Sexta'),
                            ('6', u'Sábado'),
                            ('7', u'Domingo'),
                            ('8', u'Variável'),], u'Tipo Contratação'),        
        'jornada_id': fields.many2one('hr.jornada', u'Jornada de Trabalho'),                         
    }

    _defaults = {
            'dia': '1',
                
    }

hr_horario_contratual_item()
