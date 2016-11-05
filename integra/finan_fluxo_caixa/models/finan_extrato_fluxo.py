# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
from pybrasil.data import hoje
from pybrasil.valor.decimal import Decimal as D


class finan_extrato_fluxo(osv.Model):    
    _name = 'finan.extrato.fluxo'
    _description = u'Pesquisa Fluxo de caixa '
    _auto = False
    _order = 'data_quitacao, valor_compensado_credito desc, valor_compensado_debito desc'
    
    def _saldo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for extrato_obj in self.browse(cr, uid, ids):
            res[extrato_obj.id] = D(extrato_obj.valor_compensado_credito or 0) - D(extrato_obj.valor_compensado_debito or 0)
            
        return res

    _columns = {
        'parent_id': fields.many2one('res.company', u'Empresa'),
        'company_id': fields.many2one('res.company', u'Unidade de negócio'),
        'partner_id': fields.many2one('res.partner', u'Cliente/Fornecedor'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento'),                
    
        'tipo': fields.selection((('T', u'Transferência'), ('R', u'Pagamento recebido'), ('P', u'Pagamento efetuado'), ('I', u'Saldo inicial'), ('E', u'Transação entrada'), ('S', u'Transação saída')), string=u'Tipo'),        
        'data_documento': fields.date(u'Data do Documento'),
        'data_quitacao': fields.date(u'Data de pagamento'),
        'data_compensacao': fields.date(u'Data de compensação'),
        'data_vencimento': fields.date(u'Data de vencimento'),
        'valor_compensado_credito': fields.float(u'Crédito'),
        'valor_compensado_debito': fields.float(u'Débito'),
        'conciliado': fields.boolean(u'Conciliado'),
        'valor_saldo': fields.function(_saldo, type='float', string='Saldo'),
        
        'data_vencimento_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De vencimento'),
        'data_vencimento_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A vencimento'),
        'data_documento_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De documento'),
        'data_documento_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A documento'),
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De vencimento'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A vencimento'),
        'data_quitacao_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De quitacao'),
        'data_quitacao_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A quitacao'),
        'data_baixa_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De baixa'),
        'data_baixa_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A baixa'),
    }
    
    def unlink(self, cr, uid, ids, context=None):        
        return ids


finan_extrato_fluxo()

