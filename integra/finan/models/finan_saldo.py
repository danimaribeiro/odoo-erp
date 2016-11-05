# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
from sql_finan_saldo import SQL_VIEW_GERAL
from pybrasil.data import hoje


class finan_saldo(osv.Model):
    _description = u'Saldos e conciliações'
    _name = 'finan.saldo'
    _rec_name = 'res_partner_bank_id'
    _order = 'data desc'
    _sql = SQL_VIEW_GERAL

    def set_lancamento_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente os lançamentos conciliados
        #
        if len(valor_campo) and len(ids):
            for saldo_obj in self.browse(cr, uid, ids):
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
                        valores['res_partner_bank_id'] = saldo_obj.res_partner_bank_id.id
                        valores['data'] = saldo_obj.data
                        self.pool.get('finan.lancamento').write(cr, uid, [lanc_id], valores)

    def get_lancamento_ids(self, cr, uid, ids, nome_campo, args, context=None):
        if not len(ids):
            return {}

        if not context:
            context = {}

        res = {}

        if nome_campo == 'pagamento_credito_ids':
            tipo = 'PR'
            tipo_data = 'data_quitacao'
        elif nome_campo == 'pagamento_debito_ids':
            tipo = 'PP'
            tipo_data = 'data_quitacao'
        elif nome_campo == 'transferencia_credito_ids':
            tipo = 'T'
            tipo_data = 'data'
        elif nome_campo == 'transferencia_debito_ids':
            tipo = 'T'
            tipo_data = 'data'
        elif nome_campo == 'transacao_credito_ids':
            tipo = 'E'
            tipo_data = 'data_quitacao'
        elif nome_campo == 'transacao_debito_ids':
            tipo = 'S'
            tipo_data = 'data_quitacao'

        for saldo_obj in self.browse(cr, uid, ids):
            if nome_campo == 'transferencia_credito_ids':
                lancamento_ids = self.pool.get('finan.lancamento').search(cr, uid, ['&', ('tipo', '=', tipo), '&', ('res_partner_bank_creditar_id', '=', saldo_obj.res_partner_bank_id.id), (tipo_data, '=', saldo_obj.data)])
            elif nome_campo == 'extrato_ids':
                lancamento_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', saldo_obj.res_partner_bank_id.id), ('data_compensacao', '=', saldo_obj.data)])
            else:
                if tipo == 'PR' or tipo == 'PP':
                    lancamento_ids = self.pool.get('finan.lancamento').search(cr, uid, ['&', ('tipo', '=', tipo), '&', ('res_partner_bank_id', '=', saldo_obj.res_partner_bank_id.id), '|', ('data', '=', saldo_obj.data), '&', ('data', '=', False), ('data_quitacao', '=', saldo_obj.data)])

                else:
                    lancamento_ids = self.pool.get('finan.lancamento').search(cr, uid, ['&', ('tipo', '=', tipo), '&', ('res_partner_bank_id', '=', saldo_obj.res_partner_bank_id.id), (tipo_data, '=', saldo_obj.data)])

            res[saldo_obj.id] = lancamento_ids

        return res

    def _soma_quantidade_lancamentos(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            transferencia_credito_ids = saldo_obj.transferencia_credito_ids
            transferencia_debito_ids = saldo_obj.transferencia_debito_ids
            transacao_credito_ids = saldo_obj.transacao_credito_ids
            transacao_debito_ids = saldo_obj.transacao_debito_ids
            pagamento_credito_ids = saldo_obj.pagamento_credito_ids
            pagamento_debito_ids = saldo_obj.pagamento_debito_ids

            quantidade_transferencia_credito = len(transferencia_credito_ids)
            quantidade_transferencia_debito = len(transferencia_debito_ids)
            quantidade_transacao_credito = len(transacao_credito_ids)
            quantidade_transacao_debito = len(transacao_debito_ids)
            quantidade_pagamento_credito = len(pagamento_credito_ids)
            quantidade_pagamento_debito = len(pagamento_debito_ids)

            quantidade_geral_credito = quantidade_pagamento_credito + quantidade_transacao_credito + quantidade_transferencia_credito
            quantidade_geral_debito = quantidade_pagamento_debito + quantidade_transacao_debito + quantidade_transferencia_debito

            quantidade_geral = quantidade_geral_credito + quantidade_geral_debito

            if nome_campo == 'quantidade_pagamento_credito':
                res[saldo_obj.id] = quantidade_pagamento_credito
            elif nome_campo == 'quantidade_pagamento_debito':
                res[saldo_obj.id] = quantidade_pagamento_debito
            elif nome_campo == 'quantidade_transacao_credito':
                res[saldo_obj.id] = quantidade_transacao_credito
            elif nome_campo == 'quantidade_transacao_debito':
                res[saldo_obj.id] = quantidade_transacao_debito
            elif nome_campo == 'quantidade_transferencia_credito':
                res[saldo_obj.id] = quantidade_transferencia_credito
            elif nome_campo == 'quantidade_transferencia_debito':
                res[saldo_obj.id] = quantidade_transferencia_debito
            elif nome_campo == 'quantidade_geral_credito':
                res[saldo_obj.id] = quantidade_geral_credito
            elif nome_campo == 'quantidade_geral_debito':
                res[saldo_obj.id] = quantidade_geral_debito
            elif nome_campo == 'quantidade_geral':
                res[saldo_obj.id] = quantidade_geral

        return res

    def _soma_total_lancamentos(self, cr, uid, ids, nome_campo, args, context=None):
        def soma_total(itens):
            total = 0
            for item in itens:
                total += item.valor
            return total

        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            transferencia_credito_ids = saldo_obj.transferencia_credito_ids
            transferencia_debito_ids = saldo_obj.transferencia_debito_ids
            transacao_credito_ids = saldo_obj.transacao_credito_ids
            transacao_debito_ids = saldo_obj.transacao_debito_ids
            pagamento_credito_ids = saldo_obj.pagamento_credito_ids
            pagamento_debito_ids = saldo_obj.pagamento_debito_ids

            total_transferencia_credito = soma_total(transferencia_credito_ids)
            total_transferencia_debito = soma_total(transferencia_debito_ids)
            total_transacao_credito = soma_total(transacao_credito_ids)
            total_transacao_debito = soma_total(transacao_debito_ids)
            total_pagamento_credito = soma_total(pagamento_credito_ids)
            total_pagamento_debito = soma_total(pagamento_debito_ids)

            total_geral_credito = total_transferencia_credito + total_transacao_credito + total_pagamento_credito
            total_geral_debito = total_transferencia_debito + total_transacao_debito + total_pagamento_debito

            total_geral = total_geral_credito - total_geral_debito

            if nome_campo == 'total_pagamento_credito':
                res[saldo_obj.id] = total_pagamento_credito
            elif nome_campo == 'total_pagamento_debito':
                res[saldo_obj.id] = total_pagamento_debito
            elif nome_campo == 'total_transacao_credito':
                res[saldo_obj.id] = total_transacao_credito
            elif nome_campo == 'total_transacao_debito':
                res[saldo_obj.id] = total_transacao_debito
            elif nome_campo == 'total_transferencia_credito':
                res[saldo_obj.id] = total_transferencia_credito
            elif nome_campo == 'total_transferencia_debito':
                res[saldo_obj.id] = total_transferencia_debito
            elif nome_campo == 'total_geral_credito':
                res[saldo_obj.id] = total_geral_credito
            elif nome_campo == 'total_geral_debito':
                res[saldo_obj.id] = total_geral_debito
            elif nome_campo == 'total_geral':
                res[saldo_obj.id] = total_geral

        return res

    def _conciliado(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            res[saldo_obj.id] = saldo_obj.quantidade_geral_conciliado == saldo_obj.quantidade_geral

        return res

    def _soma_saldo(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            #
            # Soma o saldo inicial a crédito, debito e total
            #
            sql_saldo_anterior = """
            select
                sum(e.valor_compensado_credito) as valor_compensado_credito,
                sum(e.valor_compensado_debito) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_quitacao < '%s';
            """

            #
            # Soma o saldo final a crédito, debito e total
            #
            sql_saldo = """
            select
                coalesce(sum(coalesce(e.valor_compensado_credito, 0.00)), 0.00) as valor_compensado_credito,
                coalesce(sum(coalesce(e.valor_compensado_debito, 0.00)), 0.00) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_quitacao <= '%s';
            """

            cr.execute(sql_saldo_anterior % (saldo_obj.res_partner_bank_id.id, saldo_obj.data))
            credito_anterior, debito_anterior = cr.fetchall()[0]

            if not credito_anterior:
                credito_anterior = 0

            if not debito_anterior:
                debito_anterior = 0

            saldo_anterior = credito_anterior - debito_anterior
            debito_anterior = abs(debito_anterior)

            cr.execute(sql_saldo % (saldo_obj.res_partner_bank_id.id, saldo_obj.data))
            credito, debito = cr.fetchall()[0]
            saldo = credito - debito
            debito = abs(debito)

            if nome_campo == 'saldo_credito_anterior':
                res[saldo_obj.id] = credito_anterior
            elif nome_campo == 'saldo_debito_anterior':
                res[saldo_obj.id] = debito_anterior
            elif nome_campo == 'saldo_anterior':
                res[saldo_obj.id] = saldo_anterior
            elif nome_campo == 'saldo_credito_final':
                res[saldo_obj.id] = credito
            elif nome_campo == 'saldo_debito_final':
                res[saldo_obj.id] = debito
            elif nome_campo == 'saldo_final':
                res[saldo_obj.id] = saldo

        return res

    def _pode_fechar(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            #
            # Pode fechar se é o primeiro movimento, ou se todos os anteriores
            # estão fechados
            #
            cr.execute("select count(*) from finan_saldo where res_partner_bank_id = %d and data < '%s' and (fechado = False or fechado is null)" % (saldo_obj.res_partner_bank_id.id, saldo_obj.data))
            abertos = cr.fetchall()[0][0]

            res[saldo_obj.id] = abertos == 0 and len(saldo_obj.assinatura_ids) > 1

        return res

    def _abertos_antes(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            cr.execute("select count(*) from finan_saldo where res_partner_bank_id = %d and data < '%s' and (fechado = False or fechado is null)" % (saldo_obj.res_partner_bank_id.id, saldo_obj.data))
            abertos_antes = cr.fetchall()[0][0]

            res[saldo_obj.id] = abertos_antes

        return res

    def _assinado(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            res[saldo_obj.id] = len(saldo_obj.assinatura_ids) == 1

        return res

    def get_resumo_formapagamento_ids(self, cr, uid, ids, nome_campo, args, context=None):
        if not len(ids):
            return {}

        if not context:
            context = {}

        res = {}

        for saldo_obj in self.browse(cr, uid, ids):
            resumo_ids = self.pool.get('finan.saldo.resumo.formapagamento').search(cr, uid, [('res_partner_bank_id', '=', saldo_obj.res_partner_bank_id.id), ('data_quitacao', '=', saldo_obj.data)])
            res[saldo_obj.id] = resumo_ids

        return res

    def _bank_type_get(self, cr, uid, context=None):
        bank_type_obj = self.pool.get('res.partner.bank.type')

        result = []
        type_ids = bank_type_obj.search(cr, 1, [])
        bank_types = bank_type_obj.browse(cr, 1, type_ids, context=context)
        for bank_type in bank_types:
            result.append((bank_type.code, bank_type.name))
        return result

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True),
        'res_partner_bank_state': fields.related('res_partner_bank_id', 'state', type='selection', selection=_bank_type_get, string=u'Tipo de conta bancária', store=True),
        'data': fields.date(u'Data', select=True),
        'conciliado': fields.function(_conciliado, string=u'Conciliado', method=True, type='boolean', store=False),

        'resumo_credito_ids': fields.function(get_resumo_formapagamento_ids, type='one2many', relation='finan.saldo.resumo.formapagamento', method=True, string=u'Formas de pagamento'),
        'pagamento_credito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Pagamentos a crédito', fnct_inv=set_lancamento_ids),
        'quantidade_pagamento_credito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de pagamentos a crédito', method=True, type='integer'),
        'total_pagamento_credito': fields.function(_soma_total_lancamentos, string=u'Total de pagamentos a crédito', method=True, type='float'),

        'transferencia_credito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Transferências a crédito'),
        'quantidade_transferencia_credito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de transferências a crédito', method=True, type='integer'),
        'total_transferencia_credito': fields.function(_soma_total_lancamentos, string=u'Total de transferências a crédito', method=True, type='float'),

        'transacao_credito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Transações a crédito'),
        'quantidade_transacao_credito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de transações a crédito', method=True, type='integer'),
        'total_transacao_credito': fields.function(_soma_total_lancamentos, string=u'Total de transações a crédito', method=True, type='float'),

        'saldo_credito_anterior': fields.function(_soma_saldo, string=u'Crédito anterior', method=True, type='float'),
        'saldo_credito_final': fields.function(_soma_saldo, string=u'Crédito final', method=True, type='float'),

        'pagamento_debito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Pagamentos a débito', fnct_inv=set_lancamento_ids),
        'quantidade_pagamento_debito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de pagamentos a débito', method=True, type='integer'),
        'total_pagamento_debito': fields.function(_soma_total_lancamentos, string=u'Total de pagamentos a débito', method=True, type='float'),

        'quantidade_transferencia_debito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de transferências a débito', method=True, type='integer'),
        'transferencia_debito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Transferências a débito'),
        'total_transferencia_debito': fields.function(_soma_total_lancamentos, string=u'Total de transferências a débito', method=True, type='float'),

        'quantidade_transacao_debito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade de transações a débito', method=True, type='integer'),
        'transacao_debito_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, string=u'Transações a débito'),
        'total_transacao_debito': fields.function(_soma_total_lancamentos, string=u'Total de transações a débito', method=True, type='float'),

        'saldo_debito_anterior': fields.function(_soma_saldo, string=u'Débito anterior', method=True, type='float'),
        'saldo_debito_final': fields.function(_soma_saldo, string=u'Débito final', method=True, type='float'),

        #
        # Resumos
        #
        'quantidade_geral_credito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade a crédito', method=True, type='integer'),
        'total_geral_credito': fields.function(_soma_total_lancamentos, string=u'Total a crédito', method=True, type='float', store=True),
        'quantidade_geral_debito': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade a débito', method=True, type='integer'),
        'total_geral_debito': fields.function(_soma_total_lancamentos, string=u'Total a débito', method=True, type='float', store=True),
        'quantidade_geral': fields.function(_soma_quantidade_lancamentos, string=u'Quantidade geral', method=True, type='integer'),
        'saldo_anterior': fields.function(_soma_saldo, string=u'Saldo anterior', method=True, type='float' , store=True),
        'saldo_final': fields.function(_soma_saldo, string=u'Saldo final', method=True, type='float', store=True),
        'fechado': fields.boolean(u'Fechado?'),
        'pode_fechar': fields.function(_pode_fechar, string=u'Pode fechar?', method=True, type='boolean'),
        'abertos_antes': fields.function(_abertos_antes, string=u'Abertos antes', method=True, type='integer'),
        'assinado': fields.function(_assinado, string=u'Assinado?', method=True, type='boolean'),

        'extrato_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.extrato', method=True, string=u'Extrato'),
        'assinatura_ids': fields.one2many('finan.saldo.assinatura', 'saldo_id', u'Assinaturas'),

        #
        # Filtros
        #
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data de'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'até'),
        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
    }

    _default = {
        'fechado': False,
    }

    _sql_constraints = [
        ('res_partner_bank_id_data_unique', 'unique(res_partner_bank_id, data)',
            u'O banco e a data não podem se repetir!'),
    ]

    def atualizar_caixa(self, cr, uid, ids, context):
        return True

    def gera_assinatura(self, cr, uid, ids, context):
        assinatura_pool = self.pool.get('finan.saldo.assinatura')

        for id in ids:
            dados = {
                'saldo_id': id,
                'user_id': uid,
                'data': fields.datetime.now()
            }

            assinatura_pool.create(cr, uid, dados)

    def fecha_movimento(self, cr, uid, ids, context):
        for saldo_obj in self.browse(cr, uid, ids):
            saldo_obj.write({'fechado': True})

    def abre_movimento(self, cr, uid, ids, context):
        for saldo_obj in self.browse(cr, uid, ids):
            saldo_obj.write({'fechado': False})

    def write(self, cr, uid, ids, dados, context=None):
        for saldo_obj in self.browse(cr, uid, ids):
            if saldo_obj.fechado:
                raise osv.except_osv(u'Erro!', u'Você não pode alterar o movimento já fechado!')

        res = super(finan_saldo, self).write(cr, uid, ids, dados, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        for saldo_obj in self.browse(cr, uid, ids):
            if saldo_obj.fechado:
                raise osv.except_osv(u'Erro!', u'Você não pode excluir o movimento já fechado!')

        res = super(finan_saldo, self).unlink(cr, uid, ids, context)
        return res

    def imprime_movimento(self, cr, uid, ids, context={}):
        res_partner_bank_id = context.get('res_partner_bank_id', False)
        data = context.get('data', False)

        if not res_partner_bank_id or not data:
            return

        dados = {
            'data_inicial': data,
            'data_final': data,
            'res_partner_bank_id': res_partner_bank_id,
        }

        rel_id = self.pool.get('finan.relatorio').create(cr, 1, dados)
        rel_obj = self.pool.get('finan.relatorio').browse(cr, 1, rel_id)
        rel_obj.gera_relatorio_movimentacao_financeira(context={'data_inicial': data, 'data_final': data, 'res_partner_bank_id': res_partner_bank_id})

        pdf = rel_obj.arquivo

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.saldo'), ('res_id', '=', ids[0]), ('name', '=', 'movimentacao_financeira.pdf')])
        #
        # Apaga os boletos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            #'datas': base64.encodestring(pdf),
            'datas': pdf,
            'name': 'movimentacao_financeira.pdf',
            'datas_fname': 'movimentacao_financeira.pdf',
            'res_model': 'finan.saldo',
            'res_id': ids[0],
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

    def onchange_res_partner_bank_id(self, cr, uid, ids, res_partner_bank_id, data, context={}):
        if (not res_partner_bank_id) or data:
            return {}

        valores = {}
        res = {'value': valores}
        filtro = {
            'bank_id': res_partner_bank_id,
        }

        #
        # Busca a última data com lançamento, que ainda não tenha caixa
        #
        sql = """
            select
                s.data
            from
                finan_saldo s
            where
                s.res_partner_bank_id = {bank_id}
            order by
                s.data desc
            limit 1;
        """
        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        ultima_data = None
        if len(dados):
            ultima_data = dados[0][0]
            filtro['ultima_data'] = ultima_data

        #
        # Agora, vamos busca o último lançamento com esse banco, que seja posterior
        # a data do último caixa, ou o primeiro lançamento existente para a conta
        #
        sql = """
            select
                l.data_quitacao
            from
                finan_lancamento l
            where
                l.tipo in ('T', 'E', 'S', 'PP', 'PR')
                and (l.res_partner_bank_id = {bank_id}
                or l.res_partner_bank_creditar_id = {bank_id})
        """

        if ultima_data:
            sql += """
                and l.data_quitacao > '{ultima_data}'
            """

        sql += """
            order by
                l.data_quitacao
            limit 1
        """
        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados):
            valores['data'] = dados[0][0]

        return res

    def cria_fechamentos_gerais(self, cr, uid, ids=[], context={}):
        saldo_pool = self.pool.get('finan.saldo')

        sql = '''
            select distinct
                e.res_partner_bank_id,
                case
                    when e.data_compensacao is not null then e.data_compensacao
                    else e.data_quitacao
                end as data

            from finan_extrato e
            join finan_lancamento l on l.id = e.lancamento_id
            left join finan_saldo s on s.res_partner_bank_id = e.res_partner_bank_id and s.data =
                case
                    when e.data_compensacao is not null then e.data_compensacao
                    else e.data_quitacao
                end

            where e.tipo != 'I'
            -- and (cast(l.create_date as date) >= current_date or cast(l.write_date as date) >= current_date)
            and s.id is null

            order by
                2,
                1;
        '''

        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados):
            for bank_id, data in dados:
                novo = {
                    'res_partner_bank_id': bank_id,
                    'data': data,
                }

                saldo_pool.create(cr, uid, novo)

        #
        # Exclui saldos de períodos sem movimento
        #
        sql = """
            select
                s.id

            from finan_saldo s
            left join finan_extrato e on s.res_partner_bank_id = e.res_partner_bank_id and s.data =
                case
                    when e.data_compensacao is not null then e.data_compensacao
                    else e.data_quitacao
                end

            where
                e.id is null
                and coalesce(s.fechado, False) = False

            limit 1;
        """
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados):
            for id, in dados:
                saldo_pool.unlink(cr, uid, [id])

        return True


