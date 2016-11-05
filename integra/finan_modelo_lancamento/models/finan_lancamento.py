# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields, orm
from decimal import Decimal as D
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes
from copy import copy



class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'modelo_id': fields.many2one('finan.lancamento', u'Modelo Lançamento', ondelete="restrict", domain=[('tipo','in',('MR','MP'))]),
        'descricao_modelo': fields.char(u'Descrição', size=80, required=True),
    }
    
    def onchange_modelo(self, cr, uid, ids, modelo_id, company_id, valor_documento=0, context={}):
        if not modelo_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores

        modelo_pool = self.pool.get('finan.lancamento')
        modelo_obj = modelo_pool.browse(cr, uid, modelo_id)

        if modelo_obj.documento_id:
            valores['documento_id'] = modelo_obj.documento_id.id            
        
        if modelo_obj.conta_id:
            valores['conta_id'] = modelo_obj.conta_id.id            
        
        if modelo_obj.sugestao_bank_id:
            valores['sugestao_bank_id'] = modelo_obj.sugestao_bank_id.id            
        
        if modelo_obj.historico:
            valores['historico'] = modelo_obj.historico            
        
        if modelo_obj.centrocusto_id:
            valores['centrocusto_id'] = modelo_obj.centrocusto_id.id
        else:
            
            padrao = copy(context)
            padrao['company_id'] = company_id
            padrao['conta_id'] = modelo_obj.conta_id.id or False
            padrao['centrocusto_id'] = modelo_obj.centrocusto_id.id or False
            rateio = {}
            rateio = self.pool.get('finan.centrocusto').realiza_rateio(cr, uid, [modelo_obj.id], context=context, rateio=rateio, padrao=padrao, valor=valor_documento, tabela_pool=modelo_pool)            

            campos = self.pool.get('finan.centrocusto').campos_rateio(cr, uid)

            dados = []
            self.pool.get('finan.centrocusto').monta_dados(rateio, campos=campos, lista_dados=dados, valor=valor_documento)
            valores['rateio_ids'] = dados            
            
                        
        return retorno
    
finan_lancamento()
