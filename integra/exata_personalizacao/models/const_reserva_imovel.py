# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

import os
import base64
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

class const_reserva_imovel(osv.Model):
    _name = 'const.reserva.imovel'
    _description = u'Controle de reservas do Imóvel'
    _order = 'id'   
    
    _columns = {              
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', on_delete='cascade'),        
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),         
        'corretor_id': fields.related('contrato_id','vendedor_id',  type='many2one', string=u'Corretor', relation='res.users', store=True),
        'partner_id': fields.related('contrato_id','partner_id',  type='many2one', string=u'Cliente', relation='res.partner', store=True),        
        'data_reserva': fields.datetime(u'Data da Reserva'),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),       
    }
    
    _defaults = {
       'data_reserva': fields.datetime.now,
    }    
       
const_reserva_imovel()