finan_saldo()


class finan_saldo_assinatura(osv.Model):
    _name = 'finan.saldo.assinatura'
    _order = 'data desc'

    _columns = {
        'saldo_id': fields.many2one('finan.saldo', u'Saldo'),
        'user_id': fields.many2one('res.users', u'Usuário'),
        'data': fields.datetime(u'Data'),
    }

    _default = {
        'user_id': lambda self, cr, uid, context: uid,
        'data': fields.datetime.now,
    }

    # Por solicitação do Ari foi removido a constraint.

    #_sql_constraints = [
    #    ('finan_saldo_assinatura_unique', 'unique(saldo_id, user_id)',
    #        u'O mesmo usuário não pode assinar 2 vezes o mesmo saldo!'),
    #]


finan_saldo_assinatura()


class finan_extrato(osv.Model):
    _name = 'finan.extrato'
    _order = 'data_quitacao, valor_compensado_credito desc, valor_compensado_debito desc'
    _auto = False

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'tipo': fields.selection((('T', u'Transferência'), ('R', u'Pagamento recebido'), ('P', u'Pagamento efetuado'), ('I', u'Saldo inicial'), ('E', u'Transação entrada'), ('S', u'Transação saída')), string=u'Tipo'),
        'data_quitacao': fields.date(u'Data de pagamento'),
        'data_compensacao': fields.date(u'Data de compensação'),
        'valor_compensado_credito': fields.float(u'Crédito'),
        'valor_compensado_debito': fields.float(u'Débito'),
        'conciliado': fields.boolean(u'Conciliado'),
    }


