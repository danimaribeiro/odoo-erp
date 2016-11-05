# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
from decimal import Decimal as D, ROUND_UP
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje, formata_data, agora
from pybrasil.valor import formata_valor
from copy import copy
from pybrasil.base import DicionarioBrasil
import os
from finan.wizard.finan_relatorio import Report, JASPER_BASE_DIR
import base64
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)


STORE_TOTAIS = {
    'sale.order': (
        lambda order_pool, cr, uid, ids, context={}: ids,
        ['vr_desconto_rateio', 'vr_desconto_rateio_servicos', 'vr_desconto_rateio_mensalidades', 'payment_term_id', 'order_line', 'percentual_acessorios', 'meses_retorno_locacao', 'vr_mensal_locacao', 'vr_mensal_atual', 'finan_contrato_id'],
        20
    ),

    'sale.order.line': (
        lambda item_pool, cr, uid, ids, context={}: [item_obj.order_id.id for item_obj in item_pool.browse(cr, uid, ids)],
        ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos', 'vr_total_venda_impostos', 'margem', 'desconto', 'porcentagem_imposto', 'proporcao_imposto', 'vr_taxa_juros', 'vr_produtos', 'vr_frete', 'vr_seguro', 'vr_outras', 'vr_desconto', 'vr_ipi', 'vr_icms_st', 'vr_ii', 'credita_icms_proprio', 'cfop_id', 'credita_icms_st',
         'credita_ipi', 'credita_pis_cofins', 'quantidade', 'fator_quantidade', 'vr_custo', 'vr_custo_estoque',
         'vr_diferencial_aliquota', 'vr_diferencial_aliquota_st', 'vr_simples',
         'credita_icms_proprio', 'credita_icms_st', 'credita_ipi', 'credita_pis_cofins'],
        10
    ),
}


CAMPOS_PRODUTOS = ('vr_total_produtos', 'vr_total_produtos_sem_desconto','vr_simples_produtos', 'vr_icms_proprio_produtos', 'vr_diferencial_aliquota_produtos', 'vr_ipi_produtos', 'vr_iss_produtos', 'vr_pis_proprio_produtos', 'vr_cofins_proprio_produtos', 'vr_csll_produtos', 'vr_irrf_produtos', 'total_imposto_produtos', 'vr_produto_base_produtos', 'vr_comissao_produtos', 'vr_margem_contribuicao_produtos',  'al_margem_contribuicao_produtos')
CAMPOS_SERVICOS = ('vr_total_servicos', 'vr_total_servicos_sem_desconto','vr_simples_servicos', 'vr_icms_proprio_servicos', 'vr_diferencial_aliquota_servicos', 'vr_ipi_servicos', 'vr_iss_servicos', 'vr_pis_proprio_servicos', 'vr_cofins_proprio_servicos', 'vr_csll_servicos', 'vr_irrf_servicos', 'total_imposto_servicos', 'vr_produto_base_servicos', 'vr_comissao_servicos', 'vr_margem_contribuicao_servicos', 'al_margem_contribuicao_servicos')
CAMPOS_MENSALIDADES = ('vr_total_mensalidades', 'vr_mensal_total', 'vr_total_mensalidades_sem_desconto','vr_simples_mensalidades', 'vr_icms_proprio_mensalidades', 'vr_diferencial_aliquota_mensalidades', 'vr_ipi_mensalidades', 'vr_iss_mensalidades', 'vr_pis_proprio_mensalidades', 'vr_cofins_proprio_mensalidades', 'vr_csll_mensalidades', 'vr_irrf_mensalidades', 'total_imposto_mensalidades', 'vr_produto_base_mensalidades', 'vr_comissao_mensalidades', 'vr_margem_contribuicao_mensalidades', 'al_margem_contribuicao_mensalidades')


class sale_simulacao_parcelas(osv.osv_memory):
    _name = 'sale.simulacao.parcelas'
    _description = u'Simulação das parcelas na venda'

    _columns = {
        'sale_id': fields.many2one('sale.order', u'Pedido', ondelete='cascade'),
        'numero': fields.char(u'Nº', size=3),
        'data': fields.date(u'Vencimento'),
        'valor': fields.float(u'Valor', digits=(18, 2)),
    }


sale_simulacao_parcelas()


class sale_margem_contribuicao(osv.Model):
    _name = 'sale.margem.contribuicao'
    _description = u'Margem de contribuição nas vendas'

    _columns = {
        'sale_id': fields.many2one('sale.order', u'Pedido', ondelete='cascade'),
        'tipo': fields.selection((('P', u'Produtos'), ('S', u'Serviços'), ('M', u'Mensalidades')), u'Tipo'),
        'campo': fields.char(u'Valor', size=30),
        'valor': fields.float(u'Valor', digits=(18, 2)),
    }


