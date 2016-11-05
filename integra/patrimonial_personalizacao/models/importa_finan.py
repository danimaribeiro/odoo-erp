# -*- encoding: utf-8 -*-


from decimal import Decimal as D
from osv import osv, fields
from plano_contas_antigo import PLANO_CONTAS
from copy import copy
from pybrasil.valor.decimal import Decimal as D


class importa_finan(osv.Model):
    _name = 'importa.finan'
    _description = u'Importação do financeiro'

    _columns = {
        'cnpj_empresa': fields.char(u'CNPJ empresa', size=18, select=True),
        'cnpj_partner': fields.char(u'CNPJ parceiro', size=18, select=True),
        'tipo': fields.selection([('R', u'Receber'), ('P', u'Pagar'), ('PR', u'Pagamento recebido'), ('PP', u'Pagamento efetuado')], u'Tipo', select=True),

        'company_id': fields.many2one('res.company', u'Empresa', required=False, select=True, ondelete='restrict'),
        'conta_antiga': fields.selection(PLANO_CONTAS, u'Conta antiga', select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', select=True, ondelete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True, ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', u'Parceiro', select=True, ondelete='restrict'),

        'data_vencimento': fields.date(u'Data de vencimento', select=True),
        'numero_documento': fields.char(u'Número do documento', size=30, select=True),
        'data_documento':  fields.date(u'Data do documento'),
        'valor_documento': fields.float(u'Valor do documento'),

        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', select=True, ondelete='restrict'),
        'nosso_numero': fields.char(u'Nosso número', size=20),
        'data_boleto': fields.date(u'Data do boleto'),

        #
        # Para contas a receber e a pagar, juros, descontos ou multa
        #
        'valor_juros': fields.float(u'Juros'),
        'valor_desconto': fields.float(u'Desconto'),
        'valor_multa': fields.float(u'Multa'),
        'outros_acrescimos': fields.float(u'Outros acréscimos'),
        'outros_debitos': fields.float(u'Outros débitos'),
        'valor_saldo': fields.float(string=u'Saldo em aberto'),
        'data_ultimo_pagamento': fields.date(u'Último pagamento'),

        'data_quitacao': fields.date(u'Data pagamento'),
        'valor': fields.float(u'Valor pago'),
        'data': fields.date(u'Data compensação'),

        'divida_id': fields.many2one('importa.finan', u'Dívida'),
        'pagamento_ids': fields.one2many('importa.finan', 'divida_id', u'Pagamentos'),

        #
        # Lançamento correspondente no financeiro
        #
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento'),
    }

    def gera_financeiro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if 'active_ids' in context:
            ids = context['active_ids']

        finan_pool = self.pool.get('finan.lancamento')
        cc_pool = self.pool.get('finan.centrocusto')

        for if_obj in self.browse(cr, uid, ids):
            #
            # Verifica se já foi criado o lançamento
            #
            if if_obj.lancamento_id:
                continue

            if if_obj.tipo in ['PP', 'PR']:
                if not if_obj.divida_id:
                    continue

                if not if_obj.divida_id.lancamento_id:
                    continue

            else:
                if not if_obj.company_id:
                    continue

                if not if_obj.partner_id:
                    continue

                if not if_obj.documento_id:
                    continue

                if not if_obj.conta_id:
                    continue

            if if_obj.tipo in ['P', 'R']:
                dados = {
                    'company_id': if_obj.company_id.id,
                    'tipo': if_obj.tipo,
                    'provisionado': False,
                    'conta_id': if_obj.conta_id.id,
                    'documento_id': if_obj.documento_id.id,
                    'partner_id': if_obj.partner_id.id,
                    'data_vencimento': if_obj.data_vencimento,
                    'numero_documento': if_obj.numero_documento,
                    'data_documento': if_obj.data_documento[:10],
                    'valor_documento': D(if_obj.valor_documento),
                    'carteira_id': if_obj.carteira_id.id if if_obj.carteira_id else False,
                    'res_partner_bank_id': if_obj.carteira_id.res_partner_bank_id.id if if_obj.carteira_id else False,
                }

                nosso_numero = if_obj.nosso_numero
                if nosso_numero and if_obj.carteira_id and if_obj.carteira_id.res_partner_bank_id.bank_bic == '237':
                    if nosso_numero.startswith('109'):
                        nosso_numero = nosso_numero[3:]

                    nosso_numero = nosso_numero[:-1]
                    nosso_numero = str(int(nosso_numero))

                dados['nosso_numero'] = nosso_numero
            else:
                dados = {
                    'company_id': if_obj.divida_id.company_id.id,
                    'tipo': if_obj.tipo,
                    'provisionado': False,
                    'conta_id': if_obj.divida_id.conta_id.id,
                    'documento_id': if_obj.divida_id.documento_id.id,
                    'partner_id': if_obj.divida_id.partner_id.id,
                    'data_vencimento': if_obj.divida_id.data_vencimento,
                    'numero_documento': if_obj.divida_id.numero_documento,
                    'data_documento': if_obj.divida_id.data_documento[:10],
                    'valor_documento': if_obj.valor_documento,
                    'valor_juros': if_obj.valor_juros,
                    'valor_multa': if_obj.valor_multa,
                    'valor_desconto': if_obj.valor_desconto,
                    'data_quitacao': if_obj.data_quitacao,
                    'data': if_obj.data,
                    'lancamento_id': if_obj.divida_id.lancamento_id.id,
                }
                valor = if_obj.valor_documento
                valor += if_obj.valor_juros or 0
                valor += if_obj.valor_multa or 0
                valor -= if_obj.valor_desconto or 0
                dados['valor'] = valor

                res_partner_bank_id = if_obj.res_partner_bank_id.id if if_obj.res_partner_bank_id else False
                if not res_partner_bank_id and if_obj.carteira_id:
                    res_partner_bank_id = if_obj.divida_id.carteira_id.res_partner_bank_id.id

                dados['res_partner_bank_id'] = res_partner_bank_id

            #
            # Verifica se o nº já existe
            #
            busca = [
                ('tipo', '=', dados['tipo']),
                ('partner_id', '=', dados['partner_id']),
                ('numero_documento', '=', dados['numero_documento']),
            ]
            lancamento_ids = finan_pool.search(cr, uid, busca)
            if len(lancamento_ids):
                #
                # Já existe
                #
                lancamento_id = lancamento_ids[0]
                lancamento_obj = finan_pool.browse(cr, uid, lancamento_id)
                dados_juntos = {
                    'valor_documento': dados['valor_documento'] + D(lancamento_obj.valor_documento),
                    #'valor_juros': dados['valor_juros'] + lancamento_obj.valor_juros,
                    #'valor_multa': dados['valor_multa'] + lancamento_obj.valor_multa,
                    #'valor_desconto': dados['valor_desconto'] + lancamento_obj.valor_desconto,
                    #'valor': dados['valor'] + lancamento_obj.valor,
                }

                vr_total = dados['valor_documento'] + D(lancamento_obj.valor_documento)
                vr_total = D(vr_total)

                #
                # Ajusta o rateio
                #
                rateio = {}
                campos = cc_pool.campos_rateio(cr, uid)
                padrao = copy(dados)
                cc_pool._realiza_rateio(vr_total, dados['valor_documento'] / vr_total * 100.00, campos, padrao, rateio)

                for rateio_obj in lancamento_obj.rateio_ids:
                    padrao = copy(dados)
                    padrao['conta_id'] = rateio_obj.conta_id.id
                    cc_pool._realiza_rateio(vr_total, D(rateio_obj.valor_documento) / vr_total * 100.00, campos, padrao, rateio)

                lancamento_obj.write(dados_juntos)
                for rateio_obj in lancamento_obj.rateio_ids:
                    rateio_obj.unlink()

                dados_rateio = []
                cc_pool.monta_dados(rateio, lista_dados=dados_rateio, valor=vr_total, campos=campos)
                print('dados_rateio', dados_rateio)

                rateio_ids = []
                for rateio_dic in dados_rateio:
                    rateio_ids.append([0, False, rateio_dic])

                lancamento_obj.write({'rateio_ids': rateio_ids})
                if_obj.write({'lancamento_id': lancamento_id})

            else:
                lancamento_id = finan_pool.create(cr, uid, dados)
                if_obj.write({'lancamento_id': lancamento_id})

                if if_obj.tipo in ['R', 'P'] and len(if_obj.pagamento_ids):
                    data_quitacao = False
                    for p_obj in if_obj.pagamento_ids:
                        self.gera_financeiro(cr, uid, [p_obj.id])
                        if not data_quitacao:
                            data_quitacao = p_obj.data_quitacao
                        elif p_obj.data_quitacao > data_quitacao:
                            data_quitacao = p_obj.data_quitacao

                    lanc_obj = finan_pool.browse(cr, uid, lancamento_id)
                    lanc_obj.write({'data_ultimo_pagamento': data_quitacao})

                lanc_obj = finan_pool.browse(cr, uid, lancamento_id)
                dados = lanc_obj.onchange_conta_id(lanc_obj.conta_id.id, lanc_obj.company_id.id, False, lanc_obj.valor_documento, lanc_obj.valor, partner_id=lanc_obj.partner_id.id, data_vencimento=lanc_obj.data_vencimento, data_documento=lanc_obj.data_documento)
                if 'value' in dados and 'rateio_ids' in dados['value']:
                    lanc_obj.write(dados['value'])

        return False

    def replica_conta(self, cr, uid, ids, context={}):
        if not ids:
            return

        ja_feitos = []

        for if_obj in self.browse(cr, uid, ids):
            if if_obj.conta_antiga in ja_feitos:
                continue

            if not if_obj.conta_id:
                continue

            cr.execute('update importa_finan set conta_id = {conta_id} where conta_antiga = {conta_antiga} and conta_id is null;'.format(conta_id=if_obj.conta_id.id, conta_antiga=if_obj.conta_antiga))
            ja_feitos.append(if_obj.conta_antiga)

        return True

    def replica_parceiro(self, cr, uid, ids, context={}):
        if not ids:
            return

        ja_feitos = []

        for if_obj in self.browse(cr, uid, ids):
            if if_obj.cnpj_partner in ja_feitos:
                continue

            if not if_obj.partner_id:
                continue

            cr.execute("update importa_finan set partner_id = {partner_id} where cnpj_partner = '{cnpj_partner}' and partner_id is null;".format(partner_id=if_obj.partner_id.id, cnpj_partner=if_obj.cnpj_partner))
            ja_feitos.append(if_obj.cnpj_partner)

        return True

    def replica_company(self, cr, uid, ids, context={}):
        if not ids:
            return

        ja_feitos = []

        for if_obj in self.browse(cr, uid, ids):
            if if_obj.cnpj_empresa in ja_feitos:
                continue

            if not if_obj.company_id:
                continue

            cr.execute("update importa_finan set company_id = {company_id} where cnpj_empresa = '{cnpj_empresa}' and company_id is null;".format(company_id=if_obj.company_id.id, cnpj_empresa=if_obj.cnpj_empresa))
            ja_feitos.append(if_obj.cnpj_empresa)

        return True

importa_finan()
