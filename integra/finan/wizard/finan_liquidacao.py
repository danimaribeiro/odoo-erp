# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
from sped.models.fields import CampoDinheiro


class finan_liquidacao(osv.osv_memory):
    _description = u'Liquidação de lançamentos'
    _name = 'finan.liquidacao'
    _rec_name = 'numero_documento'
    _order = 'data'

    def set_lancamento_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        if isinstance(ids, int):
            ids = [ids]

        #
        # Salva manualmente os lançamentos conciliados
        #
        if len(valor_campo) and len(ids):
            for liquidacao_obj in self.browse(cr, uid, ids):
                for operacao, lanc_id, valores in valor_campo:
                    #
                    # Cada lanc_item tem o seguinte formato
                    # [operacao, id_original, valores_dos_campos]
                    #
                    # operacao pode ser:
                    # 0 - criar novo registro (no caso aqui, vai ser ignorado)
                    # 1 - alterar o registro
                    # 2 - excluir o registro (também vai ser ignorado)
                    # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
                    # 4 - vincular a um registro existente
                    #
                    if operacao == '1':
                        #
                        # Ajusta o banco e a data de crédito para a data do lançamento do saldo
                        #
                        valores['res_partner_bank_id'] = liquidacao_obj.res_partner_bank_id.id
                        #valores['data'] = liquidacao_obj.data
                        self.pool.get('finan.lancamento').write(cr, uid, [lanc_id], valores)

    def get_pago_ids(self, cr, uid, ids, nome_campo, args, context={}):
        lancamento_ids = context.get('active_ids', [])

        print(context)
        print('pago_ids', lancamento_ids)

        if ids:
            res = {}
            for id in ids:
                res[id] = lancamento_ids
        else:
            res = lancamento_ids

        return res

    _columns = {
        #
        # Data e valor de caixa - movimentação do banco
        #
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária'),
        'company_id': fields.many2one('res.company', u'Empresa/unidade'),
        'data': fields.date(u'Data'),
        'valor_total': CampoDinheiro(u'Valor total'),
        'lote_id': fields.many2one('finan.lancamento', u'Lote de pagamento'),
        'pago_ids': fields.function(get_pago_ids, type='one2many', relation='finan.lancamento', string=u'Pagos', fnct_inv=set_lancamento_ids),
        'pagamento_ids': fields.one2many('finan.lancamento', 'liquidacao_id', u'Pagamentos'),

        ##
        ## Dados necessários para controle de quitação
        ##
        'data_quitacao': fields.date(u'Data de quitação'),
        #'data_baixa': fields.date(u'Data de baixa'),

        ##
        ## Para contas a receber e a pagar, juros, descontos ou multa
        ##
        'valor_juros': CampoDinheiro(u'Juros'),
        'valor_desconto': CampoDinheiro(u'Desconto'),
        'valor_multa': CampoDinheiro(u'Multa'),
        'outros_acrescimos': CampoDinheiro(u'Outros acréscimos'),
        'outros_debitos': CampoDinheiro(u'Outros débitos'),
    }

    _defaults = {
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_quitacao': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        #'data_baixa': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def prepara_liquidacao(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        pago_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')
        res_partner_bank_id = context['res_partner_bank_id']
        tipo = lancamento_pool.browse(cr, uid, pago_ids[0]).tipo
        company_id = lancamento_pool.browse(cr, uid, pago_ids[0]).company_id.id
        partner_id = lancamento_pool.browse(cr, uid, pago_ids[0]).partner_id.id

        #
        # Fazemos uma pré-validação das informações
        #
        valor_total = 0
        for lancamento_obj in lancamento_pool.browse(cr, uid, pago_ids, context):
            if lancamento_obj.data or lancamento_obj.valor or lancamento_obj.data_quitacao:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos liquidados anteriormente!')

            if lancamento_obj.data_baixa:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos baixados anteriormente!')

            if res_partner_bank_id and lancamento_obj.res_partner_bank_id and lancamento_obj.res_partner_bank_id.id != res_partner_bank_id:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação, informando a conta bancária, em lançamentos vinculados a contas bancárias diferentes!')

            if lancamento_obj.tipo != tipo:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação, liquidando lançamentos a pagar e a receber ao mesmo tempo!')

            if lancamento_obj.tipo in ['LP', 'LR', 'E', 'S', 'T']:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação nesse tipo de lançamento!')

            if lancamento_obj.company_id.id != company_id:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação com lançamentos de várias empresas!')

            if lancamento_obj.partner_id.id != partner_id:
                osv.except_osv(u'Atenção', u'Não é possível realizar a operação com lançamentos de várias clientes/fornecedores!')

            #
            # Acumula o valor total dos lançamentos a liquidar
            #
            valor_total += lancamento_obj.valor_saldo
            valor_total += lancamento_obj.valor_juros
            valor_total += lancamento_obj.valor_multa
            valor_total += lancamento_obj.outros_acrescimos
            valor_total -= lancamento_obj.valor_desconto
            valor_total -= lancamento_obj.outros_debitos

        self.write(cr, uid, ids, {'valor_total': valor_total})

    def quita_lancamentos(self, cr, uid, ids, context=None):
        self.prepara_liquidacao(cr, uid, ids, context)

        liquidacao_obj = self.browse(cr, uid, ids[0])
        lancamento_pool = self.pool.get('finan.lancamento')
        pagamento_ids = context['pagamento_ids']
        print('pagamento_ids', pagamento_ids)
        pago_ids = context['pago_ids']
        print('pago_ids', pago_ids)

        total_pagamentos = 0
        total_pago = 0
        total_juros = 0
        total_desconto = 0
        total_multa = 0
        for operacao, pag_id, valores in pagamento_ids:
            pag_obj = lancamento_pool.browse(cr, uid, pag_id)
            total_pagamentos += pag_obj.valor_documento
            total_pago += pag_obj.valor
            total_multa += pag_obj.valor_multa
            total_juros += pag_obj.valor_juros
            total_desconto += pag_obj.valor_desconto

        if total_pagamentos != liquidacao_obj.valor_total:
            osv.except_osv(u'Erro!', u'Não é possível realizar liquidação múltipla com valor parcial!')

        #
        # Agora que o total pago bate com o total devido, gerar o lote, e ajustar os valores
        #
        tipo = lancamento_pool.browse(cr, uid, pago_ids[0][1]).tipo
        company_id = lancamento_pool.browse(cr, uid, pago_ids[0][1]).company_id.id
        partner_id = lancamento_pool.browse(cr, uid, pago_ids[0][1]).partner_id.id

        if tipo == 'R':
            tipo_lote = 'LR'
        elif tipo == 'P':
            tipo_lote = 'LP'

        dados_lote = {
            'company_id': company_id,
            'tipo': tipo_lote,
            'data_quitacao': liquidacao_obj.data_quitacao,
            'data_documento': liquidacao_obj.data_quitacao,
            'numero_documento': tipo_lote + ' ' + str(fields.datetime.now()),
            'partner_id': partner_id,
            'valor_documento': liquidacao_obj.valor_total,
            'situacao': 'Quitado',
            'res_partner_bank_id': liquidacao_obj.res_partner_bank_id.id,
            'valor_juros': total_juros,
            'valor_multa': total_multa,
            'valor_desconto': total_desconto,
            'valor': total_pago,
        }

        lote_id = lancamento_pool.create(cr, uid, dados_lote)

        #
        # Salva os pagamentos
        #
        if tipo == 'P':
            tipo_pagamento = 'PP'
        else:
            tipo_pagamento = 'PR'

        for operacao, pag_id, valores in pagamento_ids:
            lancamento_pool.write(cr, uid, [pag_id], {'lancamento_id': lote_id, 'partner_id': partner_id, 'tipo': tipo_pagamento, 'company_id': liquidacao_obj.company_id.id})

        #
        # Quita os itens que estão sendo pagos
        #
        dados_quitacao = {}
        for operacao, pag_id, valores in pago_ids:
            lanc_obj = lancamento_pool.browse(cr, uid, pag_id)

            dados_quitacao = {
                'data_quitacao': liquidacao_obj.data_quitacao,
                'valor': lanc_obj.valor_documento,
                'res_partner_bank_id': liquidacao_obj.res_partner_bank_id.id,
                'situacao': 'Quitado',
                'lancamento_id': lote_id,
                'valor_saldo': 0,
            }
            lanc_obj.write(dados_quitacao)

            #
            # Agora, ajusta o rateio, se houver
            #
            dados_quitacao['rateio_ids'] = lancamento_pool.recalcula_rateio(cr, uid, pag_id)
            lanc_obj.write(dados_quitacao)

        return {'type': 'ir.actions.act_window_close'}

    def onchange_company_banco (self, cr, uid, ids, res_partner_bank_id):
        valores = {}
        retorno = {'value': valores}
        if not res_partner_bank_id:
            return res

        res_partner_bank_obj = self.pool.get('res.partner.bank').browse(cr, uid, res_partner_bank_id)
        valores['company_id'] = res_partner_bank_obj.company_id.id

        return retorno


finan_liquidacao()


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'liquidacao_id': fields.integer(u'Liquidação pai', select=True),
    }


finan_lancamento()
