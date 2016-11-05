# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
import os
import base64
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report
from decimal import Decimal as D
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia, agora, formata_data, data_por_extenso
from pybrasil.valor import formata_valor


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

DIAS_SEMANA = (
    ('1', u'Segunda'),
    ('2', u'Terça'),
    ('3', u'Quarta'),
    ('4', u'Quinta'),
    ('5', u'Sexta'),
    ('6', u'Sábado'),
    ('7', u'Domingo'),    
)

class turma(osv.Model):
    _name = 'turma'
    _description = u'Turma'
    _rec_name = 'descricao'
    
    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for turma_obj in self.browse(cr, uid, ids):            
            res[turma_obj.id] = '[' + str(turma_obj.id) + '] ' + turma_obj.nome + ' ' + turma_obj.professor_id.name

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', ondele='restrict'),
        'descricao': fields.function(_descricao, type='char', method=True, store=True, string=u'Descrição'),
        'nome': fields.char(u'Nome', size=128),                
        'dia_semana': fields.selection(DIAS_SEMANA, string=u'Dia da Semana', select=True),        
        'hora_inicial': fields.float(u'Hora Inicial',  widget='float_time'),        
        'hora_final': fields.float(u'Hora Final',  widget='float_time'),
        'professor_id': fields.many2one('res.users', u'Professor'),
        'produtos_ids': fields.many2many('product.product', 'product_turma', 'turma_id', 'product_id', u'Produtos'),            
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'turma', context=c),
        
    }    

turma()


class aula(osv.Model):
    _name = 'aula'
    _inherit = 'crm.meeting'

    _columns = {                
        'state': fields.selection([('open', u'Confirmado'),
            ('draft', u'Não Confirmado'),
            ('cancel', u'Cancelado'),
            ('done', u'Concluido')], 'State', \
            size=16, readonly=True),                                                
        'contrato_id': fields.many2one('finan.contrato', u'Contrato'),
        'turma_id': fields.many2one('turma', u'Turma'),
        'hora_inicial': fields.related('turma_id','hora_inicial',  type='float', string=u'Hora Inicial', store=True),
        'hora_final': fields.related('turma_id','hora_final',  type='float', string=u'Hora Final', store=True),
        'data': fields.datetime(u'Data'),
    }

aula()