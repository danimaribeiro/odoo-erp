# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    _columns = {
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento', ondelete='restrict', select=True),
        'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal', ondelete='restrict', select=True),
        'rateio_ids': fields.one2many('finan.rateio', 'purchase_order_id', u'Itens do rateio'),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict', select=True),

        'finan_lancamento_ids': fields.one2many('finan.lancamento', 'purchase_order_id', u'Lançamentos de provisão'),
    }

    def gera_financeiro(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        for ordem_obj in self.browse(cr, uid, ids, context=context):
            amount_total = D(0)
            amount_total = D(ordem_obj.amount_total or 0 )

            if amount_total > 0 and ordem_obj.state == 'approved':
                if not ordem_obj.payment_term_id:
                    raise osv.except_osv(u'Erro!', u'Pedido sem condição de pagamento!')

                if not ordem_obj.payment_term_id.line_ids:
                    raise osv.except_osv(u'Erro!', u'Condição de pagamento inconsistente! Revise a condição de pagamento')

                if not ordem_obj.operacao_id:
                    raise osv.except_osv(u'Erro!', u'Pedido sem operação fiscal!')

                payment_term_obj = self.pool.get('account.payment.term').browse(cr, uid, ordem_obj.payment_term_id.id)
                operacao_obj = ordem_obj.operacao_id

                lista_vencimentos = payment_term_obj.compute(amount_total, date_ref= ordem_obj.date_order[:10])

                print(lista_vencimentos)

                if lista_vencimentos:
                    parcela = 1
                    for data, valor in lista_vencimentos:
                        dados = {
                            'purchase_order_id': ordem_obj.id,
                            'company_id': ordem_obj.company_id.id,
                            'tipo': 'P',
                            'provisionado': True,
                            'conta_id': operacao_obj.finan_conta_id.id,
                            'documento_id': operacao_obj.finan_documento_id.id,
                            'partner_id': ordem_obj.partner_id.id,
                            'numero_documento': ordem_obj.name + '_' + str(parcela).zfill(2),
                            'data_documento': ordem_obj.date_order[:10],
                            'data_vencimento': data,
                            'valor_documento': valor,
                            'sugestao_bank_id': ordem_obj.partner_bank_id.id if ordem_obj.partner_bank_id else False,
                            'historico': ordem_obj.notes,
                        }

                        if hasattr(operacao_obj.finan_documento_id, 'provisionado'):
                            dados['provisionado'] = operacao_obj.finan_documento_id.provisionado

                        if ordem_obj.centrocusto_id:
                            dados['centrocusto_id'] = ordem_obj.centrocusto_id.id

                        parcela += 1

                        if parcela == len(lista_vencimentos):
                            dados['pagamento_bloqueado'] = getattr(ordem_obj.payment_term_id, 'bloqueia_pagamento', False)

                        #print(uid, dados)
                        lancamento_id = lancamento_pool.create(cr, uid, dados)
                        lancamento_obj = lancamento_pool.browse(cr, uid, lancamento_id)

                        rateio_dic = ordem_obj._dados_rateio()
                        print('rateio_dic', rateio_dic)
                        dados_rateio = []
                        dados_rateio = cc_pool.monta_dados(rateio_dic, campos=campos, lista_dados=dados_rateio, valor=D(ordem_obj.amount_total or 0), forcar_valor=lancamento_obj.valor_documento)

                        salva_rateio = []
                        for dic_rateio in dados_rateio:
                            salva_rateio += [[0, lancamento_obj.id, dic_rateio]]

                        lancamento_obj.write({'rateio_ids': salva_rateio})


                        if 'conta_id' in salva_rateio[0][2]:
                            lancamento_obj.write({'conta_id': salva_rateio[0][2]['conta_id']})

                else:
                    dados = {
                            'purchase_order_id': ordem_obj.id,
                            'company_id': ordem_obj.company_id.id,
                            'tipo': 'P',
                            'provisionado': True,
                            'conta_id': operacao_obj.finan_conta_id.id,
                            'documento_id': operacao_obj.finan_documento_id.id,
                            'partner_id': ordem_obj.partner_id.id,
                            'data_documento': ordem_obj.date_order[:10],
                            'valor_documento': amount_total,
                            'numero_documento': ordem_obj.name,
                            'sugestao_bank_id': ordem_obj.partner_bank_id.id if ordem_obj.partner_bank_id else False
                        }
                    lancamento_pool.create(cr, uid, dados)

    def wkf_approve_order(self, cr, uid, ids, context={}):
        ordem_pool = self.pool.get('purchase.order')

        res = super(purchase_order, self).wkf_approve_order(cr, uid, ids, context=context)

        for ordem_obj in self.browse(cr, uid, ids, context=context):
            amount_total = D(ordem_obj.amount_total or 0)

            if amount_total > 0 and ordem_obj.state == 'approved':
                ordem_pool.gera_financeiro(cr, uid, [ordem_obj.id], context=context)
                ordem_obj.write({'state': 'done'})
            else:
                ordem_obj.write({'state': 'approved', 'aprovado_uid': uid, 'date_approve': fields.date.context_today(self,cr,uid,context=context)})

        return res

    def _dados_rateio(self, cr, uid, ids, context={}):
        rateio = {}

        for doc_obj in self.browse(cr, uid, ids):
            total = D(0)
            for item_obj in doc_obj.order_line:
                item_obj.realiza_rateio(rateio=rateio)

        return rateio

    def onchange_centrocusto_id(self, cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, partner_id=False, data_vencimento=False, data_documento=False, context={}):
        valores = {}
        res = {'value': valores}

        if not context:
            context = {}

        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        context.update({
            'partner_id': partner_id,
            'data_vencimento': data_vencimento,
            'data_documento': data_documento,
        })

        valor_documento = valor_documento or 0
        valor = valor or 0
        company_id = company_id or False
        conta_id = conta_id or False
        centrocusto_id = centrocusto_id or False

        #print('passou aqui', centrocusto_id, valor_documento, valor)

        if centrocusto_id:
            centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)

            #
            # Define os valores padrão para o rateio
            # outros valores podem vir do contexto
            #
            padrao = copy(context)
            padrao['company_id'] = company_id
            padrao['conta_id'] = conta_id
            padrao['centrocusto_id'] = centrocusto_id
            rateio = {}
            rateio = self.pool.get('finan.centrocusto').realiza_rateio(cr, uid, [centrocusto_id], context=context, rateio=rateio, padrao=padrao, valor=valor_documento)

            campos = self.pool.get('finan.centrocusto').campos_rateio(cr, uid)

            dados = []
            self.pool.get('finan.centrocusto').monta_dados(rateio, campos=campos, lista_dados=dados, valor=valor_documento)
            valores['rateio_ids'] = dados

        #
        # Força a geração de pelo menos 1 registro para a conta financeira
        #
        elif conta_id:
            rateio_ids = []
            valores['rateio_ids'] = rateio_ids

            dados = {
                'centrocusto_id': False,
                'porcentagem': 100,
                'valor_documento': valor_documento,
                'valor': valor,
                'conta_id': conta_id,
                'company_id': company_id,
            }

            rateio_ids.append([0, False, dados])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(purchase_order, self).write(cr, uid, ids, dados, context=context)

        if 'state' in dados and dados['state'] == 'cancel':
            sql = '''
            delete from finan_lancamento where purchase_order_id = {ordem_id} and provisionado = True;
            '''
            for id in ids:
                cr.execute(sql.format(ordem_id=id))

        return res

purchase_order()
