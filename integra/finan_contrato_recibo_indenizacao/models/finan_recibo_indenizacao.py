# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields, orm
from decimal import Decimal as D
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes
from copy import copy


class finan_recibo_indenizacao(osv.Model):
    _name = 'finan.recibo.indenizacao'
    _description = u'Recibo de Indenizacao'
    _order = 'id'
                       
    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            
            if obj.company_id:            
                if obj.company_id.partner_id.cnpj_cpf:
                    res[obj.id] = obj.company_id.partner_id.cnpj_cpf
            else:
                res[obj.id] = ''

        return res    

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),
        'company_id': fields.related('contrato_id','company_id',  type='many2one', string=u'Empresa', relation='res.company', store=True),
        'partner_id': fields.related('contrato_id','partner_id',  type='many2one', string=u'Cliente', relation='res.partner', store=True),
        'carteira_id': fields.related('contrato_id','carteira_id',  type='many2one', string=u'Carteira', relation='finan.carteira', store=True),        
        'modelo_id': fields.many2one('finan.lancamento', u'Modelo Financeiro', ondelete="restrict", domain=[('tipo','=','MR')]),
        'sped_documento_id': fields.many2one('sped.documento', u'Documento Fiscal', ondelete='restrict'),
        'cnpj_cpf': fields.function(_get_raiz_cnpj, type='char', string=u'CNPJ', size=20, store=True, method=True),
        'data': fields.date(u'Data'),
        'valor': fields.float(u'Valor'),
        'data_vencimento': fields.date(u'Data Vencimento'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'data_confirmacao': fields.datetime(u'Data de Confirmação'),
        'usuario_confirmacao_id': fields.many2one('res.users', u'Confirmado por'),
        'numero': fields.integer(u'Número'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento', ondelete='restrict'),        
    }
    
    _defaults = {
        'data': fields.datetime.now,        
    }
    
    def onchange_contrato_id(self, cr, uid, ids, contrato_id, context={}):
        if not contrato_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores

        contrato_pool = self.pool.get('finan.contrato')
        contrato_obj = contrato_pool.browse(cr, uid, contrato_id)
       
        valores['company_id'] = contrato_obj.company_id.id            
        valores['partner_id'] = contrato_obj.partner_id.id  
        if contrato_obj.company_id.partner_id:
            valores['cnpj_cpf'] = contrato_obj.company_id.partner_id.cnpj_cpf
                       
        if contrato_obj.carteira_id:
            valores['carteira_id'] = contrato_obj.carteira_id.id

        return retorno
    
    def confirmar(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        
        for recibo_obj in self.browse(cr, uid, ids):            
            dados = {
                'confirmado': True,
                'data_confirmacao': fields.datetime.now(),
                'usuario_confirmacao_id': uid,                     
            }         
            
            if recibo_obj.cnpj_cpf:
                lista_ultimo_numero = self.search(cr, uid, args=[('cnpj_cpf', '=', recibo_obj.cnpj_cpf),('numero','!=', False)], limit=1, order='numero DESC')

            if lista_ultimo_numero:
                ultimo_numero = self.browse(cr, uid, lista_ultimo_numero, context)[0]               
                dados['numero'] = ultimo_numero.numero + 1
                numero = ultimo_numero.numero + 1
            else:
                dados['numero'] = 1     
                numero = 1       
            
            lancamento_id = lancamento_pool.copy(cr, uid, recibo_obj.modelo_id.id)
            
            dados_lancamento = {
                'tipo': 'R',                                              
                'recibo_indenizacao_id': recibo_obj.id,                                              
                'company_id': recibo_obj.company_id.id,
                'partner_id': recibo_obj.partner_id.id,                               
                'data_doccumento': recibo_obj.data,
                'data_vencimento': recibo_obj.data_vencimento,
                'valor_documento': recibo_obj.valor,
            }
            
            if recibo_obj.carteira_id:                 
                dados_lancamento['carteira_id'] = recibo_obj.carteira_id.id
                
            numero_documento = 'RI-' + str(numero) 
            dados_lancamento['numero_documento'] = numero_documento
            lancamento_pool.write(cr, uid, [lancamento_id], dados_lancamento)
            
            if recibo_obj.carteira_id:
                lancamento_pool.gerar_boleto(cr, uid, [lancamento_id])
            
            dados['lancamento_id'] = lancamento_id
            recibo_obj.write(dados)
            
finan_recibo_indenizacao