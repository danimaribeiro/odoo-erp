# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class finan_rateio(osv.Model):
    _inherit = 'finan.rateio'
    
    def _valor(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        
        for rateio_obj in self.browse(cr, uid, ids):
            res[rateio_obj.id] = D(0)
            
            if rateio_obj.purchase_order_id:
                res[rateio_obj.id] = D(rateio_obj.porcentagem or 0) * D(rateio_obj.purchase_order_id.amount_total or 0) / 100
            elif rateio_obj.sped_documento_id:
                res[rateio_obj.id] = D(rateio_obj.porcentagem or 0) * D(rateio_obj.sped_documento_id.vr_fatura or 0) / 100
            elif rateio_obj.sped_documentoitem_id:
                res[rateio_obj.id] = D(rateio_obj.porcentagem or 0) * D(rateio_obj.sped_documentoitem_id.vr_fatura or 0) / 100
                
        return res

    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', u'Pedido de compra', ondelete='cascade', select=True),
        'sped_documentoitem_id': fields.many2one('sped.documentoitem', u'Documento item', ondelete='cascade', select=True),
        'sped_documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
        'valor': fields.function(_valor, type='float', string='Valor'),
    }


finan_rateio()


class finan_centrocusto(osv.Model):
    _inherit = 'finan.centrocusto'
    
    _columns = {
        'sped_documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade', select=True),
    }


finan_centrocusto()
