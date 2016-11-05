# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
import base64
import os
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D


class ecd_plano_conta(osv.Model):
    _description = u'Ecd Plano de Contas'
    _name = 'ecd.plano.conta'
    _rec_name = 'nome'
    _order = 'nome'

    
    _columns = {
        'nome': fields.char(u'Nome', size=60),
        'company_ids': fields.one2many('res.company', 'plano_id', u'Empresas'),
        'conta_ids': fields.one2many('finan.conta', 'plano_id', u'Contas Contábeis'),                       
    }

    _defaults = {
    }
    
    
ecd_plano_conta()


