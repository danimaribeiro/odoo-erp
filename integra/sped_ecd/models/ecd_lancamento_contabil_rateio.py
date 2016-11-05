# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class ecd_lancamento_contabil_rateio(osv.Model):
    _description = u'ECD Lançamento Contábil - Rateio Gerencial'
    _name = 'ecd.lancamento.contabil.rateio'
    _inherit = 'finan.lancamento.rateio'
    _order = 'lancamento_contabil_id'

    def _calcula_valores_contabil(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for rateio_obj in self.browse(cr, uid, ids):
            res[rateio_obj.id] = D(0)

            if nome_campo == 'vr_debito':
                base = D(rateio_obj.lancamento_contabil_id.vr_debito or 0)
            else:
                base = D(rateio_obj.lancamento_contabil_id.vr_credito or 0)

            porcentagem = D(rateio_obj.porcentagem or 0)
            valor = base * porcentagem / D(100)
            #valor = valor.quantize(D('0.01'))

            res[rateio_obj.id] = valor

        return res
    
    _columns = {
        'lancamento_contabil_id': fields.many2one('ecd.lancamento.contabil', u'Lançamento contábil', ondelete='cascade'),
        'lote_id': fields.related('lancamento_contabil_id', 'lote_id', type='integer', string=u'Lote', store=True),
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', ondelete='restrict'),
        'vr_debito': fields.function(_calcula_valores_contabil, type='float', store=False, digits=(18, 2), string=u'Valor Débito'),
        'vr_credito': fields.function(_calcula_valores_contabil, type='float', store=False, digits=(18, 2), string=u'Valor Crédito'),
    }


ecd_lancamento_contabil_rateio()



class ecd_lancamento_contabil(osv.Model):
    _name = 'ecd.lancamento.contabil'
    _inherit = 'ecd.lancamento.contabil'

    _columns = {
        'rateio_ids': fields.one2many('ecd.lancamento.contabil.rateio', 'lancamento_contabil_id', u'Rateios'),
    }


ecd_lancamento_contabil()
