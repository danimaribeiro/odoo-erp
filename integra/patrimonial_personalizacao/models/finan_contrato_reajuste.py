# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes



class finan_contrato_reajuste(osv.Model):    
    _inherit = 'finan.contrato.reajuste'    
    
    def reajuste_automatico_contratos(self, cr, uid, ids, context={}):
        reajuste_pool = self.pool.get('finan.contrato.reajuste')
        
        sql = """
            select distinct            
            cf.res_currency_id,
            cf.company_id             
            
            from finan_contrato cf            
            
            where 
            to_char(cf.data_inicio, 'mm-dd') = '{data}'            
            and cf.res_currency_id is not null
            and cf.ativo = true
            and cf.natureza = 'R';"""
            
        sql = sql.format(data=str(hoje())[5:11])        
        #print(sql) 
           
        cr.execute(sql)    
        dados = cr.fetchall()
        
        for res_currency_id, company_id in dados:
            
            data = str(hoje())[:11]                    
            
            existe_ids = reajuste_pool.search(cr, uid, [('currency_id', '=', res_currency_id),('company_id','=',company_id),('data_reajuste','=', data)])
             
            if len(existe_ids) == 0:                    
                dados_item = {
                    'currency_id': res_currency_id,
                    'company_id': company_id,
                    'data_reajuste': hoje(),                        
                }
                contrato_id = reajuste_pool.create(cr, uid, dados_item)                
                reajuste_pool.buscar_contratos(cr, uid, [contrato_id], context=context)
                
                        
        return True
        
finan_contrato_reajuste()       
        
    