finan_extrato()


class finan_conciliacao(osv.Model):
    _name = 'finan.conciliacao'
    _order = 'data_final desc'

    def set_lancamento_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente os lançamentos conciliados
        #
        if not isinstance(ids, list):
            if ids:
                ids = [ids]
            else:
                ids = []

        if len(valor_campo) and len(ids):
            for saldo_obj in self.browse(cr, uid, ids):
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
                    if operacao == 1:
                        #
                        # Ajusta o banco e a data de crédito para a data do lançamento do saldo
                        #
                        self.pool.get('finan.lancamento').write(cr, uid, [lanc_id], valores, context={'conciliacao': True})

    def get_lancamento_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        for conc_obj in self.browse(cr, uid, ids):
            conc_obj = self.browse(cr, uid, ids[0])
            res_partner_bank_id = conc_obj.res_partner_bank_id.id
            data_inicial = conc_obj.data_inicial
            data_final = conc_obj.data_final

            lanc_ids = []
            if nome_campo == 'lancamento_a_conciliar_ids':
                conciliado = False
                #lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('conciliado', '=', conciliado), ('id', '>', 0)])
                lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('conciliado', '=', conciliado), ('id', '>', 0)])
                #lancamento_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_quitacao', '>=', data_inicial), ('data_quitacao', '<=', data_final), ('conciliado', '=', conciliado)])

            else:
                conciliado = True
                data_inicial = data_final
                #lancamento_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_quitacao', '>=', data_inicial), ('data_quitacao', '<=', data_final), ('conciliado', '=', conciliado)])
                #lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_compensacao', '>=', data_inicial), ('data_compensacao', '<=', data_final), ('conciliado', '=', conciliado), ('id', '>', 0)])
                lanc_ids = self.pool.get('finan.extrato').search(cr, uid, [('res_partner_bank_id', '=', res_partner_bank_id), ('data_compensacao', '>=', data_inicial), ('data_compensacao', '<=', data_final), ('conciliado', '=', conciliado)])


            lancamento_ids = []
            for id in lanc_ids:
                lancamento_ids.append(abs(id))
                #lancamento_ids[i] = abs(lancamento_ids[i])

            res[conc_obj.id] = lancamento_ids

        print(res)
        return res

    def _soma_saldo(self, cr, uid, ids, nome_campo, args, context=None):
        if ids:
            conc_obj = self.browse(cr, uid, ids[0])
            res_partner_bank_id = conc_obj.res_partner_bank_id.id
            data_inicial = conc_obj.data_inicial
            data_final = conc_obj.data_final

        else:
            if 'res_partner_bank_id' not in context:
                return 0
            elif 'data_inicial' not in context:
                return 0
            elif 'data_final' not in context:
                return 0

            res_partner_bank_id = context['res_partner_bank_id']
            data_inicial = context['data_inicial']
            data_final = context['data_final']

        #if not res_partner_bank_id or not data_inicial or not data_final:
        if not res_partner_bank_id or not data_final:
            return 0

        data_inicial = data_final

        sql_saldo_movimento = """
            select
                coalesce(sum(e.valor_compensado_credito), 0) as valor_compensado_credito,
                coalesce(sum(e.valor_compensado_debito), 0) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_quitacao between '%s' and '%s';
            """

        sql_saldo_conciliado = """
            select
                coalesce(sum(e.valor_compensado_credito), 0) as valor_compensado_credito,
                coalesce(sum(e.valor_compensado_debito), 0) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_quitacao between '%s' and '%s'
                and e.conciliado = True;
            """

        sql_saldo_banco = """
            select
                coalesce(sum(e.valor_compensado_credito), 0) as valor_compensado_credito,
                coalesce(sum(e.valor_compensado_debito), 0) as valor_compensado_debito
            from
                finan_extrato e
            where
                e.res_partner_bank_id = %d
                and e.data_compensacao <= '%s'
                and e.conciliado = True;
            """

        cr.execute(sql_saldo_movimento % (res_partner_bank_id, data_inicial, data_final))
        credito_movimento, debito_movimento = cr.fetchall()[0]
        saldo_movimento = credito_movimento - debito_movimento

        cr.execute(sql_saldo_conciliado % (res_partner_bank_id, data_inicial, data_final))
        credito, debito = cr.fetchall()[0]
        saldo = credito - debito

        cr.execute(sql_saldo_banco % (res_partner_bank_id, data_final))
        credito, debito = cr.fetchall()[0]
        saldo_banco = credito - debito

        if nome_campo == 'saldo_movimento':
            valor = saldo_movimento
        elif nome_campo == 'saldo_conciliado':
            valor = saldo
        elif nome_campo == 'saldo_banco':
            valor = saldo_banco
        else:
            valor = saldo_movimento - saldo

        if ids:
            res = {}
            for id in ids:
                res[id] = valor
        else:
            res = valor

        print(res)

        return res

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'lancamento_conciliado_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, fnct_inv=set_lancamento_ids),
        'lancamento_a_conciliar_ids': fields.function(get_lancamento_ids, type='one2many', relation='finan.lancamento', method=True, fnct_inv=set_lancamento_ids),
        'saldo_movimento': fields.function(_soma_saldo, type='float', string=u'Total movimentado no período'),
        'saldo_conciliado': fields.function(_soma_saldo, type='float', string=u'Total conciliado no período'),
        'saldo_banco': fields.function(_soma_saldo, type='float', string=u'Saldo no banco ao fim do período'),
        'diferenca': fields.function(_soma_saldo, type='float', string=u'Diferença a conciliar no período'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),
        'write_date': fields.datetime( u'Data Alteração'),
    }

    def onchange_busca_lancamento_ids(self, cr, uid, ids, res_partner_bank_id, data_inicial, data_final):
        context = {
            'res_partner_bank_id': res_partner_bank_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
        }

        lancamento_a_conciliar_ids = self.get_lancamento_ids(cr, uid, ids, 'lancamento_a_conciliar_ids', None, context)
        lancamento_conciliado_ids = self.get_lancamento_ids(cr, uid, ids, 'lancamento_conciliado_ids', None, context)
        saldo_movimento = self._soma_saldo(cr, uid, ids, 'saldo_movimento', None, context)
        saldo_conciliado = self._soma_saldo(cr, uid, ids, 'saldo_conciliado', None, context)
        saldo_banco = self._soma_saldo(cr, uid, ids, 'saldo_banco', None, context)
        diferenca = self._soma_saldo(cr, uid, ids, 'diferenca', None, context)

        res = {'value': {
            'lancamento_a_conciliar_ids': lancamento_a_conciliar_ids,
            'lancamento_conciliado_ids': lancamento_conciliado_ids,
            'saldo_movimento': saldo_movimento,
            'saldo_conciliado': saldo_conciliado,
            'saldo_banco': saldo_banco,
            'diferenca': diferenca,
            }
        }

        print('+', res)

    def recalcula_conciliacao(self, cr, uid, ids, context={}):
        print('entrou aqui', context)

        lancamento_a_conciliar_ids = self.get_lancamento_ids(cr, uid, ids, 'lancamento_a_conciliar_ids', None, context)
        lancamento_conciliado_ids = self.get_lancamento_ids(cr, uid, ids, 'lancamento_conciliado_ids', None, context)
        saldo_movimento = self._soma_saldo(cr, uid, ids, 'saldo_movimento', None, context)
        saldo_conciliado = self._soma_saldo(cr, uid, ids, 'saldo_conciliado', None, context)
        saldo_banco = self._soma_saldo(cr, uid, ids, 'saldo_banco', None, context)
        diferenca = self._soma_saldo(cr, uid, ids, 'diferenca', None, context)

        res =  {'value': {
            #'lancamento_a_conciliar_ids': lancamento_a_conciliar_ids,
            #'lancamento_conciliado_ids': lancamento_conciliado_ids,
            #'saldo_movimento': saldo_movimento,
            #'saldo_conciliado': saldo_conciliado,
            #'saldo_banco': saldo_banco,
            #'diferenca': diferenca,
            }
        }

        print(res)

        return False

    def create(self, cr, uid, vals, context={}):
        res = super(finan_conciliacao, self).create(cr, uid, vals, context)

        #self.unlink(cr, uid, res)

        return res


finan_conciliacao()


class finan_saldo_resumo_formapagamento(osv.Model):
    _description = u'Resumo de pagamentos'
    _name = 'finan.saldo.resumo.formapagamento'
    _rec_name = 'res_partner_bank_id'
    _order = 'formapagamento_id desc'
    _auto = False

    _columns = {
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta'),
        'data_quitacao': fields.date(u'Data', select=True),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'valor': fields.float(u'Valor'),
    }


finan_saldo_resumo_formapagamento()
