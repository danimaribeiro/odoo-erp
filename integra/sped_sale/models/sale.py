# -*- encoding: utf-8 -*-
import os
import base64
from sped.constante_tributaria import SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO
from sped.models.fields import CampoDinheiro
from osv import osv, fields
from pybrasil.base import DicionarioBrasil
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID
from copy import copy
import decimal_precision as dp
from tools.translate import _
from sale_order_line import *
from finan.wizard.finan_relatorio import Report
DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime, hoje, formata_data
from pybrasil.valor import formata_valor
from sped.constante_tributaria import *


STORE_TOTAIS = {
    'sale.order': (
        lambda order_pool, cr, uid, ids, context={}: ids,
        ['vr_desconto_rateio', 'vr_desconto_rateio_servicos', 'vr_desconto_rateio_mensalidades', 'payment_term_id', 'order_line', 'percentual_acessorios'],
        20
    ),

    'sale.order.line': (
        lambda item_pool, cr, uid, ids, context={}: [item_obj.order_id.id for item_obj in item_pool.browse(cr, uid, ids)],
        ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos', 'vr_total_venda_impostos', 'margem', 'desconto', 'porcentagem_imposto', 'proporcao_imposto', 'vr_taxa_juros', 'vr_produtos', 'vr_frete', 'vr_seguro', 'vr_outras', 'vr_desconto', 'vr_ipi', 'vr_icms_st', 'vr_ii', 'credita_icms_proprio', 'cfop_id', 'credita_icms_st',
         'credita_ipi', 'credita_pis_cofins', 'quantidade', 'fator_quantidade', 'vr_custo', 'vr_simples'],
        10
    ),
}


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        currency_pool = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': D(0),
                'amount_tax': D(0),
                'amount_total': D(0),
            }
            valor_sem_impostos = D(0)
            valor_com_impostos = D(0)
            total_impostos = D(0)

            currency_obj = order.pricelist_id.currency_id

            for item_obj in order.order_line:
                valor_sem_impostos += D(item_obj.price_subtotal or 0)
                valor_com_impostos += D(item_obj.vr_total_venda_impostos or 0)
                valor_com_impostos += D(item_obj.vr_icms_st or 0)
                percentual_impostos = D(item_obj.total_imposto or 0) / D(item_obj.price_subtotal or 1)
                total_impostos += D(item_obj.vr_total_venda_impostos or 0) *  percentual_impostos

            #if order.vr_desconto_rateio:
                #valor_com_impostos -= D(order.vr_desconto_rateio)

            #res[order.id]['amount_tax'] = currency_pool.round(cr, uid, currency_obj, total_impostos)
            #res[order.id]['amount_untaxed'] = currency_pool.round(cr, uid, currency_obj, valor_sem_impostos)
            #res[order.id]['amount_total'] = currency_pool.round(cr, uid, currency_obj, valor_com_impostos)
            res[order.id]['amount_tax'] = total_impostos
            res[order.id]['amount_untaxed'] = valor_sem_impostos
            res[order.id]['amount_total'] = valor_com_impostos
            res[order.id]['vr_a_faturar'] = valor_com_impostos

        return res

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue

            tot = 0.0

            for nota_obj in sale.sped_documento_ids:
                if nota_obj.situacao in SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO:
                    tot += nota_obj.vr_produtos

                #if nota_obj.state not in ['autorizada', 'denegada']:
                    #tot += nota_obj.vr_produtos

            if tot:
                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_total or 1.00))
            else:
                res[sale.id] = 0.0

        return res

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = True
            invoice_existence = False
            for invoice in sale.invoice_ids:
                if invoice.state!='cancel':
                    invoice_existence = True
                    if invoice.state != 'paid':
                        res[sale.id] = False
                        break
            if not invoice_existence:
                res[sale.id] = False
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            for item_obj in doc_obj.order_line:
                soma += D(str(getattr(item_obj, nome_campo, 0)))

            soma = soma.quantize(D('0.01'))

            res[doc_obj.id] = soma

        return res

    _columns = {
        'state': fields.selection([
            ('draft', u'Orçamento'),
            #('waiting_date', u'Aguardando agendamento'),
            ('manual', u'Aprovado'),
            #('progress', u'Em andamento'),
            ('shipping_except', u'Exceção de entrega'),
            ('invoice_except', u'Exceção de faturamento'),
            ('done', u'Concluído'),
            ('cancel', u'Cancelado')
            ], u'Situação', readonly=True, help=u"Informa a Situação do orçamento ou pedido. A Situação de Exceção é automaticamente definida quando um Cancelamento ocorre na validação do faturamento (Exceção de faturamento) ou no processo de separação (Excessão de entrega). O 'Aguardando agendamento' é definido quando a fatura está confirmada, mas está esperando o agendamento na data do pedido.", select=True),

        'company_id': fields.many2one('res.company', string=u'Empresa', ondelete='restrict'),
        'shop_id': fields.many2one('sale.shop', u'Estabelecimento', required=False, readonly=False, states={'draft': [('readonly', False)]}),

        #'tipo_pessoa': fields.related('partner_id', 'tipo_pessoa', type='char', string='Tipo pessoa'),

        'regime_tributario': fields.related('company_id', 'regime_tributario', type='selection', selection=REGIME_TRIBUTARIO, string=u'Regime tributário', select=True, store=True),
        'operacao_id': fields.related('company_id', 'operacao_id', relation='sped.operacao', string=u'Operação padrão para venda (pessoa jurídica/padrão)', readonly=True),
        'operacao_pessoa_fisica_id': fields.related('company_id', 'operacao_pessoa_fisica_id', relation='sped.operacao', string=u'Operação padrão para venda (pessoa física)', readonly=True),
        'operacao_ativo_id': fields.related('company_id', 'operacao_ativo_id', relation='sped.operacao', string=u'Operação padrão para venda de ativo', readonly=True),
        'operacao_faturamento_antecipado_id': fields.related('company_id', 'operacao_faturamento_antecipado_id', relation='sped.operacao', string=u'Operação padrão para faturamento antecipado', readonly=True),

        #'tipo_pessoa': fields.related('company_id', 'tipo_pessoa', type='char', string='Tipo pessoa'),
        'operacao_fiscal_produto_id': fields.many2one('sped.operacao', u'Operação fiscal para produtos'),
        'operacao_fiscal_servico_id': fields.many2one('sped.operacao', u'Operação fiscal para serviços'),
        'sped_documento_ids': fields.many2many('sped.documento', 'sale_order_sped_documento', 'sale_order_id', 'sped_documento_id', string=u'Notas Fiscais'),

        'finan_formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'modalidade_frete': fields.selection(MODALIDADE_FRETE, u'Modalidade do frete'),
        'transportadora_id': fields.many2one('res.partner', u'Transportadora', domain=[('cnpj_cpf', '!=', False)]),

        #'vr_icms_proprio': CampoDinheiro(u'Valor do ICMS próprio'),
        'vr_icms_proprio': fields.function(_get_soma_funcao, type='float', string=u'Valor do ICMS próprio', store=STORE_TOTAIS, digits=(18, 2)),
        'vr_simples': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do SIMPLES Nacional'),

        #'vr_icms_st': CampoDinheiro(u'Valor do ICMS ST'),
        'vr_icms_st': fields.function(_get_soma_funcao, type='float', string=u'Valor do ICMS ST', store=STORE_TOTAIS, digits=(18, 2)),
        #'vr_ipi': CampoDinheiro(u'Valor do IPI'),
        'vr_ipi': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do IPI'),

        #'vr_ii': CampoDinheiro(u'Valor do imposto de importação'),
        #'vr_pis_proprio': CampoDinheiro(u'Valor do PIS próprio'),
        #'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS própria'),
        #'vr_iss': CampoDinheiro(u'Valor do ISS'),
        'vr_pis_proprio': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do PIS próprio'),
        'vr_cofins_proprio': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do COFINS própria'),
        'vr_iss': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do ISS'),

        #
        # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
        #
        #'vr_pis_retido': CampoDinheiro(u'PIS retido'),
        #'vr_cofins_retido': CampoDinheiro(u'COFINS retida'),
        #'vr_csll': CampoDinheiro(u'Valor da CSLL'),
        #'vr_irrf': CampoDinheiro(u'Valor do IRRF'),
        'vr_csll': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor da CSLL'),
        'vr_irrf': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor do IRRF'),

        #'vr_previdencia': CampoDinheiro(u'Base do INSS'),
        #'vr_iss_retido': CampoDinheiro(u'Valor do ISS'),
        #'total_imposto': CampoDinheiro(u'Total dos impostos'),
        'total_imposto': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Total dos impostos'),
        'vr_produto_base': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor base do produto/serviço original'),
        'vr_produto_original': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor original do produto/serviço'),

        'vr_liquido': fields.float(u'Valor líquido', digits=(18, 2)),
        'vr_desconto_rateio': fields.float(u'Valor desconto', digits=(18, 2)),
        'vr_desconto_rateio_servicos': fields.float(u'Valor desconto', digits=(18, 2)),
        'vr_desconto_rateio_mensalidades': fields.float(u'Valor desconto', digits=(18, 2)),
        'margem_liquida': fields.float(u'Margem líquida', digits=(18, 2)),
        #'vr_total_venda_impostos': fields.float(u'Valor venda'),
        'vr_total_venda_impostos': fields.function(_get_soma_funcao, type='float', store=STORE_TOTAIS, digits=(18, 2), string=u'Valor venda'),

        'amount_untaxed': fields.function(_amount_all, digits=(18, 2), string='Untaxed Amount',
            store=STORE_TOTAIS,
            #store = {
                #'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                #'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos'], 10),
            #},
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits=(18, 2), string='Taxes',
            store=STORE_TOTAIS,
            #store = {
                #'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                #'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos'], 10),
            #},
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits=(18, 2), string='Total',
            store=STORE_TOTAIS,
            #store = {
                #'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'vr_desconto_rateio'], 10),
                #'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'total_imposto', 'vr_unitario_venda_impostos', 'vr_total_venda_impostos'], 10),
            #},
            multi='sums', help="The total amount."),

        'vr_a_faturar': fields.function(_amount_all, digits=(18, 2), string=u'Valor a faturar', store=False, multi='sums'),

        'sale_order_original_id': fields.many2one('sale.order', u'Pedido original'),
        'desconto_a_autorizar': fields.boolean(u'Desconto a autorizar?'),
        'desconto_autorizado': fields.boolean(u'Desconto autorizado?'),
        'al_desconto_rateio': fields.float(u'Percentual de desconto', digits=(21, 11)),
        'al_desconto_rateio_servicos': fields.float(u'Percentual de desconto', digits=(21, 11)),
        'al_desconto_rateio_mensalidades': fields.float(u'Percentual de desconto', digits=(21, 11)),

        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),
        'write_date': fields.datetime( u'Data Alteração'),

        'date_order_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De data'),
        'date_order_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A data'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c),
        'operacao_fiscal_produto_id': lambda s, cr, uid, c: s.pool.get('res.company').browse(cr, uid, s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c)).operacao_id.id,
        'operacao_fiscal_servico_id': lambda s, cr, uid, c: s.pool.get('res.company').browse(cr, uid, s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=c)).operacao_servico_id.id,
    }

    def onchange_cliente_id(self, cr, uid, ids, partner_id, company_id, context={}):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id or not company_id:
            return res

        valores = res['value']

        partner_obj = self.pool.get('res.partner').browse(cr, 1, partner_id)
        company_obj = self.pool.get('res.company').browse(cr, 1, company_id)

        if partner_obj.operacao_fiscal_produto_id:
            valores['operacao_fiscal_produto_id'] = partner_obj.operacao_fiscal_produto_id.id
        elif company_obj.operacao_id:
            valores['operacao_fiscal_produto_id'] = company_obj.operacao_id.id

        if partner_obj.operacao_fiscal_servico_id:
            valores['operacao_fiscal_servico_id'] = partner_obj.operacao_fiscal_servico_id.id
        elif company_obj.operacao_servico_id:
            valores['operacao_fiscal_servico_id'] = company_obj.operacao_servico_id.id

        if partner_obj.finan_formapagamento_id:
            valores['finan_formapagamento_id'] = partner_obj.finan_formapagamento_id.id

        if partner_obj.transportadora_id:
            valores['transportadora_id'] = partner_obj.transportadora_id.id

        return res

    def _gera_itens_nota(self, cr, uid, nota_obj, pedido_item_ids, contexto_item, temporario=False):
        pedido_item_pool = self.pool.get('sale.order.line')
        documento_item_pool = self.pool.get('sped.documentoitem')

        #
        # Módulo de simulação de pedidos está instalado?
        #
        modulo_simulacao_instalado = len(self.pool.get('ir.module.module').search(cr, 1, [('name','=','sped_sale_simulacao')])) == 1

        vr_total_rateio_desconto = D(0)
        for pedido_item_obj in self.pool.get('sale.order.line').browse(cr, uid, pedido_item_ids):
            vr_total_rateio_desconto += D(pedido_item_obj.vr_total_venda_impostos)
        vr_total_rateio_desconto = vr_total_rateio_desconto.quantize(D('0.01'))

        #
        # Adiciona os produtos
        #
        for pedido_item_obj in self.pool.get('sale.order.line').browse(cr, uid, pedido_item_ids):
                vr_desconto = D(0)
                if pedido_item_obj.order_id.vr_desconto_rateio > 0:
                    vr_desconto_rateio = D(pedido_item_obj.order_id.vr_desconto_rateio)
                    vr_desconto_rateio *= D(pedido_item_obj.vr_total_venda_impostos)
                    vr_desconto_rateio /= vr_total_rateio_desconto
                    vr_desconto = vr_desconto_rateio
                    vr_desconto = vr_desconto.quantize(D('0.01'))

                print('ponto 1')

                if temporario and pedido_item_obj.valor_divergente:
                    pedido_item_pool.write(cr, uid, [pedido_item_obj.id], {'vr_total_venda_impostos': D(pedido_item_obj.vr_unitario_venda_impostos) * D(pedido_item_obj.product_uom_qty), 'vr_desconto': vr_desconto})
                    continue

                print('ponto 2')
            #try:
                produto_obj = pedido_item_obj.product_id

                if temporario:
                    print('ponto 3')
                    dados = {
                        'documento_id': nota_obj,
                        'produto_id': produto_obj.id,
                        'quantidade': pedido_item_obj.product_uom_qty,
                        'quantidade_tributacao': pedido_item_obj.product_uom_qty,
                        'modelo': nota_obj.modelo,
                        'vr_produtos': D(0),
                        'vr_produtos_tributacao': D(0),
                        'vr_operacao': D(0),
                        'vr_operacao_tributacao': D(0),
                        'bc_previdencia': D(0),
                        'vr_previdencia': D(0),
                        'vr_desconto': vr_desconto
                    }

                else:
                    print('ponto 4')
                    dados = {
                        'documento_id': nota_obj.id,
                        'produto_id': produto_obj.id,
                        'quantidade': pedido_item_obj.product_uom_qty,
                        'quantidade_tributacao': pedido_item_obj.product_uom_qty,
                        'modelo': nota_obj.modelo,
                        #'vr_desconto': vr_desconto,
                    }

                #
                # Ajusta a quantidade selecionada na lista de separação aprovada
                #
                if 'stock_picking_id' in contexto_item and contexto_item['stock_picking_id']:
                    print('ponto 5')
                    sql = '''
                    select
                        m.id,
                        m.location_id,
                        m.location_dest_id,
                        m.product_qty
                    from
                        stock_move m
                    where
                        m.picking_id = {stock_picking_id}
                        and m.product_id = {product_id}
                        and m.sped_documentoitem_id is null
                        and m.state = 'done';
                    '''
                    sql = sql.format(stock_picking_id=contexto_item['stock_picking_id'], product_id=pedido_item_obj.product_id.id)
                    cr.execute(sql)
                    qtd_separada = cr.fetchall()
                    #print(sql)
                    #print(qtd_separada)
                    #print(pedido_item_obj.product_id.name)

                    #
                    # Esse item consta?
                    #
                    if not len(qtd_separada):
                        continue

                    dados['stock_move_id'] = qtd_separada[0][0]
                    dados['stock_location_id'] = qtd_separada[0][1]
                    dados['stock_location_dest_id'] = qtd_separada[0][2]
                    dados['quantidade'] = qtd_separada[0][3]
                    dados['quantidade_tributacao'] = qtd_separada[0][3]

                #
                # Não é mais simulação?
                #
                if not temporario:
                    print('ponto 6')
                    if hasattr(pedido_item_obj, 'vr_total_venda_impostos'):
                        print('ponto 7')
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_venda_impostos / pedido_item_obj.product_uom_qty
                    elif getattr(pedido_item_obj, 'usa_unitario_minimo', False):
                        print('ponto 8')
                        pedido_item_obj.price_unit = pedido_item_obj.vr_unitario_minimo
                    elif hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                        print('ponto 9')
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_margem_desconto / pedido_item_obj.product_uom_qty

                else:
                    #
                    # É simulação
                    #
                    if getattr(pedido_item_obj, 'usa_unitario_minimo', False):
                        print('ponto 10')
                        pedido_item_obj.price_unit = pedido_item_obj.vr_unitario_minimo
                    elif hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                        print('ponto 11')
                        pedido_item_obj.price_unit = pedido_item_obj.vr_total_margem_desconto / pedido_item_obj.product_uom_qty

                if modulo_simulacao_instalado and hasattr(pedido_item_obj, 'margem_fixa'):
                    if pedido_item_obj.margem_fixa:
                        pedido_item_obj.price_unit *= D(1) + (D(pedido_item_obj.margem_fixa or 0) / D(100))
                        pedido_item_obj.price_unit = D(pedido_item_obj.price_unit).quantize(D('0.01'))

                taxa = D(0)
                meses = D(0)
                #if temporario and pedido_item_obj.order_id.payment_term and pedido_item_obj.order_id.payment_term.taxa_juros:
                    #print('ponto 12')
                    #taxa = D(pedido_item_obj.order_id.payment_term.taxa_juros) / D(100)

                    #if pedido_item_obj.order_id.payment_term.tipo_taxa == '1':
                        #print('ponto 13')
                        #taxa = D(pedido_item_obj.order_id.payment_term.taxa_juros) / D(12)

                    #print('ponto 14')
                    #meses = D(len(pedido_item_obj.order_id.payment_term.line_ids))

                    ##
                    ## formula juros compostos
                    ##
                    #pedido_item_obj.price_unit = D(pedido_item_obj.price_unit) * ((D(1.0) + taxa) ** meses)

                dados['vr_taxa_juros'] = D(taxa)
                dados['vr_unitario'] = pedido_item_obj.price_unit
                dados['vr_unitario_tributacao'] = pedido_item_obj.price_unit

                if temporario:
                    print('ponto 15')
                    item_obj = DicionarioBrasil()
                    item_obj.update(documento_item_pool._defaults)
                    item_obj.update(contexto_item)
                    item_obj.update(dados)
                    item_obj['uf_partilha_id'] = False
                    item_obj['vr_ibpt'] = D(0)

                    for chave in item_obj:
                        if 'default_' in chave and chave.replace('default_', '') not in item_obj:
                            item_obj[chave.replace('default_')] = item_obj[chave]

                else:
                    print('ponto 16')
                    item_id = documento_item_pool.create(cr, uid, dados, context=contexto_item)
                    item_obj = documento_item_pool.browse(cr, uid, item_id)

                print('ponto 17')
                dados_item = documento_item_pool.onchange_produto(cr, uid, False, produto_obj.id, context=contexto_item)
                print('ponto 18')

                if not 'value' in dados_item:
                    print('ponto 19')
                    raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % produto_obj.name)

                if temporario:
                    print('ponto 20', dados_item['value'])
                    item_obj.update(dados_item['value'])
                else:
                    print('ponto 21')
                    #
                    # Ajusta o lancamento de estoque baseado na lista de separação aprovada
                    #
                    if 'stock_picking_id' in contexto_item and contexto_item['stock_picking_id']:
                        print('ponto 22')
                        sql = '''
                        select id, location_id, location_dest_id
                        from stock_move m
                        where
                            m.picking_id = {stock_picking_id}
                            and m.product_id = {product_id};
                        '''
                        cr.execute(sql.format(stock_picking_id=contexto_item['stock_picking_id'], product_id=pedido_item_obj.product_id.id))
                        qtd_separada = cr.fetchall()
                        dados_item['stock_move_id'] = qtd_separada[0][0]
                        dados_item['stock_location_id'] = qtd_separada[0][1]
                        dados_item['stock_location_dest_id'] = qtd_separada[0][1]

                    print('ponto 23')
                    item_obj.write(dados_item['value'])
                    print('ponto 24')

                    #
                    # Ajusta o lancamento de estoque baseado na lista de separação aprovada
                    #
                    if 'stock_picking_id' in contexto_item and contexto_item['stock_picking_id']:
                        print('ponto 25')
                        sql = '''
                        update stock_move set sped_documentoitem_id = {nfitem_id}
                        where
                            id = {move_id};
                        '''
                        cr.execute(sql.format(move_id=dados_item['stock_move_id'], nfitem_id=item_obj.id))

                print('ponto 26')
                dados_item = documento_item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                print('ponto 27')

                if temporario:
                    print('ponto 28')
                    item_obj.update(dados_item['value'])

                else:
                    print('ponto 29')
                    item_obj.write(dados_item['value'])

                vr_irrf = D('0')
                vr_csll = D('0')
                if contexto_item.get('ajusta_valor_venda', False) and temporario and (not pedido_item_obj.valor_divergente) and (not getattr(pedido_item_obj, 'ignora_impostos', False)):
                    #
                    # Abrir configuração na empresa para definir a presunção de lucro
                    #  há casos de faturamento anual inferior a 120.000,00 no ano
                    #  em que a presunção de lucro dos serviços cai a 16%, só pra IRPF
                    #  pra CSLL é sempre 32% mesmo
                    #
                    # Cálculo do IRPJ e CSLL para lucro presumido:
                    #
                    # Para produtos, presunção de lucro de 8%
                    # Para serviços, presunção de lucro de 32%
                    #
                    # alíquota do IRPJ:
                    #     para lucro abaixo de 20.000 (faturamento * 8%) no mês corrente: 15%
                    #     para lucro acima ou igual a 20.000 (faturamento * 8%) no mês corrente: 25%
                    #     no caso de serviços, o lucro seria faturamento * 32%
                    #
                    # Para CSLL:
                    #   para produtos, presunção de lucro de 12%
                    #   para serviços, presunção de lucro de 32%
                    # alíquota da CSLL: 9%, para produto ou serviço
                    #
                    total_impostos = dados_item['value']['vr_icms_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_ipi'] or D('0')
                    total_impostos += dados_item['value']['vr_pis_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_cofins_proprio'] or D('0')
                    total_impostos += dados_item['value']['vr_iss'] or D('0')
                    total_impostos += dados_item['value']['vr_simples'] or D('0')
                    total_impostos += dados_item['value']['vr_diferencial_aliquota'] or D('0')

                    if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
                    #if nota_obj.company_id.al_pis_cofins_id.al_pis == 0.65:
                        lucro_servico = D('0')
                        lucro_produto = D('0')

                        if produto_obj.type == 'service':
                            lucro_servico = dados_item['value']['vr_nf'] or D('0')
                            lucro_servico *= D('32') / D('100')

                        else:
                            lucro_produto = dados_item['value']['vr_nf'] or D('0')
                            lucro_produto *= D('8') / D('100')

                        vr_irrf = lucro_produto * D('25') / D('100')
                        vr_irrf += lucro_servico * D('25') / D('100')
                        vr_irrf = vr_irrf.quantize(D('0.01'))
                        total_impostos += vr_irrf

                        if produto_obj.type == 'service':
                            lucro_servico = dados_item['value']['vr_nf'] or D('0')
                            lucro_servico *= D('32') / D('100')

                        else:
                            lucro_produto = dados_item['value']['vr_nf'] or D('0')
                            lucro_produto *= D('12') / D('100')

                        vr_csll = lucro_produto * D('9') / D('100')
                        vr_csll += lucro_servico * D('9') / D('100')
                        vr_csll = vr_csll.quantize(D('0.01'))
                        total_impostos += vr_csll

                    ###
                    ### Faz uma prévia para o lucro real
                    ###
                    ##if nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL:
                        ##preco_final_provisorio = D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty)
                        ##lucro_produto = preco_final_provisorio - D(pedido_item_obj.vr_total_custo or 0)

                        ###
                        ### 15% de IR e 9% CSLL
                        ###
                        ##vr_irrf = lucro_produto * D('15') / D('100')
                        ##vr_irrf = vr_irrf.quantize(D('0.01'))
                        ##total_impostos += vr_irrf

                        ##vr_csll = lucro_produto * D('9') / D('100')
                        ##vr_csll = vr_csll.quantize(D('0.01'))
                        ##total_impostos += vr_csll

                    #if hasattr(pedido_item_obj, 'vr_total_margem_desconto'):
                    #    if pedido_item_obj.vr_total_margem_desconto:
                    #        proporcao_impostos = total_impostos / D(pedido_item_obj.vr_total_margem_desconto)
                    #    else:
                    #        proporcao_impostos = D(0)
                    #elif pedido_item_obj.price_subtotal:

                    if not getattr(pedido_item_obj.order_id.pricelist_obj, 'ignora_impostos', False):
                        try:
                            proporcao_impostos = total_impostos / (D(pedido_item_obj.price_unit) * D(pedido_item_obj.product_uom_qty))
                        except:
                            proporcao_impostos = D(0)
                    else:
                        proporcao_impostos = D(0)

                    print('irrf', vr_irrf, 'csll', vr_csll)

                    price_unit = D(pedido_item_obj.price_unit) / (D(1) - proporcao_impostos)
                    price_unit = price_unit.quantize(D('0.01'))
                    dados_item['value']['vr_irrf'] = vr_irrf
                    dados_item['value']['vr_csll'] = vr_csll
                    dados_item['value']['vr_unitario_venda_impostos'] = price_unit
                    dados_item['value']['porcentagem_imposto'] = proporcao_impostos * D(100)
                    dados_item['value']['proporcao_imposto'] = (D(1) - proporcao_impostos) * D(100)
                    dados_item['value']['vr_total_venda_impostos'] = price_unit * D(pedido_item_obj.product_uom_qty)
                    dados_item['value']['falha_configuracao'] = False
                    dados_item['value']['total_imposto'] = total_impostos

                    #
                    # Agora, injeta a proporção dos impostos nos próprios impostos já calculados
                    #
                    dados_item['value']['vr_icms_proprio'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_icms_st'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_icms_sn'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_pis_proprio'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_cofins_proprio'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_irrf'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['vr_csll'] /= (D(1) - proporcao_impostos)
                    dados_item['value']['total_imposto'] /= (D(1) - proporcao_impostos)

                    #print('atualiza nota', price_unit, price_unit * D(pedido_item_obj.product_uom_qty), pedido_item_obj.product_id.name_template, proporcao_impostos)

                #pedido_item_pool.write(cr, uid, [pedido_item_obj.id], dados_item['value'], context={'calculo_resumo': True})
                pedido_item_pool.write(cr, uid, [pedido_item_obj.id], dados_item['value'])
                #pedido_item_obj.write(dados_item['value'], context={'calculo_resumo': True})
                nota_obj.vr_icms_proprio = D(nota_obj.vr_icms_proprio or 0) + D(dados_item['value']['vr_icms_proprio'] or 0)
                nota_obj.vr_ipi = D(nota_obj.vr_ipi or 0) + D(dados_item['value']['vr_ipi'] or 0)
                nota_obj.vr_pis_proprio = D(nota_obj.vr_pis_proprio or 0) + D(dados_item['value']['vr_pis_proprio'] or 0)
                nota_obj.vr_cofins_proprio = D(nota_obj.vr_cofins_proprio or 0) + D(dados_item['value']['vr_cofins_proprio'] or 0)
                nota_obj.vr_iss = D(nota_obj.vr_iss or 0) + D(dados_item['value']['vr_iss'] or 0)
                #nota_obj.vr_irrf = D(nota_obj.vr_irrf or 0) + D(vr_irrf or 0)
                #nota_obj.vr_csll = D(nota_obj.vr_csll or 0) + D(vr_csll or 0)

            #except Exception as e:
                #if e.message:
                    #mensagem = e.message
                #elif len(e.args) > 1:
                    #mensagem = e.args[1]
                #else:
                    #mensagem = unicode(e)

                #print(mensagem)
                #pedido_item_obj.write({'falha_configuracao': mensagem})

    def gera_notas(self, cr, uid, ids, context={}):
        res = {}
        documento_pool = self.pool.get('sped.documento')
        item_pool = self.pool.get('sale.order.line')

        temporario = context.get('temporario', False)
        notas_1_N_pedidos = context.get('notas_1_N_pedidos', False)
        nota_produto_obj = context.get('nota_produto_obj', None)
        nota_servico_obj = context.get('nota_produto_obj', None)
        stock_picking_id = context.get('stock_picking_id', False)
        soh_servicos = context.get('soh_servicos', False)
        seguranca = context.get('seguranca', False)

        print('seguranca', seguranca)
        print('soh_servicos', soh_servicos)

        if not temporario:
            ajusta_valor_venda = False
        else:
            ajusta_valor_venda = context.get('ajusta_valor_venda', False)


        for pedido_obj in self.browse(cr, uid, ids):
            #
            # Verifica se tem produtos para a nota de produtos, e serviços
            # para a nota de serviços
            #
            if seguranca:
                if soh_servicos:
                    produto_ids = []

                else:
                    produto_ids = item_pool.search(cr, uid, [('order_id', '=', pedido_obj.id), ('tipo_item', '=', 'P'), ('cobrar', '=', True)])

                servico_ids = item_pool.search(cr, uid, [('order_id', '=', pedido_obj.id), ('tipo_item', '=', 'S'), ('cobrar', '=', True)])

            else:
                produto_ids = item_pool.search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '!=', 'service')])
                servico_ids = item_pool.search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '=', 'service')])

            print('pedido_id', pedido_obj.id)
            print('context', context)
            print('produto_ids', produto_ids)
            print('servico_ids', servico_ids)

            if produto_ids and not pedido_obj.operacao_fiscal_produto_id:
                break
                #raise osv.except_osv(u'Inválido!', u'Não foi informada nenhuma operação fiscal para o faturamento dos produtos!')

            if servico_ids and not pedido_obj.operacao_fiscal_servico_id:
                break
                #raise osv.except_osv(u'Inválido!', u'Não foi informada nenhuma operação fiscal para o faturamento dos serviços!')

            impostos = {
                'vr_icms_proprio': D('0'),
                #'vr_icms_st': D('0'),
                'vr_ipi': D('0'),
                #'vr_ii': D('0'),
                'vr_pis_proprio': D('0'),
                'vr_cofins_proprio': D('0'),
                'vr_iss': D('0'),
                #'vr_pis_retido': D('0'),
                #'vr_cofins_retido': D('0'),
                'vr_csll': D('0'),
                'vr_irrf': D('0'),
                #'vr_previdencia': D('0'),
                'total_imposto': D('0'),
            }
            total_nf_produto = D('0')
            total_nf_servico = D('0')


            if produto_ids and pedido_obj.operacao_fiscal_produto_id and (not soh_servicos):
                operacao_obj = pedido_obj.operacao_fiscal_produto_id

                if temporario:
                    dados = copy(documento_pool._defaults)
                    dados.update({
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                        'modelo': operacao_obj.modelo,
                    })

                    for chave in dados:
                        if hasattr(dados[chave], '__call__'):
                            dados[chave] = dados[chave](documento_pool, cr, uid, {'modelo': operacao_obj.modelo, 'default_modelo': operacao_obj.modelo, 'temporario': temporario})

                else:
                    dados = {
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                        #'municipio_fato_gerador_id': municipio_id,
                        #'finan_contrato_id': contrato_obj.id,
                        #'finan_lancamento_id': lancamento_obj.id,
                        'sale_order_ids': [(6, 0, [pedido_obj.id])],
                    }

                #
                # Gera o registro da NF-e
                #
                if temporario:
                    nota_obj = DicionarioBrasil()
                    nota_obj.update(dados)
                    dados_operacao = documento_pool.onchange_operacao(cr, uid, False, operacao_obj.id)
                    nota_obj.update(dados_operacao['value'])

                else:
                    nota_id = documento_pool.create(cr, uid, dados, context={'modelo': operacao_obj.modelo, 'default_modelo': operacao_obj.modelo, 'temporario': temporario})

                    if stock_picking_id:
                        sql = '''
                        update stock_picking set sped_documento_id = {nf_id}
                        where id = {separa_id};
                        '''
                        cr.execute(sql.format(nf_id=nota_id, separa_id=stock_picking_id))

                    nota_obj = documento_pool.browse(cr, uid, nota_id)
                    dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)
                    nota_obj.write(dados_operacao['value'])


                contexto_item = copy(dados)
                contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
                for chave in dados:
                    if 'default_' not in chave:
                        contexto_item['default_' + chave] = contexto_item[chave]

                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao
                contexto_item['stock_picking_id'] = stock_picking_id

                self._gera_itens_nota(cr, uid, nota_obj, produto_ids, contexto_item, temporario)

                if not temporario:
                    nota_obj.ajusta_impostos_retidos()
                    nota_obj.write({'numero': nota_obj.numero - 1})
                    nota_obj.write({'numero': nota_obj.numero})
                    nota_obj = documento_pool.browse(cr, uid, nota_obj.id)

                impostos['vr_icms_proprio'] += D(str(nota_obj.vr_icms_proprio))
                #impostos['vr_icms_st'] += D(str(nota_obj.vr_icms_st))
                impostos['vr_ipi'] += D(str(nota_obj.vr_ipi))
                #impostos['vr_ii'] += D(str(nota_obj.vr_ii))
                impostos['vr_pis_proprio'] += D(str(nota_obj.vr_pis_proprio))
                impostos['vr_cofins_proprio'] += D(str(nota_obj.vr_cofins_proprio))
                impostos['vr_iss'] += D(str(nota_obj.vr_iss))
                #impostos['vr_pis_retido'] += D(str(nota_obj.vr_pis_retido))
                #impostos['vr_cofins_retido'] += D(str(nota_obj.vr_cofins_retido))
                #impostos['vr_csll'] += D(str(nota_obj.vr_csll))
                #impostos['vr_irrf'] += D(str(nota_obj.vr_irrf))
                #impostos['vr_previdencia'] += D(str(nota_obj.vr_previdencia))
                #impostos['vr_iss_retido'] += D(str(nota_obj.vr_iss_retido))
                total_nf_produto = D(str(nota_obj.vr_nf))

                if not temporario:

                    #
                    # Ajusta o transporte
                    #
                    if pedido_obj.modalidade_frete:
                        nota_obj.write({'modalidade_frete': pedido_obj.modalidade_frete})

                    if pedido_obj.transportadora_id:
                        nota_obj.write({'transportadora_id': pedido_obj.transportadora_id.id})

                    #
                    # Ajusta a forma de pagamento
                    #
                    if pedido_obj.finan_formapagamento_id:
                        nota_obj.write({'finan_formapagamento_id': pedido_obj.finan_formapagamento_id.id})
                    #
                    # Ajusta a condição de pagamento e as duplicatas
                    #
                    print('vai gerar parcelas', seguranca)
                    if seguranca:
                        if len(servico_ids) == 0:
                            porcentagem_produto = 1
                        else:
                            porcentagem_produto = D(pedido_obj.vr_total_produtos).quantize(D('0.01')) / D(pedido_obj.amount_total).quantize(D('0.01'))

                        parcelas = self.pool.get('sale.order').browse(cr, 1, pedido_obj.id)
                        print('porcentagem', porcentagem_produto, parcelas.simulacao_parcelas_ids)

                        for parcela_obj in parcelas.simulacao_parcelas_ids:
                            dup = {
                                'documento_id': nota_obj.id,
                                'numero': parcela_obj.numero,
                                'data_vencimento': parcela_obj.data,
                            }

                            valor = D(parcela_obj.valor) * porcentagem_produto
                            dup['valor'] = valor.quantize(D('0.01'))

                            self.pool.get('sped.documentoduplicata').create(cr, uid, dup)

                        nota_obj.botao_regera_duplicatas()

                    else:
                        cond_pag_obj = None
                        #print(pedido_obj.payment_term, 'condicao de pagamento do pedido')
                        if pedido_obj.payment_term:
                            cond_pag_obj = pedido_obj.payment_term
                            nota_obj.write({'payment_term_id': cond_pag_obj.id})

                        elif operacao_obj.payment_term_id:
                            cond_pag_obj = operacao_obj.payment_term_id

                        #print(cond_pag_obj, 'condicao de pagamento')

                        if cond_pag_obj:
                            dados = nota_obj.onchange_payment_term(cond_pag_obj.id, nota_obj.vr_fatura, nota_obj.vr_nf, nota_obj.data_emissao, [], context={'sale_obj': pedido_obj})
                            nota_obj.write(dados['value'])

                #lancamento_obj.write({'sped_documento_id': nota_obj.id, 'valor_documento': nota_obj.vr_fatura, 'provisionado': False})

            #
            # Quando há o faturamento direto da mão de obra, não há emissão de NFS-e somente dos itens de mão-de-obra
            #
            if hasattr(pedido_obj, 'mao_de_obra_instalacao_faturamento_direto') and pedido_obj.mao_de_obra_instalacao_faturamento_direto:
                servico_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', pedido_obj.id), ('product_id.type', '=', 'service'), ('orcamento_categoria_id', '!=', 6)])
                #servico_ids = False

            if servico_ids and pedido_obj.operacao_fiscal_servico_id:
                operacao_obj = pedido_obj.operacao_fiscal_servico_id

                if temporario:
                    dados = copy(documento_pool._defaults)
                    dados.update({
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                    })

                    for chave in dados:
                        if hasattr(dados[chave], '__call__'):
                            dados[chave] = dados[chave](documento_pool, cr, uid, {'modelo': operacao_obj.modelo, 'default_modelo': operacao_obj.modelo, 'temporario': temporario})
                else:
                    dados = {
                        'company_id': pedido_obj.company_id.id,
                        'partner_id': pedido_obj.partner_id.id,
                        'operacao_id': operacao_obj.id,
                        #'municipio_fato_gerador_id': municipio_id,
                        #'finan_contrato_id': contrato_obj.id,
                        #'finan_lancamento_id': lancamento_obj.id,
                        'sale_order_ids': [(6, 0, [pedido_obj.id])],
                    }

                if pedido_obj.company_id.company_servico_id:
                    dados['company_id'] = pedido_obj.company_id.company_servico_id.id
                    dados['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                #
                # Gera o registro da NF-e
                #
                if temporario:
                    nota_obj = DicionarioBrasil()
                    nota_obj.update(dados)
                    dados_operacao = documento_pool.onchange_operacao(cr, uid, False, operacao_obj.id)

                    if pedido_obj.company_id.company_servico_id:
                        #
                        # Resgata o regime tributário da empresa
                        #
                        dados_operacao['value']['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                    nota_obj.update(dados_operacao['value'])


                else:
                    nota_id = documento_pool.create(cr, uid, dados, context={'modelo': operacao_obj.modelo, 'default_modelo': operacao_obj.modelo})
                    nota_obj = documento_pool.browse(cr, uid, nota_id)
                    dados_operacao = nota_obj.onchange_operacao(operacao_obj.id)

                    if pedido_obj.company_id.company_servico_id:
                        #
                        # Resgata o regime tributário da empresa
                        #
                        dados_operacao['value']['regime_tributario'] = pedido_obj.company_id.company_servico_id.regime_tributario

                    nota_obj.write(dados_operacao['value'])

                contexto_item = copy(dados)
                contexto_item['ajusta_valor_venda'] = ajusta_valor_venda
                for chave in dados:
                    if 'default_' not in chave:
                        contexto_item['default_' + chave] = contexto_item[chave]

                contexto_item['entrada_saida'] = nota_obj.entrada_saida
                contexto_item['regime_tributario'] = nota_obj.regime_tributario
                contexto_item['emissao'] = nota_obj.emissao
                contexto_item['data_emissao'] = nota_obj.data_emissao
                contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
                contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
                contexto_item['default_emissao'] = nota_obj.emissao
                contexto_item['default_data_emissao'] = nota_obj.data_emissao

                print('vai gerar itens de serviço', servico_ids)
                self._gera_itens_nota(cr, uid, nota_obj, servico_ids, contexto_item, temporario)

                if not temporario:
                    nota_obj.ajusta_impostos_retidos()
                    nota_obj.write({'numero': nota_obj.numero - 1})
                    nota_obj.write({'numero': nota_obj.numero})
                    nota_obj = documento_pool.browse(cr, uid, nota_obj.id)

                impostos['vr_icms_proprio'] += D(str(nota_obj.vr_icms_proprio))
                #impostos['vr_icms_st'] += D(str(nota_obj.vr_icms_st))
                impostos['vr_ipi'] += D(str(nota_obj.vr_ipi))
                #impostos['vr_ii'] += D(str(nota_obj.vr_ii))
                impostos['vr_pis_proprio'] += D(str(nota_obj.vr_pis_proprio))
                impostos['vr_cofins_proprio'] += D(str(nota_obj.vr_cofins_proprio))
                impostos['vr_iss'] += D(str(nota_obj.vr_iss))
                #impostos['vr_pis_retido'] += D(str(nota_obj.vr_pis_retido))
                #impostos['vr_cofins_retido'] += D(str(nota_obj.vr_cofins_retido))
                #impostos['vr_csll'] += D(str(nota_obj.vr_csll))
                #impostos['vr_irrf'] += D(str(nota_obj.vr_irrf))
                #impostos['vr_previdencia'] += D(str(nota_obj.vr_previdencia))
                #impostos['vr_iss_retido'] += D(str(nota_obj.vr_iss_retido))
                total_nf_servico = D(str(nota_obj.vr_nf))

                #
                #
                #
                if not temporario:
                    #
                    # Ajusta a forma de pagamento
                    #
                    if pedido_obj.finan_formapagamento_id:
                        nota_obj.write({'finan_formapagamento_id': pedido_obj.finan_formapagamento_id.id})
                    #
                    # Ajusta a condição de pagamento e as duplicatas
                    #
                    if seguranca:
                        if soh_servicos or len(produto_ids) == 0:
                            porcentagem_produto = D(1)

                        else:
                            porcentagem_produto = D(pedido_obj.vr_total_servicos).quantize(D('0.01')) / D(pedido_obj.amount_total).quantize(D('0.01'))

                        parcelas = self.pool.get('sale.order').browse(cr, 1, pedido_obj.id)
                        print('porcentagem', porcentagem_produto, parcelas.simulacao_parcelas_ids)

                        for parcela_obj in parcelas.simulacao_parcelas_ids:
                            dup = {
                                'documento_id': nota_obj.id,
                                'numero': parcela_obj.numero,
                                'data_vencimento': parcela_obj.data,
                            }

                            valor = D(parcela_obj.valor) * porcentagem_produto
                            dup['valor'] = valor.quantize(D('0.01'))

                            self.pool.get('sped.documentoduplicata').create(cr, uid, dup)

                        nota_obj.botao_regera_duplicatas()

                    else:
                        cond_pag_obj = None
                        #print(pedido_obj.payment_term, 'condicao de pagamento do pedido')
                        if pedido_obj.payment_term:
                            cond_pag_obj = pedido_obj.payment_term
                            nota_obj.write({'payment_term_id': cond_pag_obj.id})

                        elif operacao_obj.payment_term_id:
                            cond_pag_obj = operacao_obj.payment_term_id

                        #print(cond_pag_obj, 'condicao de pagamento')

                        if cond_pag_obj:
                            dados = nota_obj.onchange_payment_term(cond_pag_obj.id, nota_obj.vr_fatura, nota_obj.vr_nf, nota_obj.data_emissao, [], context={'sale_obj': pedido_obj})
                            nota_obj.write(dados['value'])

                #lancamento_obj.write({'sped_documento_id': nota_obj.id, 'valor_documento': nota_obj.vr_fatura, 'provisionado': False})


            total_imposto = D('0')
            total_imposto += impostos['vr_icms_proprio']
            #total_imposto += impostos['vr_icms_st']
            total_imposto += impostos['vr_ipi']
            #total_imposto += impostos['vr_ii']
            total_imposto += impostos['vr_pis_proprio']
            total_imposto += impostos['vr_cofins_proprio']
            total_imposto += impostos['vr_iss']

            #
            # Abrir configuração na empresa para definir a presunção de lucro
            #  há casos de faturamento anual inferior a 120.000,00 no ano
            #  em que a presunção de lucro dos serviços cai a 16%, só pra IRPF
            #  pra CSLL é sempre 32% mesmo
            #
            # Cálculo do IRPJ e CSLL para lucro presumido:
            #
            # Para produtos, presunção de lucro de 8%
            # Para serviços, presunção de lucro de 32%
            #
            # alíquota do IRPJ:
            #     para lucro abaixo de 20.000 (faturamento * 8%) no mês corrente: 15%
            #     para lucro acima ou igual a 20.000 (faturamento * 8%) no mês corrente: 25%
            #     no caso de serviços, o lucro seria faturamento * 32%
            #
            # Para CSLL:
            #   para produtos, presunção de lucro de 12%
            #   para serviços, presunção de lucro de 32%
            # alíquota da CSLL: 9%, para produto ou serviço
            #
            if pedido_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
            #if pedido_obj.company_id.al_pis_cofins_id.al_pis == 0.65:
                lucro_produto = total_nf_produto * D('8') / D('100')
                lucro_servico = total_nf_servico * D('32') / D('100')
                impostos['vr_irrf'] = lucro_produto * D('25') / D('100')
                impostos['vr_irrf'] += lucro_servico * D('25') / D('100')
                total_imposto += impostos['vr_irrf']

                lucro_produto = total_nf_produto * D('12') / D('100')
                lucro_servico = total_nf_servico * D('32') / D('100')
                impostos['vr_csll'] = lucro_produto * D('9') / D('100')
                impostos['vr_csll'] += lucro_servico * D('9') / D('100')
                total_imposto += impostos['vr_csll']

            #elif nota_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
                #lucro_produto =

            #total_imposto += impostos['vr_previdencia']
            impostos['total_imposto'] = total_imposto

            if hasattr(pedido_obj, 'vr_total_margem_desconto'):
                valor_liquido = D(str(pedido_obj.vr_total_margem_desconto))
            else:
                valor_liquido = D(pedido_obj.amount_total)

            if hasattr(pedido_obj, 'vr_total_custo'):
                valor_liquido -= D(str(pedido_obj.vr_total_custo))

            valor_liquido -= total_imposto

            if hasattr(pedido_obj, 'vr_comissao'):
                valor_liquido -= D(str(pedido_obj.vr_comissao))

            impostos['vr_liquido'] = valor_liquido
            try:
                if hasattr(pedido_obj, 'vr_total_margem_desconto'):
                    impostos['margem_liquida'] = valor_liquido / D(str(pedido_obj.vr_total_margem_desconto)) * 100
                else:
                    impostos['margem_liquida'] = valor_liquido / D(pedido_obj.amount_total) * 100

            except:
                impostos['margem_liquida'] = 0

            pedido_obj.write(impostos)

        return res

    #def button_dummy(self, cr, uid, ids, context={}):
        #context['temporario'] = True
        #context['ajusta_valor_venda'] = True
        #return self.gera_notas(cr, uid, ids, context)

    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if company_obj.operacao_id:
            valores['operacao_fiscal_produto_id'] = company_obj.operacao_id.id

        valores['operacao_id'] = company_obj.operacao_id.id if company_obj.operacao_id else False
        valores['operacao_pessoa_fisica_id'] = company_obj.operacao_pessoa_fisica_id.id if company_obj.operacao_pessoa_fisica_id else False
        valores['operacao_ativo_id'] = company_obj.operacao_ativo_id.id if company_obj.operacao_ativo_id else False
        valores['operacao_faturamento_antecipado_id'] = company_obj.operacao_faturamento_antecipado_id.id if company_obj.operacao_faturamento_antecipado_id else False

        if company_obj.operacao_servico_id:
            valores['operacao_fiscal_servico_id'] = company_obj.operacao_servico_id.id

        return res

    def imprime_pedido_venda(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        pedido_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'integra_pedido_venda.jrxml')
        recibo = 'pedido_venda_'+ pedido_obj.name + '.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, 1, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'sale.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        #print(dados)

        if 'vr_desconto_rateio' in dados or 'vr_desconto_rateio_servicos' in dados or 'vr_desconto_rateio_mensalidades' in dados:
            self.ajusta_desconto_rateio(cr, uid, ids)

        return res

    def lista_itens_rateio_desconto(self, cr, uid, sale_obj, tipo='P'):
        itens_rateio = []
        vr_total_rateio_desconto = D(0)

        for item_obj in sale_obj.order_line:
            if getattr(item_obj, 'tipo_item', 'P') != tipo:
                continue

            if not getattr(item_obj, 'usa_unitario_minimo', False):
                if item_obj.vr_total_venda_impostos:
                    itens_rateio.append(item_obj)
                    vr_total_rateio_desconto += D(item_obj.vr_total_venda_impostos)

        vr_total_rateio_desconto = vr_total_rateio_desconto.quantize(D('0.01'))

        return itens_rateio, vr_total_rateio_desconto

    def _ajusta_desconto_rateio(self, cr, uid, sale_obj, itens_rateio, vr_total_rateio_desconto, desconto_a_autorizar, tipo='P'):
        if vr_total_rateio_desconto:
            if tipo == 'P':
                al_desconto_rateio = D(sale_obj.vr_desconto_rateio) / D(vr_total_rateio_desconto) * 100
                sale_obj.vr_desconto_rateio = D(sale_obj.vr_desconto_rateio)
            elif tipo == 'S':
                al_desconto_rateio = D(sale_obj.vr_desconto_rateio_servicos) / D(vr_total_rateio_desconto) * 100
                sale_obj.vr_desconto_rateio = D(sale_obj.vr_desconto_rateio_servicos)
            elif tipo == 'M':
                al_desconto_rateio = D(sale_obj.vr_desconto_rateio_mensalidades) / D(vr_total_rateio_desconto) * 100
                sale_obj.vr_desconto_rateio = D(sale_obj.vr_desconto_rateio_mensalidades)
        else:
            al_desconto_rateio = D(0)

        if tipo == 'P':
            cr.execute('update sale_order set al_desconto_rateio = {al_desconto} where id = {id};'.format(al_desconto=al_desconto_rateio, id=sale_obj.id))
        elif tipo == 'S':
            cr.execute('update sale_order set al_desconto_rateio_servicos = {al_desconto} where id = {id};'.format(al_desconto=al_desconto_rateio, id=sale_obj.id))
        elif tipo == 'M':
            cr.execute('update sale_order set al_desconto_rateio_mensalidades = {al_desconto} where id = {id};'.format(al_desconto=al_desconto_rateio, id=sale_obj.id))

        if not sale_obj.desconto_autorizado:
            if getattr(sale_obj.pricelist_id, 'desconto_maximo', False):
                if al_desconto_rateio > sale_obj.pricelist_id.desconto_maximo:
                    desconto_maximo = D(vr_total_rateio_desconto) * D(sale_obj.pricelist_id.desconto_maximo or 0) / 100
                    desconto_a_autorizar = desconto_a_autorizar or True
                    #print('desconto_a_autorizar', desconto_a_autorizar)
                    #raise osv.except_osv(u'Aviso!', u'O desconto está acima do permitido de R$ {valor}, solicite ao gerente a autorização!'.format(valor=formata_valor(desconto_maximo)))

            if desconto_a_autorizar:
                #print('sim, desconto_a_autorizar', desconto_a_autorizar)
                cr.execute('update sale_order set desconto_a_autorizar = True where id = ' + str(sale_obj.id) + ';')
            else:
                #print('nao desconto_a_autorizar', desconto_a_autorizar)
                cr.execute('update sale_order set desconto_a_autorizar = False where id = ' + str(sale_obj.id) + ';')

        i = 0
        vr_desconto_total = D(0)

        #if tipo == 'S':
            #print('desconto sobre servicos', vr_total_rateio_desconto, itens_rateio, sale_obj.vr_desconto_rateio)

        for item_obj in itens_rateio:
            if getattr(item_obj, 'tipo_item', 'P') != tipo:
                continue

            vr_desconto = D(0)

            if sale_obj.vr_desconto_rateio:
                vr_desconto_rateio = D(sale_obj.vr_desconto_rateio)
                vr_desconto_rateio *= D(item_obj.vr_total_venda_impostos)
                vr_desconto_rateio /= vr_total_rateio_desconto
                vr_desconto = vr_desconto_rateio
            else:
                vr_desconto = D(item_obj.vr_desconto or 0)

            vr_desconto = vr_desconto.quantize(D('0.01'))

            #
            # Ajusta os centavos do desconto para a quantidade do item
            #
            item_obj.product_uom_qty = D(item_obj.product_uom_qty or 1).quantize(D('0.01'))
            vr_desconto = vr_desconto / item_obj.product_uom_qty
            vr_desconto = vr_desconto.quantize(D('0.01'))
            vr_desconto *= item_obj.product_uom_qty

            vr_desconto_total += vr_desconto
            i += 1

            #
            # Ajusta os centavos no último item
            #
            if i == len(itens_rateio):
                vr_desconto_rateio = D(sale_obj.vr_desconto_rateio).quantize(D('0.01'))
                #print('vr_desconto', vr_desconto, vr_desconto_rateio, vr_desconto_total)
                vr_desconto -= vr_desconto_total - vr_desconto_rateio
                #print('vr_desconto', vr_desconto, vr_desconto_rateio, vr_desconto_total)

            if not getattr(item_obj.order_id.pricelist_id, 'ignora_impostos', False):
                vr_desconto_venda = vr_desconto * item_obj.proporcao_imposto / D(100)
            else:
                vr_desconto_venda = vr_desconto

            vr_desconto_venda = vr_desconto_venda.quantize(D('0.01'))

            #contexto_novo = copy(context)
            contexto_novo = {}
            contexto_novo['company_id'] = sale_obj.company_id.id
            contexto_novo['partner_id'] = sale_obj.partner_id.id

            contexto_novo['operacao_fiscal_produto_id'] = sale_obj.operacao_fiscal_produto_id.id if sale_obj.operacao_fiscal_produto_id else False
            contexto_novo['operacao_fiscal_servico_id'] = sale_obj.operacao_fiscal_servico_id.id if sale_obj.operacao_fiscal_servico_id else False

            if hasattr(item_obj, 'vr_unitario_venda'):
                vr_total = D(item_obj.vr_unitario_venda or 0).quantize(D('0.01')) * D(item_obj.product_uom_qty or 1).quantize(D('0.01'))
            else:
                vr_total = D(item_obj.price_unit or 0).quantize(D('0.01')) * D(item_obj.product_uom_qty or 1).quantize(D('0.01'))

            vr_total = vr_total.quantize(D('0.01'))

            margem = D(getattr(item_obj, 'margem', 0) or 0)

            if margem:
                margem = vr_total * (margem / D('100.00'))
                margem = margem.quantize(D('0.01'))

            vr_total_margem_desconto = vr_total + margem - vr_desconto_venda
            vr_unitario_margem_desconto = vr_total_margem_desconto / D(item_obj.product_uom_qty or 1).quantize(D('0.01'))
            vr_unitario_margem_desconto = vr_unitario_margem_desconto.quantize(D('0.001'))

            contexto_novo['price_unit'] = vr_unitario_margem_desconto
            contexto_novo['price_unit_original'] = item_obj.price_unit_original
            contexto_novo['vr_unitario_base'] = item_obj.vr_unitario_base
            #contexto_novo['vr_desconto'] = vr_desconto

            impostos = self.pool.get('sale.order.line').product_id_change(cr, uid, [item_obj.id], sale_obj.pricelist_id.id, item_obj.product_id.id, item_obj.product_uom_qty, item_obj.uom_id.id, item_obj.product_uos_qty, False, item_obj.name, sale_obj.partner_id.id, False, False, sale_obj.date_order, False, False, False, contexto_novo)

            impostos['value']['discount'] = vr_desconto
            #impostos['value']['vr_unitario_margem_desconto'] = item_obj.vr_unitario_venda - vr_desconto_venda

            dados = {}
            for chave in impostos['value']:
                if not isinstance(impostos['value'][chave], DicionarioBrasil):
                    dados[chave] = impostos['value'][chave]

            if 'price_unit' in dados:
                del dados['price_unit']

            if 'vr_unitario_venda' in dados:
                del dados['vr_unitario_venda']

            #print(dados)
            self.pool.get('sale.order.line').write(cr, uid, [item_obj.id], dados)

        return desconto_a_autorizar

    def ajusta_desconto_rateio(self, cr, uid, ids):
        for sale_obj in self.browse(cr, uid, ids):
            #
            # Faz o rateio do desconto nos produtos
            #
            desconto_a_autorizar = False
            itens_rateio, vr_total_rateio_desconto = self.lista_itens_rateio_desconto(cr, uid, sale_obj, tipo='P')
            #print('desconto sobre produtos', itens_rateio, vr_total_rateio_desconto)
            #print('antes desconto_a_autorizar', desconto_a_autorizar)
            desconto_a_autorizar = self._ajusta_desconto_rateio(cr, uid, sale_obj, itens_rateio, vr_total_rateio_desconto, desconto_a_autorizar, tipo='P')
            #print('depois desconto_a_autorizar', desconto_a_autorizar)

            #
            # Faz o rateio do desconto nos serviços
            #
            itens_rateio, vr_total_rateio_desconto = self.lista_itens_rateio_desconto(cr, uid, sale_obj, tipo='S')
            #print('desconto sobre servico', itens_rateio, vr_total_rateio_desconto)
            #print('antes desconto_a_autorizar', desconto_a_autorizar)
            desconto_a_autorizar = self._ajusta_desconto_rateio(cr, uid, sale_obj, itens_rateio, vr_total_rateio_desconto, desconto_a_autorizar, tipo='S')
            #print('depois desconto_a_autorizar', desconto_a_autorizar)

            #
            # Faz o rateio do desconto nas mensalidades
            #
            itens_rateio, vr_total_rateio_desconto = self.lista_itens_rateio_desconto(cr, uid, sale_obj, tipo='M')
            desconto_a_autorizar = self._ajusta_desconto_rateio(cr, uid, sale_obj, itens_rateio, vr_total_rateio_desconto, desconto_a_autorizar, tipo='M')

    def onchange_partner_id(self, cr, uid, ids, partner_id, context={}):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id:
            return res

        #
        # Validamos a operação fiscal para pessoa física
        #
        company_pool = self.pool.get('res.company')
        company_id = company_pool._company_default_get(cr, uid, 'sale.order', context=context)
        company_obj = company_pool.browse(cr, uid, company_id)

        cliente_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

        res['value']['tipo_pessoa'] = cliente_obj.tipo_pessoa

        res['value']['operacao_id'] = company_obj.operacao_id.id if company_obj.operacao_id else False
        res['value']['operacao_pessoa_fisica_id'] = False

        if cliente_obj.tipo_pessoa == 'F' and company_obj.operacao_pessoa_fisica_id:
            res['value']['operacao_fiscal_produto_id'] = company_obj.operacao_pessoa_fisica_id.id
            res['value']['operacao_pessoa_fisica_id'] = company_obj.operacao_pessoa_fisica_id.id if company_obj.operacao_pessoa_fisica_id else False
            res['value']['operacao_id'] = False

        res['value']['operacao_ativo_id'] = company_obj.operacao_ativo_id.id if company_obj.operacao_ativo_id else False
        res['value']['operacao_faturamento_antecipado_id'] = company_obj.operacao_faturamento_antecipado_id.id if company_obj.operacao_faturamento_antecipado_id else False

        return res

    def recalcula_fora_validade(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('sale.order.line')

        for pedido_obj in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
            if (not pedido_obj.operacao_fiscal_produto_id):
                raise osv.except_osv(u'Erro!', u'Sem informação da operação fiscal para saída dos produtos!')

            if (not pedido_obj.operacao_fiscal_servico_id):
                raise osv.except_osv(u'Erro!', u'Sem informação da operação fiscal para saída dos serviços!')

            for item_obj in pedido_obj.order_line:
                if getattr(item_obj, 'autoinsert', False):
                    continue

                #
                # Guardamos a quantidade, a margem e o desconto individuais
                #
                quantidade = item_obj.product_uom_qty
                usa_unitario_minimo = getattr(item_obj, 'usa_unitario_minimo', False)
                margem = getattr(item_obj, 'margem', 0)
                desconto = getattr(item_obj, 'discount', 0)
                name = item_obj.name

                contexto_novo = {
                    'company_id': pedido_obj.company_id.id,
                    'operacao_fiscal_produto_id': pedido_obj.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': pedido_obj.operacao_fiscal_servico_id.id,
                }

                if hasattr(pedido_obj, 'orcamento_aprovado'):
                    contexto_novo['orcamento_aprovado'] = pedido_obj.orcamento_aprovado

                dados_produto = item_pool.product_id_change(cr, uid, [item_obj.id], pedido_obj.pricelist_id.id, item_obj.product_id.id, quantidade, partner_id=pedido_obj.partner_id.id, context=contexto_novo, date_order=str(hoje()))

                if 'value' in dados_produto:
                    dados_produto = dados_produto['value']
                    #if item_obj.product_id.id == 1520:
                        #print('dados_produto')
                        #print(dados_produto['price_unit'])
                        #print(dados_produto)
                        #print(dados_produto['price_unit'])
                    dados_produto['product_uom_qty'] = quantidade
                    dados_produto['usa_unitario_minimo'] = usa_unitario_minimo
                    dados_produto['margem'] = 0
                    dados_produto['discount'] = 0
                    dados_produto['name'] = name

                    dados = {}
                    for chave in dados_produto:
                        if not isinstance(dados_produto[chave], DicionarioBrasil):
                            dados[chave] = dados_produto[chave]

                    item_obj.write(dados, context={'recalcula_fora_validade': True})

                    #if hasattr(item_pool, 'on_change_quantidade_margem_desconto'):
                        #item_obj = item_pool.browse(cr, uid, item_obj.id)
                        #novos_dados = item_pool.on_change_quantidade_margem_desconto(cr, uid, [item_obj.id], pedido_obj.pricelist_id.id, item_obj.product_id.id, qty=quantidade, partner_id=pedido_obj.partner_id.id, vr_unitario_custo=dados_produto['vr_unitario_custo'], vr_unitario_minimo=dados_produto['vr_unitario_minimo'], margem=margem, desconto=desconto, mudou_quantidade=True, usa_unitario_minimo=usa_unitario_minimo, desconto_direto=True, context=contexto_novo, date_order=str(hoje()))

                        #if 'value' in novos_dados:
                            #dados_produto = novos_dados['value']

                            #dados_produto['product_uom_qty'] = quantidade
                            #dados_produto['usa_unitario_minimo'] = usa_unitario_minimo
                            #dados_produto['margem'] = margem
                            #dados_produto['discount'] = desconto
                            #dados_produto['name'] = name

                            #dados = {}
                            #for chave in dados_produto:
                                #if not isinstance(dados_produto[chave], DicionarioBrasil):
                                    #dados[chave] = dados_produto[chave]

                            #item_obj.write(dados)

            #
            # Aponta a nova validade
            #
            if hasattr(pedido_obj, 'dt_validade'):
                nova_validade = hoje()
                nova_validade += relativedelta(days=+getattr(pedido_obj, 'dias_validade', 10))
                print('nova_validade')
                print(nova_validade)
                pedido_obj.write({'dt_validade': str(nova_validade)}, context={'recalcula_fora_validade': True})

            #
            # Aponta a nova validade
            #
            if hasattr(pedido_obj, 'data_validade'):
                nova_validade = hoje()
                nova_validade += relativedelta(days=+getattr(pedido_obj, 'dias_validade', 10))
                print('nova_validade')
                print(nova_validade)
                pedido_obj.write({'data_validade': str(nova_validade)}, context={'recalcula_fora_validade': True})

        return True

    def autoriza_desconto(self, cr, uid, ids, context={}):
        for sale_obj in self.browse(cr, uid, ids):
            sale_obj.write({'desconto_autorizado': True, 'desconto_a_autorizar': False})

        return ids

    def encerrar_pedido(self, cr, uid, ids, context={}):
        #
        # Encerra o pedido e libera para o faturamento
        #
        for orc_obj in self.browse(cr, uid, ids):
            orc_obj.write({'state': 'done'})


sale_order()
