# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes
from finan_contrato import NATUREZA


class finan_contrato_reajuste(osv.Model):
    _description = u'Contrato - Reajuste'
    _name = 'finan.contrato.reajuste'
    _order = 'data_reajuste desc'

    _columns = {
        'natureza': fields.selection(NATUREZA, u'Natureza'),
        'currency_id': fields.many2one('res.currency', u'Índice', ondelete='restrict'),
        'company_id': fields.many2one('res.company', u'Empresa/Grupo', ondelete='restrict'),
        'data_reajuste': fields.date(u'Data do reajuste'),
        'partner_id': fields.many2one('res.partner', u'Cliente/Fornecedor', ondelete='restrict'),
        'contrato_excecoes_ids': fields.many2many('finan.contrato', 'finan_contrato_reajuste_excecao', 'reajuste_id', 'contrato_id', u'Exceções ao reajuste'),
        'contrato_reajustar_ids': fields.one2many('finan.contrato.reajuste.contrato', 'reajuste_id', u'Contratos a reajustar'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'ignorar_centavos': fields.boolean(u'Ignorar centavos?'),
    }

    _defaults = {
        'natureza': 'R',
        'data_reajuste': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def buscar_contratos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('finan.contrato.reajuste.contrato')
        contrato_pool = self.pool.get('finan.contrato')
        currency_pool = self.pool.get('res.currency')
        real_ids = currency_pool.search(cr, uid, [('name', '=', 'BRL')])
        real_id = real_ids[0]

        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser refeito!')

            #
            # Exclui os contratos incluídos anteriormente
            #
            for cont_obj in reajuste_obj.contrato_reajustar_ids:
                cont_obj.unlink()

            #
            # Faz uma lista dos contratos a serem excluídos do reajuste
            #
            excecao = []
            for cont_obj in reajuste_obj.contrato_excecoes_ids:
                excecao += [cont_obj.id]

            sql = '''
            select
                c.id
            from
                finan_contrato c
                join res_company cc on cc.id = c.company_id
            where
                c.ativo = True and
                (cc.id = {company_id}
                or cc.parent_id = {company_id}
                )
                and c.res_currency_id = {indice_id}
                and c.natureza = '{natureza}'
                and (
                    c.data_reajuste between '{data_inicial}' and '{data_final}'
                    or c.data_reajuste is null
                )
            '''

            filtro = {
                'company_id': reajuste_obj.company_id.id,
                'indice_id': reajuste_obj.currency_id.id,
                'natureza': reajuste_obj.natureza,
                'excecoes': str(excecao).replace('[', '').replace(']', ''),
                'data_inicial': reajuste_obj.data_inicial,
                'data_final': reajuste_obj.data_final,
            }

            if len(excecao) > 0:
                sql += '''
                and c.id not in ({excecoes})
                '''

            if reajuste_obj.partner_id:
                filtro['partner_id'] = reajuste_obj.partner_id.id
                sql += '''
                and c.partner_id = {partner_id}
                '''

            sql = sql.format(**filtro)
            print(sql)

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            for id, in dados:
                contrato_obj = contrato_pool.browse(cr, uid, id)
                dados_item = {
                    'reajuste_id': reajuste_obj.id,
                    'contrato_id': id,
                    'valor_antigo': contrato_obj.valor_mensal,
                    'valor_novo': currency_pool.compute(cr, uid, real_id, reajuste_obj.currency_id.id, contrato_obj.valor_mensal, round=False, context={'date': reajuste_obj.data_reajuste})
                }

                if reajuste_obj.ignorar_centavos:
                    dados_item['valor_novo'] = dados_item['valor_novo'].quantize(D('1'))

                item_pool.create(cr, uid, dados_item)


    def efetiva_reajuste(self, cr, uid, ids, context={}):
        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser refeito!')

            if not reajuste_obj.data_confirmacao:
                raise osv.except_osv(u'Erro!', u'Para efetivar o reajuste, é preciso preencher a data e hora de confirmação!')

            #
            # Vamos agora varrer todos os contratos a serem reajustados
            #
            for item_obj in reajuste_obj.contrato_reajustar_ids:
                ###
                ### Atualizar o valor das parcelas a vencer
                ###
                ##for lancamento_obj in item_obj.contrato_id.lancamento_ids:
                    ###
                    ### Ignorar lançamentos quitados, conciliados ou baixados
                    ###
                    ##if lancamento_obj.situacao in ['Quitado', 'Conciliado', 'Baixado']:
                        ##continue

                    ###
                    ### Ignorar lançamentos efetivos que possuam nota ou boleto
                    ###
                    ##if lancamento_obj.nosso_numero or lancamento_obj.sped_documento_id:
                        ##continue

                    ###
                    ### Ignorar lançamentos vencidos
                    ###
                    ##if lancamento_obj.situacao == 'Vencido':
                        ##continue

                    ###
                    ### Ignorar lançamentos com vencimento anterior ao reajuste
                    ###
                    ##if lancamento_obj.data_vencimento < reajuste_obj.data_reajuste:
                        ##continue

                    ###
                    ### Reajusta somente os provisionados
                    ###
                    ##if lancamento_obj.provisionado:
                        ##lancamento_obj.write({'valor_documento': item_obj.valor_novo, 'valor_original_contrato': item_obj.valor_novo})

                #
                # Atualizar o valor das parcelas a vencer
                #
                sql = """
                    update finan_lancamento l set
                        valor_documento = {valor_novo},
                        valor_original_contrato = {valor_novo}
                    where
                        l.contrato_id = {contrato_id}
                        and l.provisionado = True
                        and l.situacao in ('A vencer', 'Vence hoje')
                        and l.data_vencimento >= '{data_reajuste}'
                        and l.nosso_numero is null
                        and l.sped_documento_id is null;

                    update finan_contrato c set
                        valor_mensal = {valor_novo}
                    where
                        c.id = {contrato_id};
                """

                if not reajuste_obj.ignorar_centavos:
                    sql += """
                    update finan_contrato_produto p set
                        vr_unitario = vr_unitario * {indice}
                    where
                        p.contrato_id = {contrato_id}
                        and p.data is null;

                    update finan_contrato c set
                        valor_faturamento = (
                            select
                                sum(coalesce(p.quantidade, 0) * coalesce(p.vr_unitario, 0))
                            from
                                finan_contrato_produto p
                            where
                                p.contrato_id = {contrato_id}
                            ),
                        data_reajuste = '{data_reajuste}'
                    where
                        c.id = {contrato_id};

                    """

                filtro = {
                    'contrato_id': item_obj.contrato_id.id,
                    'data_reajuste': reajuste_obj.data_reajuste,
                    'valor_novo': item_obj.valor_novo,
                    'indice': D(item_obj.valor_novo) / D(item_obj.valor_antigo),
                }
                sql = sql.format(**filtro)
                cr.execute(sql)

                if reajuste_obj.ignorar_centavos:
                    #
                    # Agora, ajusta o valor dos itens a serem faturados
                    #
                    indice = D(item_obj.valor_novo) / D(item_obj.valor_antigo)
                    total = D(0)
                    for prod_obj in item_obj.contrato_id.contrato_produto_ids:
                        if prod_obj.data:
                            continue

                        valor = D(prod_obj.vr_unitario)
                        valor *= D(prod_obj.quantidade)
                        valor *= indice
                        valor = valor.quantize(D('0.01'))

                        vr_unitario = valor / D(prod_obj.quantidade)
                        vr_unitario = vr_unitario.quantize(D('0.01'))

                        prod_obj.write({'vr_unitario': valor})

                        valor = vr_unitario
                        valor *= D(prod_obj.quantidade)
                        total += valor

                    if total != item_obj.valor_novo:
                        valor_rateio = D(item_obj.valor_novo) - total
                        vr_unitario += valor_rateio / D(prod_obj.quantidade)
                        prod_obj.write({'vr_unitario': vr_unitario})

            #
            # Agora, trava o reajuste, para não ser mais alterado
            #
            reajuste_obj.write({'confirmado': True})

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Não deixa alterar reajustes confirmados
        #
        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser alterado!')

        return super(finan_contrato_reajuste, self).write(cr, uid, ids, dados, context=context)

    def unlink(self, cr, uid, ids, context={}):
        #
        # Não deixa excluir reajustes confirmados
        #
        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser excluído!')

        return super(finan_contrato_reajuste, self).unlink(cr, uid, ids, context=context)


finan_contrato_reajuste()


class finan_contrato_reajuste_contrato(osv.Model):
    _description = u'Itens do reajuste'
    _name = 'finan.contrato.reajuste.contrato'
    _order = 'reajuste_id, contrato_id'

    _columns = {
        'reajuste_id': fields.many2one('finan.contrato.reajuste', u'Reajuste', required=True, ondelete="cascade"),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="restrict"),

        'company_id': fields.related('contrato_id', 'company_id', relation='res.company', string=u'Empresa', type='many2one'),
        'numero': fields.related('contrato_id', 'numero', type='char', string=u'Número'),
        'partner_id': fields.related('contrato_id', 'partner_id', relation='res.partner', string=u'Parceiro', type='many2one'),

        'valor_antigo': fields.float(u'Valor antigo'),
        'valor_novo': fields.float(u'Valor novo'),
    }


finan_contrato_reajuste_contrato()
