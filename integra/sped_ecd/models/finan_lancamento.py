# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields

CAMPOS_LIBERADOS = [        
        'pagamento_ids',
        'lote_pagamento_ids',
        'contabilizacao_entrada_ids',
        'contabilizacao_pagamentos_ids',
        'mail_messagem_ids',
        'crm_phonecall_ids',
        'retorno_item_ids',
        'valor_previsto',
        'valor_multa_prevista',
        'formapagamento_id',
        'sugestao_bank_id',
        'res_partner_bank_id',
        'valor_juros_previsto',
        'valor_desconto_previsto',
        'valor_saldo',
        'nosso_numero',
        'motivo_baixa_id',
        'data_baixa',               
]                    

class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lote'),
    }
    def write(self, cr, uid, ids, dados, context={}):
        
        for lanc_obj in self.browse(cr, uid, ids):
            print(dados)
            
            libera_alteracao = True
            for campo in dados:
                if campo not in CAMPOS_LIBERADOS:
                    libera_alteracao = False
                    break
            
            if lanc_obj.lote_id and not libera_alteracao:
                raise osv.except_osv(u'Inválido !', u'Lançamento ja importado para contabildade! Lote: ' + str(lanc_obj.lote_id.codigo)) 

        res = super(finan_lancamento, self).write(cr, uid, ids, dados, context)
        
        return res
    
    def unlink(self, cr, uid, ids, context={}):
        
        for lanc_obj in self.browse(cr, uid, ids):
            if lanc_obj.lote_id:
                raise osv.except_osv(u'Inválido !', u'Lançamento ja importado para contabildade! Lote: ' + str(lanc_obj.lote_id.codigo)) 

        res = super(finan_lancamento, self).unlink(cr, uid, ids, context)
        
        return res

finan_lancamento()
