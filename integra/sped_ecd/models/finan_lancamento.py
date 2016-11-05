# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields

CAMPOS_LIBERADOS = [
        'pagamento_ids',
        'pago_ids',
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
        'numero_documento_original',
        'data_vencimento_original',
        'valor_original_contrato',
        'contrato_id',
        'lancamento_id',
        'department_id',
        'situacao',
        'valor',
        'data_quitacao',
]

CAMPOS_BLOQUEADOS_RECEBER_PAGAR = [
    'company_id',
    'partner_id',
    'documento_id',
    'valor_documento',
    'data_documento',    
    'conta_id',    
]

class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lote'),
    }

    def write(self, cr, uid, ids, dados, context={}):

        if 'baixa_boleto' not in context:
            for lanc_obj in self.browse(cr, uid, ids):
                #print(dados)
                #print('id', lanc_obj.id)

                #if 'lancamento_id' not in dados:
                    #libera_alteracao = True
                    #for campo in dados:
                        #if campo not in CAMPOS_LIBERADOS:
                            #libera_alteracao = False
                            #break

                    #if lanc_obj.lote_id and not libera_alteracao:
                        #raise osv.except_osv(u'Inválido !', u'Lançamento ja importado para contabildade! Lote: {a} Lançamento: {b}'.format(a=lanc_obj.lote_id.codigo,b=lanc_obj.descricao))

                libera_alteracao = True
                for campo in dados:
                    #print(lanc_obj.id, lanc_obj.tipo)
                    #print(campo)
                    if lanc_obj.tipo not in ('P', 'R'): 
                        if campo not in CAMPOS_LIBERADOS:
                            libera_alteracao = False
                            #print(libera_alteracao)
                            break
                    elif lanc_obj.tipo in ('P', 'R'):
                        if campo in CAMPOS_BLOQUEADOS_RECEBER_PAGAR:
                            libera_alteracao = False
                            #print(libera_alteracao)
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
