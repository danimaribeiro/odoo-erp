# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from decimal import Decimal as D
from osv import osv, fields


class sped_documentoduplicata(osv.Model):
    _description = 'Duplicatas de documentos SPED'
    _name = 'sped.documentoduplicata'
    _inherit = 'sped.documentoduplicata'

    _columns = {
        #'documento_id': fields.many2one('sped.documento', u'Documento', ondelete='cascade'),
        #'numero': fields.char(u'Número da duplicata/parcela', size=60),
        #'data_vencimento': fields.date(u'Data de vencimento'),
        #'valor': CampoDinheiro(u'Valor da duplicata/parcela'),
        'finan_documento_id': fields.related('documento_id', 'finan_documento_id', type='many2one', relation='finan.documento', string=u'Tipo do documento'),
        'finan_conta_id': fields.related('documento_id', 'finan_conta_id', type='many2one', relation='finan.conta', string=u'Conta financeira'),
        'finan_centrocusto_id': fields.related('documento_id', 'finan_centrocusto_id', type='many2one', relation='finan.centrocusto', string=u'Centro de custo/modelo de rateio'),
        'res_partner_bank_id': fields.related('documento_id', 'res_partner_bank_id', type='many2one', relation='res.partner.bank', string=u'Conta bancária'),
        'finan_carteira_id': fields.related('documento_id', 'finan_carteira_id', type='many2one', relation='finan.carteira', string=u'Carteira de cobrança'),
        'finan_lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro', ondelete='cascade'),
    }

    def unlink(self, cr, uid, ids, context={}):
        lanc_pool = self.pool.get('finan.lancamento')
        lancamento_ids = []
        for dup_obj in self.browse(cr, uid, ids):
            if dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.id not in lancamento_ids:
                lancamento_ids.append(dup_obj.finan_lancamento_id.id)

        for lanc_obj in lanc_pool.browse(cr, uid, lancamento_ids):
            if (lanc_obj.situacao not in ['Quitado', 'Conciliado', 'Baixado']) and (lanc_obj.nosso_numero == False):
                lanc_obj.unlink()
            elif (lanc_obj.situacao not in ['Quitado', 'Conciliado', 'Baixado']):
                raise osv.except_osv(u'Erro!', u'Não é permitido excluir uma duplicata vinculada a um título quitado/conciliado/baixado %s!!' % lanc_obj.numero_documento)
            else:
                raise osv.except_osv(u'Erro!', u'Não é permitido excluir uma duplicata vinculada a um boleto emitido %s!!' % lanc_obj.numero_documento)

        res = super(sped_documentoduplicata, self).unlink(cr, uid, ids, context=context)

        return res


sped_documentoduplicata()
