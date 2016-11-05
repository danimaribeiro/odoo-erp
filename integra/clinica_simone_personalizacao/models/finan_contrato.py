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


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
            }

    _defaults = {
        
    }    

finan_contrato()


class finan_contrato_produto(osv.Model):
    _name = 'finan.contrato_produto'
    _inherit = 'finan.contrato_produto'

    def onchange_product_id(self, cr, uid, ids, product_id):
        if not product_id:
            return {}
        
        res = {}
        valores = {}
        res['value'] = valores
        
        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
       
        valores['vr_unitario'] = product_obj.list_price or 0
        
        return res

finan_contrato_produto()