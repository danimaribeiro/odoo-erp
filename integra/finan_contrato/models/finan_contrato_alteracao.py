# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from osv import osv, fields
from finan_contrato import DIAS_VENCIMENTO
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, ultimo_dia_mes, hoje
from dateutil.relativedelta import relativedelta


class finan_contrato_alteracao(osv.Model):
    _description = u'Contrato - alteração'
    _name = 'finan.contrato.alteracao'
    _rec_name = 'id'

    def _set_produtos(self, cr, uid, ids, nome_campo, valor_campo, arg=None, context=None):
        self.pool.get('finan.contrato.alteracao').write(cr, uid, ids, {'contrato_produto_alteracao_ids': valor_campo})

    def _get_produtos(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for alteracao_obj in self.browse(cr, uid, ids):
            if nome_campo == 'contrato_produto_anterior_ids':
                busca = [
                    ('alteracao_id', '=', alteracao_obj.id),
                    ('novo', '=', 'N'),
                ]
            else:
                busca = [
                    ('alteracao_id', '=', alteracao_obj.id),
                    ('novo', '=', 'S'),
                ]

            produto_ids = self.pool.get('finan.contrato.alteracao.produto').search(cr, uid, busca)
            res[alteracao_obj.id] = produto_ids

        return res

    def _get_bonificacao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for alteracao_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if alteracao_obj.tipo == 'B':
                if nome_campo == 'quantidade_bonificada':
                    valor = len(alteracao_obj.lancamento_bonificado_ids)

                else:
                    for lancamento_obj in alteracao_obj.lancamento_bonificado_ids:
                        valor += D(lancamento_obj.valor_original_contrato or 0)

            res[alteracao_obj.id] = valor

        return res

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'company_id': fields.related('contrato_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa'),
        'partner_id': fields.related('contrato_id', 'partner_id', type='many2one', relation='res.partner', string=u'Cliente'),
        'tipo': fields.selection([('D', u'Data de Vencimento'), ('V', u'Valor'), ('B', u'Bonificações'), ('R', u'Rescisões')], string='Tipo', select=True),
        'eh_reducao_valor': fields.boolean(u'É redução de valor?'),
        'eh_mudanca_endereco': fields.boolean(u'É mudança de endereço?'),
        'data_solicitacao': fields.datetime(u'Data da solicitação'),
        'solicitante_id': fields.many2one('res.users', u'Solicitante'),
        'obs': fields.text(u'Justificativa/obs'),
        'aprovado': fields.boolean(u'Aprovado'),
        'data_aprovacao': fields.datetime(u'Data de aprovação'),
        'aprovador_id': fields.many2one('res.users', u'Aprovador'),
        'aprovado_area': fields.boolean(u'Aprovado - área'),
        'data_aprovacao_area': fields.datetime(u'Data de aprovação'),
        'aprovador_area_id': fields.many2one('res.users', u'Aprovador'),

        'conferido_area': fields.boolean(u'Conferido - suprimentos'),
        'data_conferencia_area': fields.datetime(u'Data de conferência'),
        'conferidor_area_id': fields.many2one('res.users', u'Conferidor'),

        #
        # Alteração de dia vencimento
        #
        'dia_vencimento_anterior': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento anterior'),
        'dia_vencimento_novo': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento novo'),

        #
        # Alteração de valor/itens faturados
        #
        'contrato_produto_alteracao_ids': fields.one2many('finan.contrato.alteracao.produto', 'alteracao_id', u'Produtos e serviços alteração', ondelete="cascade"),
        'contrato_produto_anterior_ids': fields.function(_get_produtos, type='one2many', relation='finan.contrato.alteracao.produto', method=True, string=u'Produtos e serviços anteriores', fnct_inv=_set_produtos),
        'valor_mensal_anterior': fields.float(u'Valor mensal anterior'),
        'contrato_produto_novo_ids': fields.function(_get_produtos, type='one2many', relation='finan.contrato.alteracao.produto', method=True, string=u'Produtos e serviços novos', fnct_inv=_set_produtos),
        'valor_mensal_novo': fields.float(u'Valor mensal novo'),
        'sale_order_id': fields.many2one('sale.order', u'Pedido'),
        'data_alteracao': fields.date(u'Data da alteração'),
        'valor_pro_rata': fields.float(u'Valor pro-rata'),
        'data_proximo_vencimento_nao_faturado': fields.date(u'Próximo vencimento não faturado'),
        'pro_rata_novo_valor': fields.boolean(u'Pro-rata sobre o novo valor?'),
        'retirada_equipamento_cliente': fields.boolean(u'Precisa retirar equipamento do cliente?'),

        #
        # Bonificação de parcelas
        #
        'lancamento_bonificado_ids': fields.many2many('finan.lancamento', 'finan_contrato_alteracao_bonificacao', 'alteracao_id', 'lancamento_id', string=u'Parcelas a bonificar'),
        'motivo_baixa_id': fields.many2one('finan.motivobaixa', u'Motivo para a bonificação'),
        'quantidade_bonificada': fields.function(_get_bonificacao, type='integer', string=u'Qtd. bonificada'),
        'valor_bonificado': fields.function(_get_bonificacao, type='float', string=u'Valor bonificado'),

        #
        # Rescisões
        #
        'motivo_distrato_id': fields.many2one('finan.motivo_distrato', u'Motivo do distrato', ondelete='restrict'),
        'data_comunicacao': fields.date(u'Data de comunicação'),
        'data_distrato': fields.date(u'Data de distrato'),
        'data_prevista_retirada': fields.date(u'Data prevista da retirada'),
        'bonifica_mes_comunicacao': fields.boolean(u'Bonificar parcela do mês de comunicação?'),
        'bonifica_prorata_distrato': fields.boolean(u'Bonificar saldo do distrato?'),
        'efetivar_retirada': fields.boolean(u'Ao TÉCNICO e SUPRIMENTOS: Trata- se alterações de proprietário então não há efetiva retirada de equipamento'),
    }

    _defaults = {
        'solicitante_id': lambda self, cr, uid, context: uid,
        'aprovado': False,
        'data_solicitacao': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def onchange_contrato_id(self, cr, uid, ids, contrato_id, tipo):
        if (not contrato_id) or (not tipo):
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, contrato_id)

        valores['company_id'] = contrato_obj.company_id.id
        valores['partner_id'] = contrato_obj.partner_id.id

        if tipo == 'D':
            valores['dia_vencimento_anterior'] = contrato_obj.dia_vencimento

        elif tipo in ('V', 'R'):
            valores['valor_mensal_anterior'] = contrato_obj.valor_mensal
            produtos = []

            for produto_obj in contrato_obj.contrato_produto_ids:
                if produto_obj.data:
                    continue

                dados_produto = {
                    'novo': 'N',
                    'contrato_id': contrato_obj.id,
                    'product_id': produto_obj.product_id.id,
                    'quantidade': produto_obj.quantidade,
                    'vr_unitario': produto_obj.vr_unitario,
                    'vr_total': produto_obj.vr_total,
                }

                produtos.append([0, False, dados_produto])

            lancamento_pool = self.pool.get('finan.lancamento')
            proximo_vencimento_ids = lancamento_pool.search(cr, uid, [('contrato_id', '=', contrato_obj.id), ('provisionado', '=', True)], order='data_vencimento', limit=1)

            if len(proximo_vencimento_ids):
                proximo_vencimento_obj = lancamento_pool.browse(cr, uid, proximo_vencimento_ids[0])
                valores['data_proximo_vencimento_nao_faturado'] = proximo_vencimento_obj.data_vencimento

            valores['contrato_produto_anterior_ids'] = produtos

        return res


    def onchange_sale_order_id(self, cr, uid, ids, sale_order_id, valor_mensal_anterior, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not sale_order_id:
            return res

        valor_mensal_anterior = D(valor_mensal_anterior or 0)

        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        sale_order_obj.vr_mensal = D(sale_order_obj.vr_mensal or 0)

        if getattr(sale_order_obj, 'renegociacao', False):
            if sale_order_obj.vr_mensal > valor_mensal_anterior:
                valor_mensal_novo = sale_order_obj.vr_mensal - valor_mensal_anterior

            else:
                valor_mensal_novo = sale_order_obj.vr_mensal

        else:
            valor_mensal_novo = valor_mensal_anterior + sale_order_obj.vr_mensal

        valores['valor_mensal_novo'] = valor_mensal_novo

        return res

    def create(self, cr, uid, dados, context={}):
        dados['solicitante_id'] = uid
        dados['data_solicitacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, dados['contrato_id'])

        if dados['tipo'] == 'D':
            dados['dia_vencimento_anterior'] = contrato_obj.dia_vencimento

        elif dados['tipo'] == 'V':
            data_alteracao = parse_datetime(dados['data_alteracao']).date()

            if 'valida_data_alteracao' in context:
                if data_alteracao < hoje():
                    dias_da_alteracao = hoje() - data_alteracao
                    if dias_da_alteracao.days > 5:
                        raise osv.except_osv(u'Inválido!', u'Proibido informar a data do início do novo valor com menos de 5 dias de antecedência!')

            dados['valor_mensal_anterior'] = contrato_obj.valor_mensal
            produtos = []

            for produto_obj in contrato_obj.contrato_produto_ids:
                if produto_obj.data:
                    continue

                dados_produto = {
                    'novo': 'N',
                    'contrato_id': contrato_obj.id,
                    'product_id': produto_obj.product_id.id,
                    'quantidade': produto_obj.quantidade,
                    'vr_unitario': produto_obj.vr_unitario,
                    'vr_total': produto_obj.vr_total,
                }

                produtos.append([0, False, dados_produto])

            dados['contrato_produto_anterior_ids'] = produtos

            lancamento_pool = self.pool.get('finan.lancamento')
            proximo_vencimento_ids = lancamento_pool.search(cr, uid, [('contrato_id', '=', contrato_obj.id), ('provisionado', '=', True)], order='data_vencimento', limit=1)

            if len(proximo_vencimento_ids):
                proximo_vencimento_obj = lancamento_pool.browse(cr, uid, proximo_vencimento_ids[0])
                dados['data_proximo_vencimento_nao_faturado'] = proximo_vencimento_obj.data_vencimento

        return super(finan_contrato_alteracao, self).create(cr, uid, dados, context=context)

    def aprovar(self, cr, uid, ids, context={}):
        contrato_pool = self.pool.get('finan.contrato')
        lancamento_pool = self.pool.get('finan.lancamento')

        for alteracao_obj in self.browse(cr, uid, ids):
            dados_alteracao = {
                'aprovador_id': uid,
                'data_aprovacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'aprovado': True,
            }

            #
            # Alteração de data de vencimento
            #
            if alteracao_obj.tipo == 'D':
                dados_contrato = {
                    'dia_vencimento': alteracao_obj.dia_vencimento_novo,
                }

                contrato_pool.write(cr, uid, [alteracao_obj.contrato_id.id], dados_contrato)
                contrato_pool.gera_todas_parcelas(cr, uid, [alteracao_obj.contrato_id.id], context={'gera_lancamento': True})

                alteracao_obj.write(dados_alteracao)

            elif alteracao_obj.tipo == 'V':
                #
                # Verificando se os valores estão corretos
                #
                produto_ids = []

                valor_produtos = D(0)
                for produto_obj in alteracao_obj.contrato_produto_novo_ids:
                    dados_produto = {
                        'product_id': produto_obj.product_id.id,
                        'quantidade': produto_obj.quantidade,
                        'vr_unitario': produto_obj.vr_unitario,
                        'vr_total': produto_obj.vr_total,
                    }
                    produto_ids.append([0, False, dados_produto])
                    valor_produtos += D(produto_obj.vr_total or 0)

                if not alteracao_obj.valor_mensal_novo:
                    raise osv.except_osv(u'Inválido!', u'Proibido aprovar sem a informação do valor novo!')

                elif (D(alteracao_obj.valor_mensal_novo or 0) != valor_produtos) and (alteracao_obj.valor_mensal_novo > alteracao_obj.valor_mensal_anterior):
                    raise osv.except_osv(u'Inválido!', u'Proibido aprovar se a soma dos novos produtos/serviços for diferente do valor novo!')

                for produto_obj in alteracao_obj.contrato_id.contrato_produto_ids:
                    if produto_obj.data:
                        continue
                    produto_obj.unlink()

                dados_contrato = {
                    'valor_mensal': alteracao_obj.valor_mensal_novo,
                }

                produto_ids = []

                for produto_obj in alteracao_obj.contrato_produto_novo_ids:
                    dados_produto = {
                        'product_id': produto_obj.product_id.id,
                        'quantidade': produto_obj.quantidade,
                        'vr_unitario': produto_obj.vr_unitario,
                        'vr_total': produto_obj.vr_total,
                    }
                    produto_ids.append([0, False, dados_produto])

                dados_contrato['contrato_produto_ids'] = produto_ids

                contrato_pool.write(cr, uid, [alteracao_obj.contrato_id.id], dados_contrato)
                contrato_pool.gera_todas_parcelas(cr, uid, [alteracao_obj.contrato_id.id], context={'gera_lancamento': True})

                #
                # Adicionamos também o item do pro-rata no próximo vencimento não efetivado
                #
                if alteracao_obj.valor_pro_rata:
                    dados_produto['data'] = alteracao_obj.data_proximo_vencimento_nao_faturado
                    dados_produto['vr_unitario'] = alteracao_obj.valor_pro_rata
                    dados_produto['vr_total'] = alteracao_obj.valor_pro_rata
                    produto_ids = ([0, False, dados_produto],)
                    dados_contrato = {
                        'contrato_produto_ids': produto_ids,
                    }
                    contrato_pool.write(cr, uid, [alteracao_obj.contrato_id.id], dados_contrato)
                    dados_produto['novo'] = 'S'
                    dados_produto['contrato_id'] = alteracao_obj.contrato_id.id
                    dados_alteracao['contrato_produto_alteracao_ids'] = produto_ids

                alteracao_obj.write(dados_alteracao)

            elif alteracao_obj.tipo == 'B':
                for lancamento_obj in alteracao_obj.lancamento_bonificado_ids:
                    data_baixa = parse_datetime(lancamento_obj.data_vencimento)
                    data_baixa += relativedelta(day=1)
                    data_baixa += relativedelta(months=-1)
                    data_baixa = ultimo_dia_mes(data_baixa)
                    lancamento_obj.write({'data_baixa': str(data_baixa), 'motivo_baixa_id': alteracao_obj.motivo_baixa_id.id, 'provisionado': False})

                alteracao_obj.write(dados_alteracao)

            elif alteracao_obj.tipo == 'R':
                if (alteracao_obj.bonifica_mes_comunicacao or alteracao_obj.bonifica_prorata_distrato) and (not alteracao_obj.motivo_baixa_id):
                    raise osv.except_osv(u'Inválido!', u'Em caso de bonificação, é necessário informar o motivo!')

                #
                # Realizamos o distrato, e regeramos as parcelas para pegar a
                # parcela do distrato
                #
                contrato_pool.gera_todas_parcelas(cr, uid, [alteracao_obj.contrato_id.id], context={'gera_lancamento': True})
                contrato_pool.write(cr, uid, [alteracao_obj.contrato_id.id], {'data_distrato': alteracao_obj.data_distrato, 'motivo_distrato_id': alteracao_obj.motivo_distrato_id.id, 'ativo': False})
                contrato_pool.gera_todas_parcelas(cr, uid, [alteracao_obj.contrato_id.id], context={'gera_lancamento': True})

                #
                # Verificamos agora a bonificação das 2 últimas parcelas
                #
                ultimas_parcelas_ids = lancamento_pool.search(cr, uid, [
                    ('contrato_id', '=', alteracao_obj.contrato_id.id),
                    ('provisionado', '=', True),
                    ], order='data_vencimento_original desc', limit=2)

                print(ultimas_parcelas_ids)

                if alteracao_obj.bonifica_prorata_distrato and len(ultimas_parcelas_ids) >= 1:
                    parcela_distrato_id = ultimas_parcelas_ids[0]
                    parcela_distrato_obj = lancamento_pool.browse(cr, uid, parcela_distrato_id)
                    data_baixa = parse_datetime(parcela_distrato_obj.data_vencimento)
                    data_baixa += relativedelta(day=1)
                    data_baixa += relativedelta(months=-1)
                    data_baixa = ultimo_dia_mes(data_baixa)
                    parcela_distrato_obj.write({'data_baixa': str(data_baixa), 'motivo_baixa_id': alteracao_obj.motivo_baixa_id.id, 'provisionado': False})

                if alteracao_obj.bonifica_mes_comunicacao and len(ultimas_parcelas_ids) >= 2:
                    parcela_comunicacao_id = ultimas_parcelas_ids[1]
                    parcela_comunicacao_obj = lancamento_pool.browse(cr, uid, parcela_comunicacao_id)
                    data_baixa = parse_datetime(parcela_comunicacao_obj.data_vencimento)
                    data_baixa += relativedelta(day=1)
                    data_baixa += relativedelta(months=-1)
                    data_baixa = ultimo_dia_mes(data_baixa)
                    parcela_comunicacao_obj.write({'data_baixa': str(data_baixa), 'motivo_baixa_id': alteracao_obj.motivo_baixa_id.id, 'provisionado': False})

                alteracao_obj.write(dados_alteracao)

        return True

    def aprovar_area(self, cr, uid, ids, context={}):
        for alteracao_obj in self.browse(cr, uid, ids):
            #
            # Verificando se os valores estão corretos
            #
            if alteracao_obj.tipo == 'V':
                valor_produtos = D(0)
                for produto_obj in alteracao_obj.contrato_produto_novo_ids:
                    valor_produtos += D(produto_obj.vr_total or 0)

                if not alteracao_obj.valor_mensal_novo:
                    raise osv.except_osv(u'Inválido!', u'Proibido aprovar sem a informação do valor novo!')

                elif D(alteracao_obj.valor_mensal_novo or 0) != valor_produtos:
                    raise osv.except_osv(u'Inválido!', u'Proibido aprovar se a soma dos novos produtos/serviços for diferente do valor novo!')

            dados_alteracao = {
                'aprovador_area_id': uid,
                'data_aprovacao_area': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'aprovado_area': True,
            }
            alteracao_obj.write(dados_alteracao)

        return True

    def conferir_area(self, cr, uid, ids, context={}):
        for alteracao_obj in self.browse(cr, uid, ids):
            dados_alteracao = {
                'conferidor_area_id': uid,
                'data_conferencia_area': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'conferido_area': True,
            }
            alteracao_obj.write(dados_alteracao)

        return True

    def unlink(self, cr, uid, ids, context={}):
        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.aprovado:
                raise osv.except_osv(u'Inválido !', u'Proibido excluir após a aprovação!')

            if alteracao_obj.tipo == 'B' and alteracao_obj.aprovado_area:
                raise osv.except_osv(u'Inválido !', u'Proibido excluir após a aprovação!')

            if alteracao_obj.tipo in ('R', 'V') and alteracao_obj.retirada_equipamento_cliente and alteracao_obj.aprovado_area:
                raise osv.except_osv(u'Inválido !', u'Proibido excluir após a aprovação!')

        return super(finan_contrato_alteracao, self).unlink(cr, uid, ids, context=context)

    def onchange_valor_mensal_novo(self, cr, uid, ids, valor_mensal_novo, valor_mensal_anterior, data_alteracao, pro_rata_novo_valor):
        res = {}
        valores = {}
        res['value'] = valores

        if not (valor_mensal_novo and valor_mensal_anterior and data_alteracao):
            return res

        valor_mensal_novo = D(valor_mensal_novo)
        valor_mensal_anterior = D(valor_mensal_anterior)
        dia_alteracao = parse_datetime(data_alteracao).date().day
        ultimo_dia = ultimo_dia_mes(data_alteracao).day

        #
        # Comentado para atender o chamado 2619
        #
        #if pro_rata_novo_valor:
            #if valor_mensal_anterior > valor_mensal_novo:
                #mudanca = valor_mensal_anterior - valor_mensal_novo
            #else:
                #mudanca = valor_mensal_novo - valor_mensal_anterior

            #dias_pro_rata = dia_alteracao - 1

        #else:
            #if valor_mensal_novo > valor_mensal_anterior:
                #mudanca = D(valor_mensal_novo) - D(valor_mensal_anterior)
            #else:
                #mudanca = D(valor_mensal_anterior) - D(valor_mensal_novo)

            #dias_pro_rata = ultimo_dia - dia_alteracao + 1

        if pro_rata_novo_valor:
            mudanca = D(valor_mensal_anterior or 0) - D(valor_mensal_novo or 0)
            dias_pro_rata = dia_alteracao - 1

        else:
            mudanca = D(valor_mensal_novo) - D(valor_mensal_anterior)
            dias_pro_rata = ultimo_dia - dia_alteracao + 1

        valor_dia = mudanca / D(ultimo_dia)
        valores['valor_pro_rata'] = valor_dia * dias_pro_rata

        return res

    def onchange_data_alteracao(self, cr, uid, ids, data_alteracao, data_proximo_vencimento_nao_faturado, valida_data_alteracao=False):
        res = {}
        valores = {}
        res['value'] = valores

        if not (data_alteracao and data_proximo_vencimento_nao_faturado):
            return res

        data_alteracao = parse_datetime(data_alteracao).date()

        #
        # Validar data somente para redução de mensalidade
        #
        if valida_data_alteracao:
            if data_alteracao < hoje():
                dias_da_alteracao = hoje() - data_alteracao
                if dias_da_alteracao.days > 5:
                    raise osv.except_osv(u'Inválido!', u'Proibido informar a data do início do novo valor com menos de 5 dias de antecedência!')

        data_alteracao += relativedelta(day=1)
        data_alteracao += relativedelta(months=+1)
        data_proximo_vencimento_nao_faturado = parse_datetime(data_proximo_vencimento_nao_faturado).date()

        valores['pro_rata_novo_valor'] = (data_alteracao.year == data_proximo_vencimento_nao_faturado.year) and (data_alteracao.month == data_proximo_vencimento_nao_faturado.month)

        return res

    def onchange_data_comunicacao(self, cr, uid, ids, data_comunicacao):
        valores = {}
        res = {}
        res['value'] = valores

        if not data_comunicacao:
            return res

        data_distrato = parse_datetime(data_comunicacao) + relativedelta(days=+30)

        valores['data_distrato'] = str(data_distrato)[:10]

        return res


finan_contrato_alteracao()


class finan_contrato_alteracao_produto(osv.Model):
    _description = u'Itens do contrato - alteracao'
    _name = 'finan.contrato.alteracao.produto'
    _inherit = 'finan.contrato_produto'

    _columns = {
        'alteracao_id': fields.many2one('finan.contrato.alteracao', u'Alteração', select=True, ondelete='cascade'),
        'novo': fields.char(u'Novo', size=1),
    }

    _defaults = {
        'novo': 'N',
    }


finan_contrato_alteracao_produto()
