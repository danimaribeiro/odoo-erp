# -*- coding: utf-8 -*-

from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, formata_data


class sped_documento_provisao_compra(osv.Model):
    _name = 'sped.documento.provisao.compra'
    _description = u'SPED DOCUMENTO PROVISÃO DE COMPRA'
    _rec_name = 'lancamento_id'
    
    
    def _busca_campo(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        
        for obj in self.browse(cr, uid, ids):
            valor = 0
            
            
            nome_campo = nome_campo.replace('func_', '')
            
            if nome_campo == 'purchase_order_id':
                purchase_obj = getattr(obj, nome_campo, 0)
                valor = purchase_obj.id
            else:                
                valor = getattr(obj, nome_campo, 0)
            
            res[obj.id] = valor
            
        return res  
    
    _columns = {        
        'documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento'),
        
        'data_vencimento': fields.date(u'Data vencimento'),
        'func_data_vencimento': fields.function(_busca_campo, type='date', string=u'Data vencimento'),
        
        'valor_provisionado': fields.float(u'Valor Provisionado'),
        'func_valor_provisionado': fields.function(_busca_campo, type='float', string=u'Valor Provisionado'),
        
        'purchase_order_id': fields.many2one('purchase.order', u'Pedido de compra'),
        'func_purchase_order_id': fields.function(_busca_campo, type='many2one', relation='purchase.order', string=u'Valor Provisionado'),
        
        'valor_atendido': fields.float(u'Valor Atendido'),        
        'partner_id': fields.many2one('res.partner', u'Forncedor'),
        'salvo': fields.boolean(u'Já salvo?'),
    }
    
    def onchange_lancamento_id(self, cr, uid, ids, lancamento_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id)
        
        if lancamento_obj:
            valores['data_vencimento'] = lancamento_obj.data_vencimento
            valores['func_data_vencimento'] = lancamento_obj.data_vencimento
            valores['valor_provisionado'] = lancamento_obj.valor_documento            
            valores['func_valor_provisionado'] = lancamento_obj.valor_documento            
            valores['purchase_order_id'] = lancamento_obj.purchase_order_id.id
            valores['func_purchase_order_id'] = lancamento_obj.purchase_order_id.id

        return res   


sped_documento_provisao_compra()
