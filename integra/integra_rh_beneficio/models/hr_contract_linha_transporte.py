# -*- coding: utf-8 -*-


from osv import osv, fields
from datetime import datetime, date, timedelta


class hr_contract_linha_transporte(osv.Model):
    _name = 'hr.contract.linha.transporte'
    _description = 'Contrato Vale Transporte'

    _columns = {        
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'linha_id': fields.many2one('hr.linha.transporte', u'Linha de transporte'),
        'vr_unitario': fields.related('linha_id', 'valor', type='float', string='Valor Unit.', store=True),
        'quantidade': fields.float(u'Quantidade'),
        'vr_total': fields.float(u'Valor total'),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
    }
    
    _defaults = {
        'data_inicial': fields.date.today, 
        #'data_final': fields.date.today,
    }
    
    def get_linha(self, cr, uid, ids, linha_id, context={}):
        
        retorno = {}
        valores = {}
        if not linha_id:
            return retorno

        linha_pool = self.pool.get('hr.linha.transporte')
        linha_obj = linha_pool.browse(cr, uid, linha_id)

        retorno['value'] = valores
        valores['vr_unitario'] = linha_obj.valor
        return retorno
    
    
    def soma_total(self, cr, uid, ids, vr_unitario=0, quantidade=0, context={}):
        
        retorno = {}
        valores = {}
        
        total = vr_unitario * quantidade    
        retorno['value'] = valores
        valores['vr_total'] = total
        return retorno

hr_contract_linha_transporte()