sale_margem_contribuicao()


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def _tempo_etapa(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = 0

            if sale_obj.data_ultima_etapa and sale_obj.data_proxima_etapa:
                data_inicial = parse_datetime(sale_obj.data_ultima_etapa)
                data_final = parse_datetime(sale_obj.data_proxima_etapa)
            elif sale_obj.data_proxima_etapa:
                data_inicial = parse_datetime(sale_obj.create_date)
                data_final = parse_datetime(sale_obj.data_proxima_etapa)
            else:
                data_inicial = parse_datetime(sale_obj.create_date)
                data_final = parse_datetime(fields.datetime.now())

            intervalo = data_final - data_inicial

            res[sale_obj.id] = intervalo.days

            print(data_final, data_inicial)

        return res

    def _valores_separados(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            valor = D(0)

            if nome_campo in CAMPOS_PRODUTOS:
                for item_obj in sale_obj.item_produto_ids:
                    if nome_campo == 'vr_total_produtos' or nome_campo == 'vr_total_produtos_sem_desconto':
                        valor += D(item_obj.vr_total_venda_impostos or 0)
                    else:
                        valor += D(getattr(item_obj, nome_campo[:-9], 0) or 0)

                if nome_campo == 'vr_total_produtos_sem_desconto':
                    valor += D(sale_obj.vr_desconto_rateio or 0)

                if nome_campo == 'al_margem_contribuicao_produtos':
                    valor = D(0)
                    vr_produtos = D(sale_obj.vr_total_produtos or 0)
                    if vr_produtos > 0:
                        valor = D(sale_obj.vr_margem_contribuicao_produtos or 0) / vr_produtos
                        valor *= 100

            elif nome_campo in CAMPOS_SERVICOS:
                for item_obj in sale_obj.item_servico_ids:
                    if nome_campo == 'vr_total_servicos' or nome_campo == 'vr_total_servicos_sem_desconto':
                        valor += D(item_obj.vr_total_venda_impostos or 0)
                    else:
                        valor += D(getattr(item_obj, nome_campo[:-9], 0) or 0)

                if nome_campo == 'vr_total_servicos_sem_desconto':
                    valor += D(sale_obj.vr_desconto_rateio_servicos or 0)

                if nome_campo == 'al_margem_contribuicao_servicos':
                    valor = D(0)
                    vr_servicos = D(sale_obj.vr_total_servicos or 0)
                    if vr_servicos > 0:
                        valor = D(sale_obj.vr_margem_contribuicao_servicos or 0) / vr_servicos
                        valor *= 100

            elif nome_campo in CAMPOS_MENSALIDADES:
                for item_obj in sale_obj.item_mensalidade_ids:
                    if nome_campo in ('vr_total_mensalidades', 'vr_mensal_total', 'vr_total_mensalidades_sem_desconto'):
                        valor += D(item_obj.vr_total_venda_impostos or 0)
                    else:
                        valor += D(getattr(item_obj, nome_campo[:-13], 0) or 0)

                if nome_campo == 'vr_mensal_total':
                    valor += D(sale_obj.vr_mensal_locacao or 0)
                    valor += D(sale_obj.vr_mensal_atual or 0)

                if nome_campo == 'vr_total_mensalidades_sem_desconto':
                    valor += D(sale_obj.vr_desconto_rateio_mensalidades or 0)

                if nome_campo == 'al_margem_contribuicao_mensalidades':
                    valor = D(0)
                    vr_mensalidades = D(sale_obj.vr_total_mensalidades or 0)
                    if vr_mensalidades > 0:
                        valor = D(sale_obj.vr_margem_contribuicao_mensalidades or 0) / vr_mensalidades
                        valor *= 100

            res[sale_obj.id] = valor

        return res

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        currency_pool = self.pool.get('res.currency')

        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = {
                'amount_untaxed': D(0),
                'amount_tax': D(0),
                'amount_total': D(0),
            }
            valor_sem_impostos = D(0)
            valor_com_impostos = D(0)
            total_impostos = D(0)

            currency_obj = sale_obj.pricelist_id.currency_id

            for item_obj in sale_obj.order_line:
                if getattr(item_obj, 'tipo_item', 'P') not in ('P', 'S'):
                    continue

                valor_sem_impostos += D(item_obj.price_subtotal or 0)
                valor_com_impostos += D(item_obj.vr_total_venda_impostos or 0)
                valor_com_impostos += D(item_obj.vr_icms_st or 0)
                percentual_impostos = D(item_obj.total_imposto or 0) / D(item_obj.price_subtotal or 1)
                total_impostos += D(item_obj.vr_total_venda_impostos or 0) *  percentual_impostos

            #if sale_obj.vr_desconto_rateio:
                #valor_com_impostos -= D(sale_obj.vr_desconto_rateio)

            #res[sale_obj.id]['amount_tax'] = currency_pool.round(cr, uid, currency_obj, total_impostos)
            #res[sale_obj.id]['amount_untaxed'] = currency_pool.round(cr, uid, currency_obj, valor_sem_impostos)
            #res[sale_obj.id]['amount_total'] = currency_pool.round(cr, uid, currency_obj, valor_com_impostos)
            res[sale_obj.id]['amount_tax'] = total_impostos
            res[sale_obj.id]['amount_untaxed'] = valor_sem_impostos
            res[sale_obj.id]['amount_total'] = valor_com_impostos

        return res

    def _simulacao_parcelas(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            parcelas = False

            if sale_obj.payment_term and sale_obj.amount_total:
                dados = sale_obj.onchange_payment_term(sale_obj.payment_term.id, sale_obj.amount_total, sale_obj.vr_total_servicos, sale_obj.meses_retorno_locacao_original, sale_obj.vr_entrada)

                parcelas = dados['value']['simulacao_parcelas_ids']

            res[sale_obj.id] = parcelas

        return res

    def _field_readonly(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        nome_campo = nome_campo.replace('_readonly', '')

        for obj in self.browse(cr, uid, ids, context=context):
            if nome_campo[-3:] == '_id':
                campo = getattr(obj, nome_campo, False)

                if campo:
                    res[obj.id] = campo.id
                else:
                    res[obj.id] = False

            else:
                res[obj.id] = getattr(obj, nome_campo, False)

        return res

    def _finan_vencidos(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        lancamento_pool = self.pool.get('finan.lancamento')

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = False

            if not obj.partner_id:
                continue

            sql = """
            select
                l.id
            from
                finan_lancamento l
            where
                l.tipo = 'R'
                and (
                    l.situacao = 'Vencido'
                    or l.situacao = 'Vence hoje'
                )
                and coalesce(l.provisionado, False) = False
                and l.partner_id = {partner_id};
            """
            sql = sql.format(partner_id=obj.partner_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            lancamento_ids = []
            for lancamento_id, in dados:
                lancamento_ids.append(lancamento_id)

            if nome_campo == 'pendencia_financeira':
                res[obj.id] = len(lancamento_ids) > 0
            else:
                res[obj.id] = lancamento_ids

        return res

    def _etapa_prospecto_id(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = False

            if sale_obj.etapa_id.tipo == 'P' or sale_obj.etapa_id.id == 2:
                res[sale_obj.id] = sale_obj.etapa_id.id

        return res

    def _etapa_orcamento_id(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = False

            if sale_obj.etapa_id.tipo == 'V' or sale_obj.etapa_id.id == 3:
                res[sale_obj.id] = sale_obj.etapa_id.id

        return res

    def _etapa_ordem_servico_id(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = False

            if sale_obj.etapa_id.tipo == 'O':
                res[sale_obj.id] = sale_obj.etapa_id.id

        return res

    def _margem_contribuicao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        TIPOS_MARGEM = {
            'P': 'produtos',
            'S': 'servicos',
            'M': 'mensalidades',
        }

        CAMPOS_MARGEM = {
            'vr_margem_contribuicao_': u'Margem de contribuição',
            'vr_simples_': u'SIMPLES',
            'vr_iss_': u'ISS',
            'vr_pis_proprio_': u'PIS',
            'vr_cofins_proprio_': u'COFINS',
            'vr_csll_': u'CSLL',
            'vr_irrf_': u'IRPJ',
            'vr_produto_base_': u'Custo',
            'vr_comissao_': u'Comissão',
        }

        for sale_obj in self.browse(cr, uid, ids, context=context):
            margens = [[5, False, False]]

            for tipo in TIPOS_MARGEM:
                nome_tipo = TIPOS_MARGEM[tipo]

                if sale_obj.vr_margem_contribuicao_produtos:
                    for campo in CAMPOS_MARGEM:
                        if not getattr(sale_obj, campo + nome_tipo, False):
                            continue

                        dados = {
                            #'sale_id': sale_obj.id,
                            'tipo': tipo,
                            'campo': CAMPOS_MARGEM[campo],
                            'valor': D(getattr(sale_obj, campo + nome_tipo, False) or 0)
                        }

                        margens.append([1, False, dados])

            res[sale_obj.id] = margens

        return res

    def _group_etapa_prospecto_id(self, cr, uid, grupos_atuais_ids, domain, read_group_order=None, access_rights_uid=None, context={}):
        etapa_pool = self.pool.get('sale.etapa')
        etapa_ids = etapa_pool.search(cr, uid, ['|', ('tipo', '=', 'P'), ('id', '=', 2)])
        res = etapa_pool.name_get(cr, uid, etapa_ids)
        return res

    def _group_etapa_orcamento_id(self, cr, uid, grupos_atuais_ids, domain, read_group_order=None, access_rights_uid=None, context={}):
        etapa_pool = self.pool.get('sale.etapa')
        etapa_ids = etapa_pool.search(cr, uid, ['|', ('tipo', '=', 'V'), ('id', '=', 3)])
        res = etapa_pool.name_get(cr, uid, etapa_ids)
        return res

    def _group_etapa_ordem_servico_id(self, cr, uid, grupos_atuais_ids, domain, read_group_order=None, access_rights_uid=None, context={}):
        etapa_pool = self.pool.get('sale.etapa')
        etapa_ids = etapa_pool.search(cr, uid, [('tipo', '=', 'O')])
        res = etapa_pool.name_get(cr, uid, etapa_ids)
        return res

    _group_by_full = {
        'etapa_prospecto_id': _group_etapa_prospecto_id,
        'etapa_orcamento_id': _group_etapa_orcamento_id,
        'etapa_ordem_servico_id': _group_etapa_ordem_servico_id,
    }

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=False, readonly=False),
        'lista_precos_alterada': fields.boolean(u'Lista de preços alterada?'),

        #
        # Campos do partner para o prospecto
        #
        'partner_cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', string=u'CNJP/CPF'),
        'partner_name': fields.related('partner_id', 'name', type='char', string=u'Nome'),
        'partner_fone': fields.related('partner_id', 'fone', type='char', string=u'Fone'),
        'partner_celular': fields.related('partner_id', 'celular', type='char', string=u'Celular'),
        'partner_email': fields.related('partner_id', 'email', type='char', string=u'Email'),
        #'partner_razao_social': fields.related('partner_id', 'razao_social', type='char', string=u'Razão Social/Nome'),
        #'partner_fantasia': fields.related('partner_id', 'fantasia', type='char', string=u'Fantasia'),
        'partner_endereco': fields.related('partner_id', 'endereco', type='char', string=u'Endereço'),
        'partner_numero': fields.related('partner_id', 'numero', type='char', string=u'nº'),
        'partner_complemento': fields.related('partner_id', 'complemento', type='char', string=u'complemento'),
        'partner_bairro': fields.related('partner_id', 'bairro', type='char', string=u'Bairro'),
        'partner_municipio_id': fields.related('partner_id', 'municipio_id', type='many2one', relation='sped.municipio', string=u'Município'),
        'partner_cep': fields.related('partner_id', 'cep', type='char', string=u'CEP'),

        #
        # Para prospecto
        #
        'receita_esperada': fields.float(u'Receita esperada', digits=(18, 2)),
        'data_fechamento_esperada': fields.date(u'Data de fechamento esperada'),
        'porcentagem_fechamento': fields.float(u'Probabilidade de fechamento (%)'),

        #
        # Para o kanban do prospecto
        #
        'cor_kanban': fields.integer(u'Cor no kanban'),
        'etapa_prospecto_id': fields.function(_etapa_prospecto_id, type='many2one', relation='sale.etapa', string=u'Etapa prospecto', store=True, select=True),
        'etapa_orcamento_id': fields.function(_etapa_orcamento_id, type='many2one', relation='sale.etapa', string=u'Etapa orçamento', store=True, select=True),
        'etapa_ordem_servico_id': fields.function(_etapa_ordem_servico_id, type='many2one', relation='sale.etapa', string=u'Etapa ordem de serviço', store=True, select=True),

        #
        # Separação dos itens
        #
        'item_produto_ids': fields.one2many('sale.order.line', 'order_id', string=u'Produtos', domain=[['tipo_item', '=', 'P']]),
        'item_servico_ids': fields.one2many('sale.order.line', 'order_id', string=u'Serviços', domain=[['tipo_item', '=', 'S']]),
        'item_mensalidade_ids': fields.one2many('sale.order.line', 'order_id', string=u'Mensalidades', domain=[['tipo_item', '=', 'M']]),

        'amount_untaxed': fields.function(_amount_all, type='float', digits=(18, 2), string=u'Valor sem impostos', store=STORE_TOTAIS, multi='sums'),
        'amount_tax': fields.function(_amount_all, type='float', digits=(18, 2), string=u'Impostos', store=STORE_TOTAIS, multi='sums'),
        'amount_total': fields.function(_amount_all, type='float', digits=(18, 2), string=u'Valor total', store=STORE_TOTAIS, multi='sums'),

        'vr_total_produtos': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total dos produtos', store=STORE_TOTAIS),
        'vr_total_produtos_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Total dos produtos', store=False),

        'vr_total_produtos_sem_desconto': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total dos produtos sem desconto', store=STORE_TOTAIS),
        'vr_total_produtos_sem_desconto_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Total dos produtos sem desconto', store=False),

        'vr_total_servicos': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total dos serviços', store=STORE_TOTAIS),
        'vr_total_servicos_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Total dos serviços', store=False),

        'vr_total_servicos_sem_desconto': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total dos serviços sem desconto', store=STORE_TOTAIS),
        'vr_total_servicos_sem_desconto_readonly': fields.function(_field_readonly, type='float', digits=(18, 2), string=u'Total dos serviços sem desconto', store=False),

        'vr_total_mensalidades': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total das mensalidades', store=STORE_TOTAIS),
        'vr_total_mensalidades_sem_desconto': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Total das mensalidades sem desconto', store=STORE_TOTAIS),

        'vr_mensal_locacao': fields.float(u'Mensalidade locação', digits=(18, 2)),
        'vr_mensal_total': fields.function(_valores_separados, type='float', digits=(18, 2), string=u'Mensalidade total', store=STORE_TOTAIS),

        #
        # Margem de contribuição
        #
        'vr_simples_produtos':              fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do SIMPLES'),
        'vr_icms_proprio_produtos':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ICMS próprio'),
        'vr_diferencial_aliquota_produtos': fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do DIFA'),
        'vr_ipi_produtos':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IPI'),
        'vr_iss_produtos':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ISS'),
        'vr_pis_proprio_produtos':          fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do PIS'),
        'vr_cofins_proprio_produtos':       fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do COFINS'),
        'vr_csll_produtos':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da CSLL'),
        'vr_irrf_produtos':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IRPJ'),
        'total_imposto_produtos':           fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Total do imposto'),
        'vr_produto_base_produtos':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor base do produto/serviço original'),
        'vr_comissao_produtos':             fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da comissão'),
        'vr_margem_contribuicao_produtos':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),
        'al_margem_contribuicao_produtos':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),

        'vr_simples_servicos':              fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do SIMPLES'),
        'vr_icms_proprio_servicos':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ICMS próprio'),
        'vr_diferencial_aliquota_servicos': fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do DIFA'),
        'vr_ipi_servicos':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IPI'),
        'vr_iss_servicos':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ISS'),
        'vr_pis_proprio_servicos':          fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do PIS'),
        'vr_cofins_proprio_servicos':       fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do COFINS'),
        'vr_csll_servicos':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da CSLL'),
        'vr_irrf_servicos':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IRPJ'),
        'total_imposto_servicos':           fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Total do imposto'),
        'vr_produto_base_servicos':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor base do produto/serviço original'),
        'vr_comissao_servicos':             fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da comissão'),
        'vr_margem_contribuicao_servicos':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),
        'al_margem_contribuicao_servicos':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),

        'vr_simples_mensalidades':              fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do SIMPLES'),
        'vr_icms_proprio_mensalidades':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ICMS próprio'),
        'vr_diferencial_aliquota_mensalidades': fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do DIFA'),
        'vr_ipi_mensalidades':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IPI'),
        'vr_iss_mensalidades':                  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do ISS'),
        'vr_pis_proprio_mensalidades':          fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do PIS'),
        'vr_cofins_proprio_mensalidades':       fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do COFINS'),
        'vr_csll_mensalidades':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da CSLL'),
        'vr_irrf_mensalidades':                 fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor do IRPJ'),
        'total_imposto_mensalidades':           fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Total do imposto'),
        'vr_produto_base_mensalidades':         fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor base do produto/serviço original'),
        'vr_comissao_mensalidades':             fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Valor da comissão'),
        'vr_margem_contribuicao_mensalidades':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),
        'al_margem_contribuicao_mensalidades':  fields.function(_valores_separados, type='float', digits=(18, 2), store=True, string=u'Margem de contribuição'),

        #
        # Gráficos da margem de contribuição
        #
        'margem_contribuicao_produtos_ids': fields.one2many('sale.margem.contribuicao', 'sale_id', string=u'Margem de contribuição', domain=[('tipo', '=', 'P')]),
        'margem_contribuicao_servicos_ids': fields.one2many('sale.margem.contribuicao', 'sale_id', string=u'Margem de contribuição', domain=[('tipo', '=', 'S')]),
        'margem_contribuicao_mensalidades_ids': fields.one2many('sale.margem.contribuicao', 'sale_id', string=u'Margem de contribuição', domain=[('tipo', '=', 'M')]),
        'margem_contribuicao_ids': fields.one2many('sale.margem.contribuicao', 'sale_id', string=u'Margem de contribuição'),

        #
        # Locação
        #
        'meses_retorno_locacao_original': fields.related('pricelist_id', 'meses_retorno_locacao', string=u'Meses para retorno'),
        'meses_retorno_locacao': fields.float(u'Meses para retorno', digits=(21, 11)),
        'meses_retorno_locacao_excedido': fields.boolean(u'Excedeu o limite de meses pra retorno?'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato'),
        'vr_mensal_atual': fields.float(u'Mensalidade atual', digits=(18,2)),

        #
        # Simulação de parcelas
        #
        #'simulacao_parcelas': fields.function(_simulacao_parcelas, type='text', string=u'Simulação de parcelas', store=STORE_TOTAIS),
        'vr_entrada': fields.float(u'Entrada', digits=(18, 2)),
        'simulacao_parcelas_readonly_ids': fields.function(_simulacao_parcelas, type='one2many', relation='sale.simulacao.parcelas', string=u'Simulação de parcelas'),
        'simulacao_parcelas_ids': fields.one2many('sale.simulacao.parcelas', 'sale_id', string=u'Simulação de parcelas'),

        #
        # Novo controle de etapas do orçamento
        #
        'etapa_id': fields.many2one('sale.etapa', u'Etapa', ondelete='restrict'),
        'etapa_id_readonly': fields.function(_field_readonly, type='many2one', relation='sale.etapa', string=u'Etapa'),
        'codigo': fields.related('etapa_id', 'codigo', type='char', string=u'Código', store=False, select=True),
        'filtro_etapa': fields.related('etapa_id', 'filtro_etapa', type='char', string=u'filtro', store=False, select=True),
        'proxima_etapa_id': fields.many2one('sale.etapa', u'Próxima Etapa'),
        'etapa_seguinte_ids': fields.related('etapa_id','etapa_seguinte_ids', type='many2many', relation='sale.etapa', string=u'Próxima Etapa', store=False),

        'alimenta_estoque': fields.related('etapa_id','alimenta_estoque', type='boolean', string=u'Alimenta estoque?', store=False),

        'trava_comercial': fields.related('etapa_id','trava_comercial', type='boolean', string=u'Trava comercial?', store=False),
        'trava_tecnico': fields.related('etapa_id','trava_tecnico', type='boolean', string=u'Trava técnico?', store=False),
        'libera_faturamento_contrato': fields.related('etapa_id','libera_faturamento_contrato', type='boolean', string=u'Libera o faturamento/contrato?', store=True),
        'libera_monitoramento': fields.related('etapa_id','libera_monitoramento', type='boolean', string=u'Libera o monitoramento?', store=False),

        'data_ultima_etapa': fields.datetime(u'Data da última etapa'),
        'data_proxima_etapa': fields.datetime(u'Data da próxima etapa'),
        'tempo_etapa': fields.function(_tempo_etapa, type='integer', string=u'Tempo (dias)'),

        'etapa_historico_ids': fields.one2many('sale.etapa.historico', 'sale_id', u'Histórico de etapas'),

        'dias_validade': fields.float(u'Dias de validade'),

        'canal_id': fields.many2one('sale.canal', u'Canal', ondelete='restrict'),
        'categoria_id': fields.many2one('sale.categoria', u'Categoria', ondelete='restrict'),
        'categoria_ids': fields.many2many('sale.categoria', 'sale_categorias', 'sale_id', 'categoria_id', u'Categorias'),

        #
        # Para tratamento da OS
        #
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo'),
        'tecnico_id': fields.many2one('res.users', u'Técnico'),
        'tipo_os_id': fields.many2one('sale.tipo.os', u'Tipo da OS'),
        'prioridade_id': fields.many2one('sale.prioridade.os', u'Prioridade'),
        'prioridade_dias': fields.related('prioridade_id', 'dias', string=u'Dias', type='integer'),
        'defeito_id': fields.many2one('sale.defeito.os', u'Defeito'),
        'defeito_obs': fields.text(u'Defeito'),

        #
        # Controle do estoque e faturamento/contrato
        #
        'estoque_alimentado': fields.boolean(u'Estoque alimentado?'),
        'faturado': fields.boolean(u'Faturado?'),
        'finan_contrato_gerado_id': fields.many2one('finan.contrato', u'Contrato novo'),

        #
        # Orçamento de referência
        #
        'order_referencia_id': fields.many2one('sale.order.referencia', u'Orçamento de referência'),

        #
        # Informações financeiras
        #
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', select=True, ondelete='restrict'),
        'vencido_ids': fields.function(_finan_vencidos, type='many2many', relation='finan.lancamento', string=u'Lançamentos vencidos'),
        'pendencia_financeira': fields.function(_finan_vencidos, type='boolean', string=u'Pendência financeira'),
        'meeting_ids': fields.one2many('crm.meeting', 'sale_order_id', u'Agendamentos'),
        'stock_move_ids': fields.one2many('stock.move', 'sale_order_id', u'Movimentações de estoque'),
        'stock_move_saida_ids': fields.one2many('stock.move', 'sale_order_id', u'Movimentações de estoque', domain=[('eh_saida', '=', True)]),
        'stock_move_retorno_ids': fields.one2many('stock.move', 'sale_order_id', u'Movimentações de estoque', domain=[('eh_saida', '=', False)]),
        'stock_location_saida_id': fields.related('tipo_os_id', 'stock_location_saida_id', type='many2one', relation='stock.location', string=u'Local de saída'),
        'stock_location_entrada_id': fields.related('tipo_os_id', 'stock_location_entrada_id', type='many2one', relation='stock.location', string=u'Local de entrada'),
        'lo_modelo_id': fields.many2one('lo.modelo',u'Modelo de Contrato',  domain=[['tabela', '=', 'sale.order']]),
    }

    _defaults = {
        #'etapa_id': 1,
        #'proxima_etapa_id': 2,
        'dias_validade': 30,
        'meses_retorno_locacao': 0,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=c),
        'partner_id': lambda self, cr, uid, context: self.pool.get('res.company').browse(cr, uid, self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)).partner_id.id if context.get('default_modelo', False) else False,
    }

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, vr_total_produtos, context={}):
        if not pricelist_id:
            return {}

        pricelist_obj = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id)

        res = {}
        valores = {}
        res['value'] = valores
        valores['meses_retorno_locacao_original'] = pricelist_obj.meses_retorno_locacao
        valores['meses_retorno_locacao'] = pricelist_obj.meses_retorno_locacao

        if pricelist_obj.meses_retorno_locacao:
            valores['finan_contrato_id'] = False
            if vr_total_produtos:
                valores['vr_mensal_locacao'] = D(vr_total_produtos or 0) / D(pricelist_obj.meses_retorno_locacao or 1)

        if pricelist_obj.tipo_os_id:
            valores['tipo_os_id'] = pricelist_obj.tipo_os_id.id

        valores['lista_precos_alterada'] = True

        return res

    def avanca_etapa(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        prospecto_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seguranca', 'sale_order_seguranca_prospecto_form')[1]
        orcamento_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seguranca', 'sale_order_seguranca_orcamento_form')[1]
        os_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seguranca', 'sale_order_seguranca_ordem_servico_form')[1]

        res = {
            'type': 'ir.actions.act_window',
            'name': 'Prospecto',
            'res_model': 'sale.order',
            'res_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            #'target': 'new',  # isto faz abrir numa janela no meio da tela
            'target': 'inline',  # Abre na mesma janela, sem ser no meio da tela
            #'context': {'model': 'sale.order', 'active_ids': [lancamento_id]},
        }

        for sale_obj in self.browse(cr, uid, ids):
            if not sale_obj.proxima_etapa_id:
                raise osv.except_osv(u'Inválido !', u'Selecione a próxima etapa')

            dados = {
                'etapa_id': sale_obj.proxima_etapa_id.id,
                'proxima_etapa_id': False,
                'data_proxima_etapa': fields.datetime.now(),
                'data_ultima_etapa': sale_obj.data_proxima_etapa or sale_obj.create_date,
                'etapa_historico_ids': [[0, False, {'etapa_id': sale_obj.proxima_etapa_id.id, 'data_proxima_etapa': fields.datetime.now(), 'data_ultima_etapa': sale_obj.data_proxima_etapa or sale_obj.create_date}]]
            }

            if sale_obj.proxima_etapa_id.tipo == 'P':
                res['view_id'] = prospecto_form_id
                res['name'] = u'Prospecto'
                res['context'] = {'form_view_ref': 'seguranca.sale_order_seguranca_prospecto_form', 'tree_view_ref': 'seguranca.sale_order_seguranca_prospecto_tree', 'search_view_ref': 'seguranca.sale_order_seguranca_prospecto_search'}
            elif sale_obj.proxima_etapa_id.tipo == 'V':
                res['view_id'] = orcamento_form_id
                res['name'] = u'Orçamento'
                res['context'] = {'form_view_ref': 'seguranca.sale_order_seguranca_orcamento_form', 'tree_view_ref': 'seguranca.sale_order_seguranca_orcamento_tree', 'search_view_ref': 'seguranca.sale_order_seguranca_orcamento_search'}
            elif sale_obj.proxima_etapa_id.tipo == 'O':
                res['view_id'] = os_form_id
                res['name'] = u'Ordem de Serviço'
                res['context'] = {'form_view_ref': 'seguranca.sale_order_seguranca_ordem_servico_form', 'tree_view_ref': 'seguranca.sale_order_seguranca_ordem_servico_tree', 'search_view_ref': 'seguranca.sale_order_seguranca_ordem_servico_search'}

            res['res_id'] = sale_obj.id

            if sale_obj.etapa_id.tipo == 'V' and sale_obj.proxima_etapa_id.tipo == 'O':
                #
                # Para transformar o orçamento em OS, tem que ter todos os dados do cliente,
                # a forma de pagamento e a condição de pagamento
                #
                if not sale_obj.finan_formapagamento_id:
                    raise osv.except_osv(u'Inválido!', u'Preencha a forma de pagamento na aba Fechamento antes de prosseguir para a próxima etapa.')

                if not sale_obj.payment_term:
                    raise osv.except_osv(u'Inválido!', u'Preencha a condição de pagamento na aba Fechamento antes de prosseguir para a próxima etapa.')

                if not (sale_obj.partner_id.cnpj_cpf and sale_obj.partner_id.razao_social and sale_obj.partner_id.endereco and
                        sale_obj.partner_id.numero and sale_obj.partner_id.bairro and sale_obj.partner_id.municipio_id and
                        sale_obj.partner_id.cep):
                    raise osv.except_osv(u'Inválido!', u'Antes de prosseguir para próxima etapa, preencha os dados completos do cliente no cadastro de cliente: CNPJ/CPF, razão social/nome, endereço, número, bairro, município, CEP')

            if sale_obj.proxima_etapa_id.alimenta_estoque:
                sale_obj.gera_alimenta_estoque()

            sale_obj.write(dados)

        return res

    def create(self, cr, uid, dados, context={}):
        if 'etapa_id' in dados:
            dados['etapa_historico_ids'] = [[0, False, {'etapa_id': dados['etapa_id']}]]

        if 'finan_contrato_id' in dados:
            valores = self.onchange_finan_contrato_id(cr, uid, False, dados['finan_contrato_id'])
            dados['vr_mensal_atual'] = valores['value']['vr_mensal_atual']

        return super(sale_order, self).create(cr, uid, dados, context={})

    def write(self, cr, uid, ids, dados, context={}):
        if 'finan_contrato_id' in dados:
            valores = self.onchange_finan_contrato_id(cr, uid, False, dados['finan_contrato_id'])
            dados['vr_mensal_atual'] = valores['value']['vr_mensal_atual']

        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        self.ajusta_mensalidade_locacao(cr, uid, ids)
        self.ajusta_margens_contribuicao(cr, uid, ids)

        return res

    def onchange_payment_term(self, cr, uid, ids, payment_term_id, amount_total, vr_total_servicos, meses_retorno_locacao_original, vr_entrada, context={}):
        if not (payment_term_id and amount_total):
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        texto = u'Condição de pagamento\n'
        texto += u'Parcela\tVencimento\t\tValor\n'

        condicao_obj = self.pool.get('account.payment.term').browse(cr, uid, payment_term_id)

        #
        # É locação?
        # Se sim, a condição de pagamento só vai se aplicar pros serviços
        #
        #print('entrada', vr_entrada)
        if meses_retorno_locacao_original:
            parcelas = condicao_obj.calcula(vr_total_servicos, data_base=hoje(), entrada=vr_entrada)

        else:
            parcelas = condicao_obj.calcula(amount_total, data_base=hoje(), entrada=vr_entrada)

        simulacao_parcelas_ids = [[5, False, {}]]
        i = 1
        total = D(0)

        #if vr_entrada:
            #dados = {
                #'numero': str(i).zfill(3),
                #'data': str(hoje()),
                #'valor': vr_entrada,
            #}
            #simulacao_parcelas_ids.append([0, False, dados] )
            #i += 1

        for parcela in parcelas:
            dados = {
                'numero': str(i).zfill(3),
                'data': str(parcela.data) if parcela.data is not None else False,
                'valor': parcela.valor,
            }
            simulacao_parcelas_ids.append([0, False, dados] )
            i += 1

        valores['simulacao_parcelas_readonly_ids'] = simulacao_parcelas_ids
        valores['simulacao_parcelas_ids'] = simulacao_parcelas_ids

        return res

    def onchange_locacao(self, cr, uid, ids, meses_retorno_locacao, vr_mensal_locacao, amount_total, vr_total_produtos, vr_total_servicos, vr_total_mensalidades, meses_retorno_locacao_original, context={}):
        if (not meses_retorno_locacao) and (not vr_mensal_locacao):
            return {}

        if not amount_total:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        amount_total = D(amount_total or 0).quantize(D('0.01'))
        vr_total_produtos = D(vr_total_produtos or 0).quantize(D('0.01'))
        vr_total_servicos = D(vr_total_servicos or 0).quantize(D('0.01'))
        vr_mensal_locacao = D(vr_mensal_locacao or 0).quantize(D('0.01'))

        if not meses_retorno_locacao:
            #meses_retorno_locacao = amount_total / D(vr_mensal_locacao or 1)
            meses_retorno_locacao = vr_total_produtos / D(vr_mensal_locacao or 1)
            meses_retorno_locacao = meses_retorno_locacao
        else:
            meses_retorno_locacao = D(meses_retorno_locacao or 1)

        #vr_mensal_locacao = amount_total / meses_retorno_locacao
        vr_mensal_locacao = vr_total_produtos / meses_retorno_locacao
        vr_mensal_locacao = vr_mensal_locacao.quantize(D('0.01'))

        valores['meses_retorno_locacao'] = meses_retorno_locacao
        valores['vr_mensal_locacao'] = vr_mensal_locacao
        valores['vr_mensal_total'] = vr_mensal_locacao + D(vr_total_mensalidades or 0)

        if meses_retorno_locacao > meses_retorno_locacao_original:
            valores['meses_retorno_locacao_excedido'] = True
        else:
            valores['meses_retorno_locacao_excedido'] = False

        return res

    def onchange_al_desconto_rateio(self, cr, uid, ids, al_desconto_rateio, vr_desconto_rateio, vr_total_produtos_sem_desconto, tipo='P'):
        res = {}
        valores = {}
        res['value'] = valores

        vr_total_produtos_sem_desconto = D(vr_total_produtos_sem_desconto or 0).quantize(D('0.01'))

        if al_desconto_rateio is not None:
            al_desconto_rateio = D(al_desconto_rateio or 0)
            vr_desconto_rateio = vr_total_produtos_sem_desconto * al_desconto_rateio
            vr_desconto_rateio /= 100
            vr_desconto_rateio = vr_desconto_rateio.quantize(D('0.01'))

            valores['amount_total'] = 0

            if tipo == 'P':
                valores['vr_desconto_rateio'] = vr_desconto_rateio
                valores['vr_total_produtos'] = 0
            elif tipo == 'S':
                valores['vr_desconto_rateio_servicos'] = vr_desconto_rateio
                valores['vr_total_servicos'] = 0
            elif tipo == 'M':
                valores['vr_desconto_rateio_mensalidades'] = vr_desconto_rateio
                valores['vr_total_mensalidades'] = 0

        elif vr_desconto_rateio is not None:
            vr_desconto_rateio = D(vr_desconto_rateio or 0).quantize(D('0.01'))
            al_desconto_rateio = vr_desconto_rateio / vr_total_produtos_sem_desconto
            al_desconto_rateio *= 100
            al_desconto_rateio = al_desconto_rateio

            valores['amount_total'] = 0

            if tipo == 'P':
                valores['al_desconto_rateio'] = al_desconto_rateio
                valores['vr_total_produtos'] = 0
            elif tipo == 'S':
                valores['al_desconto_rateio_servicos'] = al_desconto_rateio
                valores['vr_total_servicos'] = 0
            elif tipo == 'M':
                valores['al_desconto_rateio_mensalidades'] = al_desconto_rateio
                valores['vr_total_mensalidades'] = 0

        return res

    def ajusta_mensalidade_locacao(self, cr, uid, ids, context={}):
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if not sale_obj.meses_retorno_locacao_original:
                continue

            #vr_mensal_locacao = D(sale_obj.amount_total or 0) / D(sale_obj.meses_retorno_locacao or 1)
            vr_mensal_locacao = D(sale_obj.vr_total_produtos or 0) / D(sale_obj.meses_retorno_locacao or 1)
            vr_mensal_total = vr_mensal_locacao + D(sale_obj.vr_total_mensalidades or 0) + D(sale_obj.vr_mensal_atual or 0)

            cr.execute("""
                update sale_order set
                    vr_mensal_locacao = {vr_mensal_locacao},
                    vr_mensal_total = {vr_mensal_total}
                where
                    id = {id};
            """.format(id=sale_obj.id, vr_mensal_locacao=vr_mensal_locacao, vr_mensal_total=vr_mensal_total))

    def onchange_partner_id_locacao(self, cr, uid, ids, partner_id, company_id, meses_retorno_locacao_original, context={}):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if meses_retorno_locacao_original:
            contrato_pool = self.pool.get('finan.contrato')
            contrato_ids = contrato_pool.search(cr, uid, [('partner_id', '=', partner_id), ('company_id', '=', company_id), ('data_distrato', '=', False)])

            if len(contrato_ids):
                res['value']['finan_contrato_id'] = contrato_ids[0]

        else:
            res['value']['finan_contrato_id'] = False

        return res

    def onchange_finan_contrato_id(self, cr, uid, ids, finan_contrato_id, vr_mensal_locacao=0, vr_total_mensalidades=0):
        res = {}
        valores = {}
        res['value'] = valores

        vr_mensal_atual = D(0)

        if finan_contrato_id:
            contrato_pool = self.pool.get('finan.contrato')
            contrato_obj = contrato_pool.browse(cr, uid, finan_contrato_id)
            vr_mensal_atual = D(contrato_obj.valor_mensal or 0).quantize(D('0.01'))

        valores['vr_mensal_atual'] = vr_mensal_atual
        valores['vr_mensal_total'] = vr_mensal_atual + D(vr_mensal_locacao or 0) + D(vr_total_mensalidades or 0)

        return res

    def onchange_order_referencia_id(self, cr, uid, ids, order_referencia_id, pricelist_id, partner_id, date_order, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not order_referencia_id:
            return res

        referencia_obj = self.pool.get('sale.order.referencia').browse(cr, uid, order_referencia_id)

        item_pool = self.pool.get('sale.order.line')

        produto_ids = [[5, False, {}]]
        for item_obj in referencia_obj.item_produto_ids:
            contexto_item = copy(context)
            contexto_item['default_tipo_item'] = 'P'
            dados = item_pool.product_id_change(cr, uid, False, pricelist_id, item_obj.product_id.id, item_obj.quantidade, False, False, False, False, partner_id, False, True, date_order, False, False, False, contexto_item)

            dados_item = {}
            for chave in dados['value']:
                if not isinstance(dados['value'][chave], DicionarioBrasil):
                    dados_item[chave] = dados['value'][chave]

            dados_item['tipo_item'] = 'P'
            produto_ids.append([0, False, dados_item])

        valores['item_produto_ids'] = produto_ids

        servico_ids = [[5, False, {}]]
        for item_obj in referencia_obj.item_servico_ids:
            contexto_item = copy(context)
            contexto_item['default_tipo_item'] = 'S'
            dados = item_pool.product_id_change(cr, uid, False, pricelist_id, item_obj.product_id.id, item_obj.quantidade, False, False, False, False, partner_id, False, True, date_order, False, False, False, contexto_item)

            dados_item = {}
            for chave in dados['value']:
                if not isinstance(dados['value'][chave], DicionarioBrasil):
                    dados_item[chave] = dados['value'][chave]

            dados_item['tipo_item'] = 'S'
            servico_ids.append([0, False, dados_item])

        valores['item_servico_ids'] = servico_ids

        mensalidade_ids = [[5, False, {}]]
        for item_obj in referencia_obj.item_mensalidade_ids:
            contexto_item = copy(context)
            contexto_item['default_tipo_item'] = 'M'
            dados = item_pool.product_id_change(cr, uid, False, pricelist_id, item_obj.product_id.id, item_obj.quantidade, False, False, False, False, partner_id, False, True, date_order, False, False, False, contexto_item)

            dados_item = {}
            for chave in dados['value']:
                if not isinstance(dados['value'][chave], DicionarioBrasil):
                    dados_item[chave] = dados['value'][chave]

            dados_item['tipo_item'] = 'M'
            mensalidade_ids.append([0, False, dados_item])

        valores['item_mensalidade_ids'] = mensalidade_ids

        return res

    def onchange_tipo_os_id(self, cr, uid, ids, tipo_os_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not tipo_os_id:
            return res

        tipo_os_obj = self.pool.get('sale.tipo.os').browse(cr, uid, tipo_os_id)

        if tipo_os_obj.stock_location_saida_id:
            valores['stock_location_saida_id'] = tipo_os_obj.stock_location_saida_id.id

        if tipo_os_obj.stock_location_entrada_id:
            valores['stock_location_entrada_id'] = tipo_os_obj.stock_location_entrada_id.id

        return res

    def gera_alimenta_estoque(self, cr, uid, ids, context={}):
        move_pool = self.pool.get('stock.move')

        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.estoque_alimentado:
                continue

            #
            # Vamos criar as saídas do estoque
            #
            for item_obj in sale_obj.item_produto_ids:
                dados = {
                    'sale_order_id': sale_obj.id,
                    'tipo_os_id': sale_obj.tipo_os_id.id,
                    'product_id': item_obj.product_id.id,
                    'product_uom': item_obj.product_id.uom_id.id,
                    'product_qty': item_obj.product_uom_qty,
                    'company_id': sale_obj.company_id.id,
                    'partner_id': sale_obj.partner_id.id,
                    'origin': sale_obj.name,
                    'location_id': sale_obj.stock_location_saida_id.id,
                    'location_dest_id': sale_obj.stock_location_entrada_id.id,
                    'name': sale_obj.name + '; ' + item_obj.name,
                    'eh_saida': True,
                }
                move_pool.create(cr, uid, dados)

            sale_obj.write({'estoque_alimentado': True})

    def gerar_contrato(self, cr, uid, ids, context={}):
        contrato_pool = self.pool.get('finan.contrato')

        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.finan_contrato_id:
                continue

            #
            # Vamos gerar o novo contrato
            #
            dados = {
                'sale_order_id': sale_obj.id,
                'company_id': sale_obj.company_id.id,
                'cnpj_cpf': sale_obj.company_id.partner_id.cnpj_cpf,
                'raiz_cnpj': sale_obj.company_id.partner_id.cnpj_cpf[:10],
                'partner_id': sale_obj.partner_id.id,
                'natureza': 'IR',
                #'dia_vencimento': sale_obj.dia_vencimento,
                #'data_assinatura': sale_obj.data_assinatura,
                #'data_inicio': sale_obj.data_inicio,
                'duracao': sale_obj.meses_retorno_locacao_original,
                'vendedor_id': sale_obj.user_id.id,
                'valor_mensal': sale_obj.vr_mensal_total,
            }

            contrato_id = contrato_pool.create(cr, uid, dados)
            sale_obj.write({'finan_contrato_gerado_id': contrato_id})


    def _gerar_orcamento(self, cr, uid, ids, mostra_margem_contribuicao=False, context={}):
        attachment_pool = self.pool.get('ir.attachment')

        for sale_obj in self.browse(cr, uid, ids, context=context):
            rel = Report('Orcamento Seguranca', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'seguranca_orcamento.jrxml')
            rel.parametros['OS_ID'] = sale_obj.id
            rel.parametros['MOSTRA_MARGEM_CONTRIBUICAO'] = mostra_margem_contribuicao

            pdf, formato = rel.execute()

            if sale_obj.etapa_id.tipo != 'O':
                if mostra_margem_contribuicao:
                    nome = u'OrcamentoEspelho_' + sale_obj.name.replace(' ', '_') + '.pdf'
                else:
                    nome = u'Orcamento_' + sale_obj.name.replace(' ', '_') + '.pdf'
            else:
                nome = u'OS_' + sale_obj.name.replace(' ', '_') + '.pdf'

            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', sale_obj.id), ('name', '=', nome)])
            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome,
                'datas_fname': nome,
                'res_model': 'sale.order',
                'res_id': sale_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        return ids

    def imprime_orcamento(self, cr, uid, ids, context={}):
        return self._gerar_orcamento(cr, uid, ids, mostra_margem_contribuicao=False, context=context)

    def imprime_orcamento_espelho(self, cr, uid, ids, context={}):
        return self._gerar_orcamento(cr, uid, ids, mostra_margem_contribuicao=True, context=context)

    def gera_contrato_venda(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        modelo_pool = self.pool.get('lo.modelo')

        for sale_obj in self.browse(cr, uid, ids):

            if sale_obj.lo_modelo_id:
                modelo_obj = sale_obj.lo_modelo_id

                dados = {
                    'sale_obj': sale_obj,
                    'cliente': sale_obj.partner_id,
                    'produtos': sale_obj.item_produto_ids,
                }

                nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                nome_arquivo += '_' + sale_obj.name

                attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', sale_obj.id), ('name', 'like', nome_arquivo)])
                attachment_pool.unlink(cr, uid, attachment_ids)

                nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                nome_arquivo += '.'
                nome_arquivo += modelo_obj.formato or 'doc'

                arquivo = modelo_obj.gera_modelo_novo(dados,formato=modelo_obj.formato)

                dados = {
                    'datas': arquivo,
                    'name': nome_arquivo,
                    'datas_fname': nome_arquivo,
                    'res_model': 'sale.order',
                    'res_id': sale_obj.id,
                    'file_type': 'application/msword',
                }
                attachment_pool.create(cr, uid, dados)

        return

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        print(fone, celular)
        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            return {'value': {'partner_fone': fone}}

        elif celular is not None and celular:
            if not valida_fone_internacional(celular) and not valida_fone_celular(celular):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            celular = formata_fone(celular)
            return {'value': {'partner_celular': celular}}

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'partner_cep': cep[:5] + '-' + cep[5:]}}

    def ajusta_margens_contribuicao(self, cr, uid, ids, context={}):
        TIPOS_MARGEM = {
            'P': 'produtos',
            'S': 'servicos',
            'M': 'mensalidades',
        }

        CAMPOS_MARGEM = {
            #'vr_total_': u'(+) Valor',
            'vr_margem_contribuicao_': u'(=) Margem de contribuição',
            'vr_simples_': u'(-) SIMPLES',
            'vr_diferencial_aliquota_': u'(-) DIFA',
            'vr_iss_': u'(-) ISS',
            'vr_pis_proprio_': u'(-) PIS',
            'vr_cofins_proprio_': u'(-) COFINS',
            'vr_csll_': u'(-) CSLL',
            'vr_irrf_': u'(-) IRPJ',
            'vr_produto_base_': u'(-) Custo',
            'vr_comissao_': u'(-) Comissão',
        }

        for sale_obj in self.browse(cr, uid, ids, context=context):
            cr.execute('delete from sale_margem_contribuicao where sale_id = ' + str(sale_obj.id) + ';')

            for tipo in TIPOS_MARGEM:
                nome_tipo = TIPOS_MARGEM[tipo]

                if sale_obj.vr_margem_contribuicao_produtos:
                    for campo in CAMPOS_MARGEM:
                        if not getattr(sale_obj, campo + nome_tipo, False):
                            continue

                        valor = D(getattr(sale_obj, campo + nome_tipo, False) or 0)
                        nome_campo = CAMPOS_MARGEM[campo]

                        if valor < 0:
                            if campo != 'vr_margem_contribuicao_':
                                continue
                            else:
                                nome_campo = u'(=) Prejuízo'
                                valor *= -1

                        dados = {
                            'sale_id': sale_obj.id,
                            'tipo': tipo,
                            'campo': nome_campo,
                            'valor': valor,
                        }



                        cr.execute(u"""
                            insert into sale_margem_contribuicao (sale_id, tipo, campo, valor)
                                values ({sale_id}, '{tipo}', '{campo}', {valor});
                            """.format(**dados))

    def atualiza_lista_precos(self, cr, uid, ids, context={}):
        self.recalcula_fora_validade(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'lista_precos_alterada': False}, context=context)

sale_order()
