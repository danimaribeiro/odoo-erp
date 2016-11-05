# -*- encoding: utf-8 -*-

from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from pybrasil.base import DicionarioBrasil
from tools.translate import _
import netsvc
from pybrasil.data import formata_data, hoje, ultimo_dia_mes
from pybrasil.valor import formata_valor
from copy import copy
import random
import os
import base64
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


DIAS_VENCIMENTO = [
    #[ '1', ' 1'],
    [ '2', ' 2'],
    #[ '3', ' 3'],
    #[ '4', ' 4'],
    [ '5', ' 5'],
    #[ '6', ' 6'],
    #[ '7', ' 7'],
    #[ '8', ' 8'],
    #[ '9', ' 9'],
    ['10', '10'],
    #['11', '11'],
    #['12', '12'],
    #['13', '13'],
    #['14', '14'],
    #['15', '15'],  # Comentado chamado 2902
    #['16', '16'],
    #['17', '17'],
    #['18', '18'],
    #['19', '19'],
    #['20', '20'],  # Comentado chamado 2902
    #['21', '21'],
    #['22', '22'],
    #['23', '23'],
    #['24', '24'],
    #['25', '25'],  # Comentado chamado 2902
    #['26', '26'],
    #['27', '27'],
    #['28', '28'],
    #['29', '29'],
    #['30', '30']   # Comentado chamado 2902
]



CATEGORIA_EQUIPAMENTO_EMPRESA_ID = 1
CATEGORIA_INFRAESTRUTURA_ID = 2
CATEGORIA_ACESSORIOS_ID = 4
CATEGORIA_MAO_DE_OBRA_ID = 6


def monta_objs(self, cr, uid):
    produto_pool = self.pool.get('product.product')

    BECAPE_CHIP_CLARO_OBJ = produto_pool.browse(cr, 1, 1834)

    BECAPE_CHIP_OI_OBJ = produto_pool.browse(cr, 1, 1835)

    BECAPE_CHIP_TIM_OBJ = produto_pool.browse(cr, 1, 1833)

    BECAPE_CHIP_VIVO_OBJ = produto_pool.browse(cr, 1, 1832)

    POSTO_MOVEL_OBJ = produto_pool.browse(cr, 1, 3196)

    RONDA_OBJ = produto_pool.browse(cr, 1, 3195)

    MANUTENCAO_TECNICA_OBJ = produto_pool.browse(cr, 1, 3315)

    MONITORAMENTO_ELETRONICO_OBJ = produto_pool.browse(cr, 1, 3178)

    MONITORAMENTO_IMAGENS_OBJ = produto_pool.browse(cr, 1, 3186)

    ANIMAL_ADESTRADO_OBJ = produto_pool.browse(cr, 1, 3187)

    MONITORAMENTO_GARANTIDO_PESSOA_FISICA_OBJ = produto_pool.browse(cr, 1, 3204)

    MONITORAMENTO_GARANTIDO_PESSOA_JURIDICA_OBJ = produto_pool.browse(cr, 1, 3205)

    ACESSORIOS_OBJ = produto_pool.browse(cr, 1, 3191)

    MAO_DE_OBRA_INSTALACAO_OBJ = produto_pool.browse(cr, 1, 3367)

    return (BECAPE_CHIP_CLARO_OBJ, BECAPE_CHIP_OI_OBJ, BECAPE_CHIP_TIM_OBJ, BECAPE_CHIP_VIVO_OBJ, POSTO_MOVEL_OBJ, RONDA_OBJ, MANUTENCAO_TECNICA_OBJ, MONITORAMENTO_ELETRONICO_OBJ, MONITORAMENTO_IMAGENS_OBJ, ANIMAL_ADESTRADO_OBJ, MONITORAMENTO_GARANTIDO_PESSOA_FISICA_OBJ, MONITORAMENTO_GARANTIDO_PESSOA_JURIDICA_OBJ, ACESSORIOS_OBJ, MAO_DE_OBRA_INSTALACAO_OBJ)


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'
    _order = 'date_order desc, name desc'

    def _pendencia_financeira(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for orc_obj in self.browse(cr, uid, ids, context=context):
            sql = """
            select
                l.id

            from
                finan_lancamento l

            where
                l.tipo = 'R'
                and l.situacao = 'Vencido'
                and (current_date - l.data_vencimento) >= 10
                and l.partner_id = {partner_id};
            """
            sql = sql.format(partner_id=orc_obj.partner_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[orc_obj.id] = len(dados) > 0

        return res

    def _mensalidade_excede_limite(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for order_obj in self.browse(cr, uid, ids, context=context):
            res[order_obj.id] = False

            if order_obj.orcamento_aprovado != 'locacao':
                continue

            #
            # Os contratos podem ser da Comércio ou da Segurança, conforme o tipo de mensalidade
            #
            #
            # Patrimonial Segurança
            #
            mensal_mon_eletronico = D(0)
            if order_obj.monitoramento_eletronico:
                mensal_mon_eletronico = D(order_obj.monitoramento_eletronico or 0)
            #print(mensal_mon_eletronico)

            if order_obj.posto_movel:
                mensal_mon_eletronico += D(order_obj.posto_movel or 0)
            #print(mensal_mon_eletronico)

            if order_obj.ronda:
                mensal_mon_eletronico += D(order_obj.ronda or 0)
            #print(mensal_mon_eletronico)

            #if order_obj.manutencao_tecnica:
                #mensal_mon_eletronico += D(order_obj.manutencao_tecnica or 0)
            #print(mensal_mon_eletronico)

            if order_obj.qtd_becape_chip and order_obj.produto_chip_id:
                mensal_mon_eletronico += D(order_obj.qtd_becape_chip or 0) * D(order_obj.vr_becape_chip or 0)
            #print(mensal_mon_eletronico)

            mensal_mon_imagens = D(0)
            if order_obj.monitoramento_imagens:
                mensal_mon_imagens = D(order_obj.monitoramento_imagens or 0)
            #print(mensal_mon_imagens)

            mensal_mon_garantido = D(0)
            if order_obj.qtd_monitoramento_garantido:
                mensal_mon_garantido = D(order_obj.qtd_monitoramento_garantido or 0) * D(order_obj.vr_monitoramento_garantido or 0)
            #print(mensal_mon_garantido)

            mensal_vig_animal = D(0)
            if order_obj.animal_adestrado:
                mensal_vig_animal = D(order_obj.animal_adestrado or 0)
            #print(mensal_vig_animal)

            mensal_seguranca = mensal_mon_eletronico + mensal_mon_imagens + mensal_mon_garantido + mensal_vig_animal

            mensal_comercio = (order_obj.vr_mensal or 0)
            #print(mensal_seguranca)
            #print(mensal_comercio)
            mensal_comercio -= mensal_seguranca

            res[order_obj.id] = (mensal_seguranca > order_obj.partner_vr_limite_credito) or (mensal_comercio > order_obj.partner_vr_limite_credito)

        return res

    def _operacoes_fiscais(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for order_obj in self.browse(cr, uid, ids, context=context):
            operacoes = []

            if order_obj.bonificacao_venda:
                operacoes = [419, 163]

            else:
                if order_obj.company_id.operacao_id:
                    operacoes.append(order_obj.company_id.operacao_id.id)

                if order_obj.company_id.operacao_pessoa_fisica_id:
                    operacoes.append(order_obj.company_id.operacao_pessoa_fisica_id.id)

                if order_obj.company_id.operacao_ativo_id:
                    operacoes.append(order_obj.company_id.operacao_ativo_id.id)

                if order_obj.company_id.operacao_faturamento_antecipado_id:
                    operacoes.append(order_obj.company_id.operacao_faturamento_antecipado_id.id)

            res[order_obj.id] = operacoes

        return res

    _columns = {
        'partner_vr_limite_credito': fields.related('partner_id', 'vr_limite_credito', type='float', string=u'Limite de crédito mensal'),
        'motivo_liberacao_venda_sem_limite': fields.char(u'Motivo da liberação', size=180),
        'pendencia_financeira': fields.function(_pendencia_financeira, type='boolean', string=u'Pendência financeira'),
        'parcela_excede_limite': fields.boolean(u'Parcelas excedem limite de crédito mensal?'),
        'mensalidade_excede_limite': fields.function(_mensalidade_excede_limite, type='boolean', string=u'Mensalidades excedem limite de crédito mensal?'),

        'orcamento_aprovado': fields.selection([('venda', 'venda'), ('locacao', u'locação')], u'Orçamento aprovado para', required=True),
        #
        # O estado de aprovado cria uma cópia dos itens aprovados
        # do pedido, para comparação com efetivamente faturado
        # vindo do estoque
        #
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

        'orcamento_resumo_venda_ids': fields.one2many('orcamento.orcamento_locacao', 'sale_order_id', u'Resumo do orçamento', domain=[('considera_venda', '=', True)]),
        'orcamento_resumo_locacao_ids': fields.one2many('orcamento.orcamento_locacao', 'sale_order_id', u'Resumo do orçamento', domain=[('considera_venda', '!=', True)]),

        'produto_chip_id': fields.many2one('product.product', u'Chip'),
        'qtd_becape_chip': fields.integer(u'Qtde.'),
        'vr_becape_chip': fields.float(u'Valor'),
        #'becape_chip_claro': fields.integer(u'Chip CLARO'),
        #'becape_chip_oi': fields.integer(u'Chip OI'),
        #'becape_chip_tim': fields.integer(u'Chip TIM'),
        #'becape_chip_vivo': fields.integer(u'Chip VIVO'),

        'posto_movel': fields.float(u'Posto móvel', digits=(18, 2)),
        'ronda': fields.float(u'Ronda/acompanhamento', digits=(18, 2)),
        'manutencao_tecnica': fields.float(u'Manutenção técnica', digits=(18, 2)),
        'monitoramento_eletronico': fields.float(u'Monitoramento eletrônico', digits=(18, 2)),
        'monitoramento_imagens': fields.float(u'Monitoramento de imagens', digits=(18, 2)),
        'animal_adestrado': fields.float(u'Animais adestrados', digits=(18, 2)),

        'produto_monitoramento_garantido_id': fields.many2one('product.product', u'Monitoramento garantido'),
        'qtd_monitoramento_garantido': fields.integer(u'Qtde.'),
        'vr_monitoramento_garantido': fields.float(u'Valor'),
        #'monitoramento_garantido_pessoa_fisica': fields.integer(u'Monitoramento garantido (pessoa física)', digits=(18, 2)),
        #'monitoramento_garantido_pessoa_juridica': fields.integer(u'Monitoramento garantido (pessoa jurídica)', digits=(18, 2)),

        'becape_chip_id':  fields.many2one('sale.order.line', u'Chip'),
        #'becape_chip_claro_id': fields.many2one('sale.order.line', u'Chip CLARO'),
        #'becape_chip_oi_id': fields.many2one('sale.order.line', u'Chip OI'),
        #'becape_chip_tim_id': fields.many2one('sale.order.line', u'Chip TIM'),
        #'becape_chip_vivo_id': fields.many2one('sale.order.line', u'Chip VIVO'),

        'posto_movel_id': fields.many2one('sale.order.line', u'Posto móvel'),
        'ronda_id': fields.many2one('sale.order.line', u'Ronda'),
        'manutencao_tecnica_id': fields.many2one('sale.order.line', u'Manutenção técnica'),
        'monitoramento_eletronico_id': fields.many2one('sale.order.line', u'Monitoramento eletrônico'),
        'monitoramento_imagens_id': fields.many2one('sale.order.line', u'Monitoramento de imagens'),
        'animal_adestrado_id': fields.many2one('sale.order.line', u'Animais adestrados'),

        'monitoramento_garantido_id': fields.many2one('sale.order.line', u'Monitoramento garantido'),
        #'monitoramento_garantido_pessoa_fisica_id': fields.many2one('sale.order.line', u'Monitoramento garantido (pessoa física)'),
        #'monitoramento_garantido_pessoa_juridica_id': fields.many2one('sale.order.line', u'Monitoramento garantido (pessoa jurídica)'),

        'percentual_acessorios': fields.float(u'Acessórios'),
        'percentual_acessorios_id': fields.many2one('sale.order.line', u'Acessórios'),
        'mao_de_obra_instalacao': fields.float(u'Mão-de-obra de instalação'),
        'mao_de_obra_instalacao_faturamento_direto': fields.boolean(u'Faturamento direto?'),
        'mao_de_obra_instalacao_id': fields.many2one('sale.order.line', u'Mão-de-obra de instalação'),
        'mao_de_obra_instalacao_payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento da mão-de-obra'),

        'item_aprovado_ids': fields.one2many('sale.order.line.aprovado', 'order_id', u'Itens aprovados'),
        'partner_assinatura_id': fields.many2one('res.partner.address', u'Assinatura do contrato', domain=[('type', '=', 'assinatura')]),

        'somente_mao_obra': fields.boolean(u'Somente mão de obra?'),
        'bonificacao_venda': fields.boolean(u'É bonificação?'),

        'valor_entrada': fields.float(u'Valor de entrada'),
        'mao_de_obra_instalacao_valor_entrada': fields.float(u'Valor de entrada'),
        'simulacao_parcelas': fields.text(u'Simulação das parcelas'),

        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelete='restrict'),
        'res_partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),

        'nome_pdf_versao_cliente': fields.char(u'Versão do cliente', 120, readonly=True),
        'pdf_versao_cliente': fields.binary(u'Versão do cliente', readonly=True),
        'nome_pdf_versao_detalhada': fields.char(u'Versão detalhada', 120, readonly=True),
        'pdf_versao_detalhada': fields.binary(u'Versão detalhada', readonly=True),
        'nome_pdf_mao_de_obra': fields.char(u'Mão-de-obra', 120, readonly=True),
        'pdf_versao_mao_de_obra': fields.binary(u'Mão-de-obra', readonly=True),

        #
        # Para vincular a mão de obra da locação na proposta de venda
        #
        'proposta_venda_id': fields.many2one('sale.order', u'Proposta de venda'),

        #
        # Dados dos contratos
        #
        'data_assinatura': fields.date(u'Data de início do serviço'),
        'data_inicio': fields.date(u'Data de início da cobrança'),
        'conferido_vendedor': fields.boolean(u'Conferido pelo comercial?'),
        'dia_vencimento': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento'),
        'pro_rata': fields.boolean('Pro-rata?'),
        'duracao': fields.integer(u'Duração em meses'),

        'finan_contrato_ids': fields.one2many('finan.contrato', 'sale_order_id', u'Contratos'),
        'saldo_obra_liberado': fields.boolean(u'Saldo da obra já liberado?'),

        'contrato_original_comercio_id': fields.many2one('finan.contrato', u'Contrato original da Comércio', ondelete='restrict'),
        'contrato_original_seguranca_id': fields.many2one('finan.contrato', u'Contrato original da Segurança', ondelete='restrict'),
        'renegociacao': fields.boolean(u'É renegociação?'),
        'eh_mudanca_endereco': fields.boolean(u'É mudança de endereço?'),

        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),

        #
        # Checklist
        #
        'checklist_id': fields.many2one('checklist.contrato', u'Check-list' ),
        'checklist_ids': fields.one2many('checklist.contrato.item', 'sale_order_id', u'Check-list'),
        'operacao_fiscal_ids': fields.function(_operacoes_fiscais, type='many2many', relation='sped.operacao', string=u'Operações permitidas'),
    }

    _defaults = {
        'somente_mao_obra': False,
        'qtd_becape_chip': 0,
        'vr_becape_chip': 0,
        #'becape_chip_claro': 0,
        #'becape_chip_oi': 0,
        #'becape_chip_tim': 0,
        #'becape_chip_vivo': 0,
        'posto_movel': 0,
        'ronda': 0,
        'manutencao_tecnica': 0,
        'monitoramento_eletronico': 0,
        'monitoramento_imagens': 0,
        'animal_adestrado': 0,
        'qtd_monitoramento_garantido': 0,
        'vr_monitoramento_garantido': 0,
        'percentual_acessorios': 8,
        'mao_de_obra_instalacao': 0,
        #'monitoramento_garantido_pessoa_fisica': 0,
        #'monitoramento_garantido_pessoa_juridica': 0,

        'pro_rata': True,
        'dia_vencimento': '5',
    }

    def onchange_becape_chip(self, cr, uid, ids, produto_chip_id, qtd_becape_chip):
        res = {}
        valores = {}
        res['value'] = valores

        if not produto_chip_id:
            return res

        if not qtd_becape_chip:
            return res

        chip_obj = self.pool.get('product.product').browse(cr, uid, produto_chip_id)

        valores['vr_becape_chip'] = qtd_becape_chip * chip_obj.list_price

        return res

    def onchange_monitoramento_garantido(self, cr, uid, ids, produto_monitoramento_garantido_id, qtd_monitoramento_garantido):
        res = {}
        valores = {}
        res['value'] = valores

        if not produto_monitoramento_garantido_id:
            return res

        if not qtd_monitoramento_garantido:
            return res

        mg_obj = self.pool.get('product.product').browse(cr, uid, produto_monitoramento_garantido_id)

        valores['vr_monitoramento_garantido'] = qtd_monitoramento_garantido * mg_obj.list_price

        return res

    def create(self, cr, uid, dados, context={}):
        if '__copy_data_seen' not in context:
            self.pool.get('sale.order').valida_criacao_alteracao(cr, uid, False, dados)

        res = super(sale_order, self).create(cr, uid, dados, context=context)

        copia = '__copy_data_seen' in context

        if not copia:
            self.ajusta_itens_locacao_patrimonial(cr, uid, [res])
            #self.ajusta_itens_locacao_patrimonial(cr, uid, res)
            #self.gera_notas(cr, uid, [res], context={'ajusta_valor_venda': True})
            self.abre_oportunidade(cr, uid, [res], context={'salvando': True})

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if '__copy_data_seen' not in context:
            self.pool.get('sale.order').valida_criacao_alteracao(cr, uid, False, dados)

        if 'finan_contrato_ids' in dados:
            del dados['finan_contrato_ids']

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        print('dados que estão vindo')
        print(dados)
        #print('context')
        #print(context)

        #
        # Campos que permitem alteração
        #
        alteracao_permitida = ['hr_department_id', 'user_id', 'data_inicio', 'data_assinatura', 'note', 'shipped', 'payment_term', 'valor_entrada',
            'mao_de_obra_instalacao_payment_term_id', 'mao_de_obra_instalacao_valor_entrada', 'simulacao_parcelas', 'recalculo']
        pode_alterar = True
        campos_alterados = 0
        for chave in dados:
            #print(chave)
            if chave in alteracao_permitida:
                campos_alterados += 1
                break

        if campos_alterados == 0:
            pode_alterar = False

        #print(pode_alterar)

        #
        # Não deixa alterar se a ordem de entrega não estiver concluída
        #
        if (not pode_alterar) and ('state' not in dados and len(dados) > 0 and (not context.get('complementar', False))):
            picking_pool = self.pool.get('stock.picking')
            picking_ids = picking_pool.search(cr, uid, [['sale_id', 'in', ids]])
            picking_dados = picking_pool.read(cr, uid, picking_ids, ['state', 'name'])
            for picking_dado in picking_dados:
                if 'state' in picking_dado and picking_dado['state'] not in ['done', 'cancel']:
                    raise osv.except_osv(u'Erro', u'Não é permitido gravar as alterações enquanto a ordem de entrega nº {codigo} no estoque não estiver concluída!'.format(codigo=picking_dado['name']))

        if 'orcamento_aprovado' in dados:
            del dados['orcamento_aprovado']

        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        if (not context.get('complementar', False)):
            self.ajusta_itens_locacao_patrimonial(cr, uid, ids, context={'ajusta_locacao_patrimonial': True, 'calcula_resumo': True})

        return res

    def gerar_contratos(self, cr, uid, ids, context={}):
        contrato_pool = self.pool.get('finan.contrato')
        contrato_alteracao_pool = self.pool.get('finan.contrato.alteracao')

        order_obj = self.pool.get('sale.order').browse(cr, uid, ids[0])

        if order_obj.orcamento_aprovado != 'locacao':
            return

        if not order_obj.data_assinatura:
            raise osv.except_osv('Erro!', u'Não é possível gerar o(s) contrato(s) sem a informação da data de início do serviço')

        if not order_obj.data_inicio:
            raise osv.except_osv('Erro!', u'Não é possível gerar o(s) contrato(s) sem a informação da data de início da cobrança')

        if order_obj.data_inicio[:7] == order_obj.data_assinatura[:7]:
            raise osv.except_osv('Erro!', u'Não é possível gerar o(s) contrato(s) em que a data de início da cobrança ocorre no mesmo mê do início do serviço')

        if not order_obj.duracao:
            raise osv.except_osv('Erro!', u'Não é possível gerar o(s) contrato(s) sem a informação da duração')

        if not order_obj.conferido_vendedor:
            raise osv.except_osv('Erro!', u'Não é possível gerar o(s) contrato(s) sem a conferência do vendedor')

        #
        # Verifica se o vendedor a ser definido na proposta é o vendedor que é o dono
        # do cliente/carteira
        #
        if order_obj.partner_id.user_id and order_obj.partner_id.user_id.id != order_obj.user_id.id:
            raise osv.except_osv(u'Aviso!', u'O gestor de contas vinculado à proposta não é o gestor de contas da carteira do cliente; somente será permitido gerar o contrato/alteração contratual caso o gestor de contas seja alterado para “%s”!' % order_obj.partner_id.user_id.name)

        dados = {
            'sale_order_id': order_obj.id,
            'company_id': order_obj.company_id.id,
            'partner_id': order_obj.partner_id.id,
            'pro_rata': order_obj.pro_rata,
            'natureza': 'IR',
            'dia_vencimento': order_obj.dia_vencimento,
            'data_assinatura': order_obj.data_assinatura,
            'data_inicio': order_obj.data_inicio,
            'duracao': order_obj.duracao,
        }

        if order_obj.pro_rata:
            dados['data_encerramento'] = str(ultimo_dia_mes(order_obj.data_assinatura))

        #
        # Contratos que começam no início do mês não têm pro-rata
        #
        if order_obj.data_assinatura[8:10] == '01':
            dados['pro_rata'] = False

        if order_obj.partner_invoice_id:
            dados['res_partner_address_id'] = order_obj.partner_invoice_id.id

        if order_obj.partner_shipping_id:
            dados['endereco_prestacao_id'] = order_obj.partner_shipping_id.id

            if order_obj.partner_shipping_id.municipio_id:
                dados['municipio_id'] = order_obj.partner_shipping_id.municipio_id.id

        if 'municipio_id' not in dados:
            dados['municipio_id'] = order_obj.partner_id.municipio_id.id

        #
        # Os contratos podem ser da Comércio ou da Segurança, conforme o tipo de mensalidade
        #
        #
        # Patrimonial Segurança
        #
        mensal_mon_eletronico = D(0)
        if order_obj.monitoramento_eletronico:
            mensal_mon_eletronico = D(order_obj.monitoramento_eletronico or 0)
        #print(mensal_mon_eletronico)

        if order_obj.posto_movel:
            mensal_mon_eletronico += D(order_obj.posto_movel or 0)
        #print(mensal_mon_eletronico)

        if order_obj.ronda:
            mensal_mon_eletronico += D(order_obj.ronda or 0)
        #print(mensal_mon_eletronico)

        #if order_obj.manutencao_tecnica:
            #mensal_mon_eletronico += D(order_obj.manutencao_tecnica or 0)
        #print(mensal_mon_eletronico)

        if order_obj.qtd_becape_chip and order_obj.produto_chip_id:
            mensal_mon_eletronico += D(order_obj.qtd_becape_chip or 0) * D(order_obj.vr_becape_chip or 0)
        #print(mensal_mon_eletronico)

        mensal_mon_imagens = D(0)
        if order_obj.monitoramento_imagens:
            mensal_mon_imagens = D(order_obj.monitoramento_imagens or 0)
        #print(mensal_mon_imagens)

        mensal_mon_garantido = D(0)
        if order_obj.qtd_monitoramento_garantido:
            mensal_mon_garantido = D(order_obj.qtd_monitoramento_garantido or 0) * D(order_obj.vr_monitoramento_garantido or 0)
        #print(mensal_mon_garantido)

        mensal_vig_animal = D(0)
        if order_obj.animal_adestrado:
            mensal_vig_animal = D(order_obj.animal_adestrado or 0)
        #print(mensal_vig_animal)

        mensal_seguranca = mensal_mon_eletronico + mensal_mon_imagens + mensal_mon_garantido + mensal_vig_animal

        mensal_comercio = (order_obj.vr_mensal or 0)
        #print(mensal_seguranca)
        #print(mensal_comercio)
        mensal_comercio -= mensal_seguranca

        if mensal_comercio > 0:
            #
            # Vai ser aumento da mensalidade?
            #
            if order_obj.contrato_original_comercio_id:
                #
                # Gera as próximas parcelas do contrato antes
                #
                contrato_pool.gera_todas_parcelas(cr, 1, [order_obj.contrato_original_comercio_id.id])

                dados_comercio = copy(dados)
                dados_comercio['tipo'] = 'V'
                dados_comercio['solicitante_id'] = order_obj.user_id.id
                dados_comercio['contrato_id'] = order_obj.contrato_original_comercio_id.id
                dados_comercio['company_id'] =  order_obj.contrato_original_comercio_id.company_id.id
                dados_comercio['data_alteracao'] = order_obj.data_assinatura
                dados_comercio['eh_mudanca_endereco'] = order_obj.eh_mudanca_endereco

                if order_obj.renegociacao or order_obj.eh_mudanca_endereco:
                    if mensal_comercio < D(order_obj.contrato_original_comercio_id.valor_mensal or 0):
                        dados_comercio['eh_reducao_valor'] = True

                principal = contrato_alteracao_pool.onchange_contrato_id(cr, uid, False, order_obj.contrato_original_comercio_id.id, 'V')

                dados_comercio.update(principal['value'])

                contrato_comercio_id = contrato_alteracao_pool.create(cr, uid, dados_comercio)
                #
                # Ajusta os itens faturados da Comércio
                #
                itens = contrato_alteracao_pool.onchange_sale_order_id(cr, uid, [contrato_comercio_id], order_obj.id, order_obj.contrato_original_comercio_id.id, dados_comercio['valor_mensal_anterior'])
                contrato_alteracao_pool.write(cr, uid, [contrato_comercio_id], itens['value'])
                dados_comercio.update(itens['value'])

                datas = contrato_alteracao_pool.onchange_data_alteracao(cr, uid, [contrato_comercio_id], dados_comercio['data_alteracao'], dados_comercio['data_proximo_vencimento_nao_faturado'])
                contrato_alteracao_pool.write(cr, uid, [contrato_comercio_id], datas['value'])
                dados_comercio.update(datas['value'])

                valores = contrato_alteracao_pool.onchange_valor_mensal_novo(cr, uid, [contrato_comercio_id], dados_comercio['valor_mensal_novo'], dados_comercio['valor_mensal_anterior'], dados_comercio['data_alteracao'], dados_comercio['pro_rata_novo_valor'])
                contrato_alteracao_pool.write(cr, uid, [contrato_comercio_id], valores['value'])

            #
            # Ou senão, é contrato novo
            #
            else:
                contrato_comercio_id = contrato_pool.create(cr, uid, dados)
                contrato_comercio_obj = contrato_pool.browse(cr, uid, contrato_comercio_id)
                #
                # Ajusta os itens faturados da Comércio
                #
                itens = contrato_comercio_obj.onchange_sale_order_id(order_obj.company_id.id, order_obj.id)
                contrato_comercio_obj.write(itens['value'])

        if mensal_seguranca > 0:

            #
            # Vai ser aumento da mensalidade?
            #
            if order_obj.contrato_original_seguranca_id:
                #
                # Gera as próximas parcelas do contrato antes
                #
                contrato_pool.gera_todas_parcelas(cr, 1, [order_obj.contrato_original_seguranca_id.id])

                dados_seguranca = copy(dados)
                dados_seguranca['tipo'] = 'V'
                dados_seguranca['solicitante_id'] = order_obj.user_id.id
                dados_seguranca['contrato_id'] = order_obj.contrato_original_seguranca_id.id
                dados_seguranca['company_id'] =  order_obj.contrato_original_seguranca_id.company_id.id
                dados_seguranca['data_alteracao'] = order_obj.data_assinatura
                dados_seguranca['eh_mudanca_endereco'] = order_obj.eh_mudanca_endereco

                if order_obj.renegociacao or order_obj.eh_mudanca_endereco:
                    if mensal_seguranca < D(order_obj.contrato_original_seguranca_id.valor_mensal or 0):
                        dados_seguranca['eh_reducao_valor'] = True

                principal = contrato_alteracao_pool.onchange_contrato_id(cr, uid, False, order_obj.contrato_original_seguranca_id.id, 'V')

                dados_seguranca.update(principal['value'])

                contrato_seguranca_id = contrato_alteracao_pool.create(cr, uid, dados_seguranca)
                #
                # Ajusta os itens faturados da Segurança
                #
                itens = contrato_alteracao_pool.onchange_sale_order_id(cr, uid, [contrato_seguranca_id], order_obj.id, order_obj.contrato_original_seguranca_id.id, dados_seguranca['valor_mensal_anterior'])
                contrato_alteracao_pool.write(cr, uid, [contrato_seguranca_id], itens['value'])
                dados_seguranca.update(itens['value'])

                datas = contrato_alteracao_pool.onchange_data_alteracao(cr, uid, [contrato_seguranca_id], dados_seguranca['data_alteracao'], dados_seguranca['data_proximo_vencimento_nao_faturado'])
                contrato_alteracao_pool.write(cr, uid, [contrato_seguranca_id], datas['value'])
                dados_seguranca.update(datas['value'])

                valores = contrato_alteracao_pool.onchange_valor_mensal_novo(cr, uid, [contrato_seguranca_id], dados_seguranca['valor_mensal_novo'], dados_seguranca['valor_mensal_anterior'], dados_seguranca['data_alteracao'], dados_seguranca['pro_rata_novo_valor'])
                contrato_alteracao_pool.write(cr, uid, [contrato_seguranca_id], valores['value'])

            #
            # Ou senão, é contrato novo
            #
            else:
                dados['company_id'] = order_obj.company_id.unidade_contrato_servico_id.id
                contrato_seguranca_id = contrato_pool.create(cr, uid, dados)
                contrato_seguranca_obj = contrato_pool.browse(cr, uid, contrato_seguranca_id)
                #
                # Ajusta os itens faturados da Segurança
                #
                itens = contrato_seguranca_obj.onchange_sale_order_id(order_obj.company_id.unidade_contrato_servico_id.id, order_obj.id)

                contrato_seguranca_obj.write(itens['value'])

        #
        # Agora que gerou os contratos, encerra o pedido
        #
        order_obj.write({'state': 'done'})

    def copy(self, cr, uid, id, default={}, context={}):
        res = super(sale_order, self).copy(cr, uid, id, default=default, context=context)

        #
        # Agora, revincula os itens específicos da Patrimonial
        #
        novo_obj = self.browse(cr, uid, res)
        dados = {}
        for item_obj in novo_obj.order_line:
            if novo_obj.produto_chip_id:
                if item_obj.product_id.id == novo_obj.produto_chip_id.id:
                    cr.execute('update sale_order set becape_chip_id = %d where id = %d' % (item_obj.id, novo_obj.id))

            if novo_obj.produto_monitoramento_garantido_id:
                if item_obj.product_id.id == novo_obj.produto_monitoramento_garantido_id.id:
                    cr.execute('update sale_order set monitoramento_garantido_id = %d where id = %d' % (item_obj.id, novo_obj.id))

            if item_obj.product_id.id == 3196:
                cr.execute('update sale_order set posto_movel_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3195:
                cr.execute('update sale_order set ronda_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3197:
                cr.execute('update sale_order set manutencao_tecnica_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3178:
                cr.execute('update sale_order set monitoramento_eletronico_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3186:
                cr.execute('update sale_order set monitoramento_imagens_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3187:
                cr.execute('update sale_order set animal_adestrado_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3191:
                cr.execute('update sale_order set percentual_acessorios_id = %d where id = %d' % (item_obj.id, novo_obj.id))
            elif item_obj.product_id.id == 3313:
                cr.execute('update sale_order set mao_de_obra_instalacao_id = %d where id = %d' % (item_obj.id, novo_obj.id))

        return res

    def _monta_dados_item(self, orc_obj, produto_obj):
        dados = {
            'order_id': orc_obj.id,
            'product_id': produto_obj.id,
            'name': produto_obj.name,
            'orcamento_categoria_id': produto_obj.orcamento_categoria_id.id,
            'product_uom_qty': 1,
            'vr_unitario_custo': produto_obj.standard_price,
            'vr_total_custo': produto_obj.standard_price,
            'vr_total_minimo': 0,
            'vr_unitario_minimo': produto_obj.standard_price,
            'vr_unitario_venda': produto_obj.list_price,
            'vr_total': 0,
            'vr_unitario_margem_desconto': 0,
            'vr_total_margem_desconto': 0,
            'price_unit': produto_obj.list_price,
            'usa_unitario_minimo': False,
            'margem': 0,
            'discount': 0,
            'vr_comissao': 0,
            'vr_comissao_locacao': 0,
            'comissao_venda_id': False,
            'comissao_locacao_id': False,
            'product_uom': produto_obj.uom_id.id,
            'type': produto_obj.procure_method,
            'th_weight': 0,
            'product_packaging': False,
            'product_uos_qty': 1,
            'notes': produto_obj.description_sale,
            'autoinsert': False,
        }

        if produto_obj.orcamento_categoria_id.comissao_venda_id:
            dados['comissao_venda_id'] = produto_obj.orcamento_categoria_id.comissao_venda_id.id
        if produto_obj.orcamento_categoria_id.comissao_locacao_id:
            dados['comissao_locacao_id'] = produto_obj.orcamento_categoria_id.comissao_locacao_id.id

        if orc_obj.partner_id.comissao_venda_id:
            dados['comissao_venda_id'] = orc_obj.partner_id.comissao_venda_id.id
        if orc_obj.partner_id.comissao_locacao_id:
            dados['comissao_locacao_id'] = orc_obj.partner_id.comissao_locacao_id.id

        return dados

    def ajusta_itens_locacao_patrimonial(self, cr, uid, orc_ids, context={}):
        for orc_obj in self.pool.get('sale.order').browse(cr, 1, orc_ids):
            ##
            ## Ajustamos o usuário para ser o usuário dono do cliente
            ##
            #if orc_obj.partner_id.user_id:
                #uid = orc_obj.partner_id.user_id.id

            #
            # Ajusta o faturamento direto
            #
            if orc_obj.mao_de_obra_instalacao_faturamento_direto:
                sql = '''
                update sale_order_line set
                    ignora_impostos = True,
                    margem = 0,
                    discount = 0,
                    vr_unitario_margem_desconto = vr_unitario_custo,
                    vr_unitario_venda_impostos = vr_unitario_custo,
                    vr_total_margem_desconto = vr_unitario_custo * product_uom_qty,
                    vr_total_venda_impostos = vr_unitario_custo * product_uom_qty,
                    porcentagem_imposto = 0,
                    proporcao_imposto = 0,
                    total_imposto = 0

                where
                    order_id = {ped_id}
                    and orcamento_categoria_id = 6;
                '''.format(ignora_impostos=orc_obj.mao_de_obra_instalacao_faturamento_direto, ped_id=orc_obj.id)

            else:
                sql = '''
                update sale_order_line set
                    ignora_impostos = False
                where
                    order_id = {ped_id}
                    and orcamento_categoria_id = 6;
                '''.format(ignora_impostos=orc_obj.mao_de_obra_instalacao_faturamento_direto, ped_id=orc_obj.id)

            cr.execute(sql)

            BECAPE_CHIP_CLARO_OBJ, BECAPE_CHIP_OI_OBJ, BECAPE_CHIP_TIM_OBJ, BECAPE_CHIP_VIVO_OBJ, POSTO_MOVEL_OBJ, RONDA_OBJ, MANUTENCAO_TECNICA_OBJ, MONITORAMENTO_ELETRONICO_OBJ, MONITORAMENTO_IMAGENS_OBJ, ANIMAL_ADESTRADO_OBJ, MONITORAMENTO_GARANTIDO_PESSOA_FISICA_OBJ, MONITORAMENTO_GARANTIDO_PESSOA_JURIDICA_OBJ, ACESSORIOS_OBJ, MAO_DE_OBRA_INSTALACAO_OBJ = monta_objs(self, cr, uid)

            item_pool = self.pool.get('sale.order.line')
            locacao_pool = self.pool.get('orcamento.orcamento_locacao')

            itens_quantidade = []

            #itens_quantidade = [
                #[orc_obj.becape_chip_claro, BECAPE_CHIP_CLARO_OBJ, orc_obj.becape_chip_claro_id, 'becape_chip_claro_id'],
                #[orc_obj.becape_chip_oi, BECAPE_CHIP_OI_OBJ, orc_obj.becape_chip_oi_id, 'becape_chip_oi_id'],
                #[orc_obj.becape_chip_tim, BECAPE_CHIP_TIM_OBJ, orc_obj.becape_chip_tim_id, 'becape_chip_tim_id'],
                #[orc_obj.becape_chip_vivo, BECAPE_CHIP_VIVO_OBJ, orc_obj.becape_chip_vivo_id, 'becape_chip_vivo_id'],
                #[orc_obj.monitoramento_garantido_pessoa_fisica, MONITORAMENTO_GARANTIDO_PESSOA_FISICA_OBJ, orc_obj.monitoramento_garantido_pessoa_fisica_id, 'monitoramento_garantido_pessoa_fisica_id'],
                #[orc_obj.monitoramento_garantido_pessoa_juridica, MONITORAMENTO_GARANTIDO_PESSOA_JURIDICA_OBJ, orc_obj.monitoramento_garantido_pessoa_juridica_id, 'monitoramento_garantido_pessoa_juridica_id'],
            #]

            if orc_obj.produto_chip_id:
                item_chip = [[
                    orc_obj.qtd_becape_chip,
                    orc_obj.produto_chip_id,
                    orc_obj.becape_chip_id,
                    'becape_chip_id',
                ]]
                itens_quantidade += item_chip

            if orc_obj.produto_monitoramento_garantido_id:
                item_monitoramento_garantido = [[
                    orc_obj.qtd_monitoramento_garantido,
                    orc_obj.produto_monitoramento_garantido_id,
                    orc_obj.monitoramento_garantido_id,
                    'monitoramento_garantido_id',
                ]]
                itens_quantidade += item_monitoramento_garantido

            for quantidade, produto_obj, item_obj, nome_campo in itens_quantidade:
                if (not quantidade) and item_obj:
                    item_obj.unlink(context={'calculo_resumo': True})

                if quantidade:
                    dados = self._monta_dados_item(orc_obj, produto_obj)
                    dados['product_uom_qty'] = quantidade
                    dados['product_uos_qty'] = quantidade
                    dados['vr_total_custo'] = quantidade * dados['vr_unitario_custo']
                    dados['vr_total_minimo'] = quantidade * dados['vr_unitario_minimo']
                    dados['vr_total'] = quantidade * dados['price_unit']
                    vr_total = D(str(dados['vr_total']))

                    if not item_obj:
                        dados['margem'] = produto_obj.orcamento_categoria_id.margem or 0
                    else:
                        dados['margem'] = item_obj.margem or 0
                        dados['discount'] = item_obj.discount or 0

                    margem = D(str(dados['margem']))
                    desconto = D(str(dados['discount']))

                    vr_total_margem_desconto = vr_total * (1 + (margem / D('100.00')))
                    vr_total_margem_desconto *= 1 - (desconto / D('100.00'))
                    vr_total_margem_desconto = vr_total_margem_desconto.quantize(D('0.01'))
                    dados['vr_total_margem_desconto'] = vr_total_margem_desconto
                    dados['vr_unitario_margem_desconto'] = vr_total_margem_desconto / quantidade

                    if not item_obj:
                        id = item_pool.create(cr, uid, dados, context={'__copy_data_seen': True})
                        cr.execute('update sale_order set ' + nome_campo + ' = ' + str(id) + ' where id = ' + str(orc_obj.id) + ';')
                        item_obj = item_pool.browse(cr, uid, id)
                    else:
                        item_obj.write(dados, context={'calculo_resumo': True})

                    item_pool.after_insert_update(cr, uid, item_obj.id)

            itens_valor = [
                [orc_obj.posto_movel, POSTO_MOVEL_OBJ, orc_obj.posto_movel_id, 'posto_movel_id'],
                [orc_obj.ronda, RONDA_OBJ, orc_obj.ronda_id, 'ronda_id'],
                [orc_obj.manutencao_tecnica, MANUTENCAO_TECNICA_OBJ, orc_obj.manutencao_tecnica_id, 'manutencao_tecnica_id'],
                [orc_obj.monitoramento_eletronico, MONITORAMENTO_ELETRONICO_OBJ, orc_obj.monitoramento_eletronico_id, 'monitoramento_eletronico_id'],
                [orc_obj.monitoramento_imagens, MONITORAMENTO_IMAGENS_OBJ, orc_obj.monitoramento_imagens_id, 'monitoramento_imagens_id'],
                [orc_obj.animal_adestrado, ANIMAL_ADESTRADO_OBJ, orc_obj.animal_adestrado_id, 'animal_adestrado_id'],
                [orc_obj.mao_de_obra_instalacao, MAO_DE_OBRA_INSTALACAO_OBJ, orc_obj.mao_de_obra_instalacao_id, 'mao_de_obra_instalacao_id'],
            ]

            for valor, produto_obj, item_obj, nome_campo in itens_valor:
                if not valor and item_obj:
                    item_obj.unlink(context={'calculo_resumo': True})

                if valor:
                    dados = self._monta_dados_item(orc_obj, produto_obj)
                    dados['price_unit'] = valor
                    dados['vr_unitario_venda'] = valor
                    dados['vr_unitario_minimo'] = valor
                    dados['vr_unitario_venda_impostos'] = valor

                    locacao_id = locacao_pool.search(cr, uid, [('sale_order_id', '=', orc_obj.id), ('orcamento_categoria_id', '=', produto_obj.orcamento_categoria_id.id)])[0]
                    locacao_obj = locacao_pool.browse(cr, uid, locacao_id)

                    if produto_obj.id == MAO_DE_OBRA_INSTALACAO_OBJ.id:
                        dados['vr_unitario_custo'] = valor
                        quantidade = D(1)
                        dados['ignora_impostos'] = orc_obj.mao_de_obra_instalacao_faturamento_direto
                        if dados['ignora_impostos']:
                            dados['porcentagem_imposto'] = 0
                            dados['proporcao_imposto'] = 0
                            dados['vr_unitario_venda_impostos'] = valor

                    else:
                        quantidade = D(str(locacao_obj.meses_retorno_investimento))

                    dados['product_uom_qty'] = quantidade
                    dados['product_uos_qty'] = quantidade

                    dados['vr_total_custo'] = quantidade * D(str(dados['vr_unitario_custo']))
                    dados['vr_total_minimo'] = quantidade * D(str(dados['vr_unitario_minimo']))
                    dados['vr_total'] = quantidade * D(str(dados['price_unit']))
                    vr_total = D(str(dados['vr_total']))

                    if not item_obj:
                        dados['margem'] = produto_obj.orcamento_categoria_id.margem
                    else:
                        dados['margem'] = item_obj.margem
                        dados['discount'] = item_obj.discount

                    margem = D(str(dados['margem']))
                    desconto = D(str(dados['discount']))

                    vr_total_margem_desconto = vr_total / (1 - (margem / D('100.00')))
                    vr_total_margem_desconto *= 1 - (desconto / D('100.00'))
                    vr_total_margem_desconto = vr_total_margem_desconto.quantize(D('0.01'))
                    dados['vr_total_margem_desconto'] = vr_total_margem_desconto
                    dados['vr_unitario_margem_desconto'] = vr_total_margem_desconto / quantidade
                    dados['vr_total_venda_impostos'] = dados['vr_unitario_venda_impostos'] * quantidade

                    if 'ignora_impostos' in dados and dados['ignora_impostos']:
                        dados['margem'] = 0
                        dados['desconto'] = 0
                        dados['porcentagem_imposto'] = 0
                        dados['proporcao_imposto'] = 0
                        dados['total_imposto'] = 0
                        dados['vr_unitario_margem_desconto'] = valor
                        dados['vr_total_margem_desconto'] = D(valor) * quantidade
                        dados['vr_unitario_venda_impostos'] = valor
                        dados['vr_total_venda_impostos'] = D(valor) * quantidade

                    if not item_obj:
                        id = item_pool.create(cr, uid, dados, context={'__copy_data_seen': True})
                        item_obj = item_pool.browse(cr, uid, id)
                        cr.execute('update sale_order set ' + nome_campo + ' = ' + str(id) + ' where id = ' + str(orc_obj.id) + ';')
                    else:
                        item_obj.write(dados, context={'calculo_resumo': True})

                    item_pool.after_insert_update(cr, uid, item_obj.id)

            #
            # Calcula o percentual de acessórios
            #
            total_equipamento = 0
            if not orc_obj.percentual_acessorios:
                if orc_obj.percentual_acessorios_id:
                    orc_obj.percentual_acessorios_id.unlink()
                    #orc_obj.percentual_acessorios_id.unlink(cr, uid)
            else:
                for locacao_obj in orc_obj.orcamento_locacao_ids:
                    if locacao_obj.orcamento_categoria_id.id in [CATEGORIA_EQUIPAMENTO_EMPRESA_ID, CATEGORIA_INFRAESTRUTURA_ID]:
                        total_equipamento += locacao_obj.vr_total_minimo

                dados = self._monta_dados_item(orc_obj, ACESSORIOS_OBJ)
                valor = total_equipamento * (orc_obj.percentual_acessorios / 100.00)
                dados['price_unit'] = valor
                dados['vr_unitario_custo'] = valor
                dados['vr_unitario_venda'] = valor
                dados['vr_unitario_minimo'] = valor
                dados['vr_unitario_margem_desconto'] = valor
                dados['product_uom_qty'] = 1
                dados['product_uos_qty'] = 1

                dados['vr_total_custo'] = valor
                dados['vr_total_minimo'] = valor
                dados['vr_total'] = valor
                dados['vr_total_margem_desconto'] = valor
                dados['margem'] = 0
                dados['discount'] = 0
                dados['usa_unitario_minimo'] = True

                if not orc_obj.percentual_acessorios_id:
                    id = item_pool.create(cr, uid, dados, context={'__copy_data_seen': True})
                    item_obj = item_pool.browse(cr, uid, id)
                    cr.execute('update sale_order set percentual_acessorios_id = ' + str(id) + ' where id = ' + str(orc_obj.id) + ';')

                else:
                    item_pool.write(cr, uid, [orc_obj.percentual_acessorios_id.id], dados)
                    item_obj = item_pool.browse(cr, uid, orc_obj.percentual_acessorios_id.id)

                contexto_novo = {
                    'company_id': item_obj.order_id.company_id.id,
                    'partner_id': item_obj.order_id.partner_id.id,
                    'operacao_fiscal_produto_id': item_obj.order_id.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': item_obj.order_id.operacao_fiscal_servico_id.id,
                    'orcamento_aprovado': item_obj.order_id.orcamento_aprovado,
                    'quantity': item_obj.product_uom_qty,
                    'pricelist': item_obj.order_id.pricelist_id.id,
                    #'shop': item_obj.order_id.shop_id,
                    'uom': item_obj.product_uom.id,
                    'force_product_uom': True,
                    'price_unit': valor,
                }

                impostos = item_pool.product_id_change(cr, uid, [item_obj.id], item_obj.order_id.pricelist_id.id, item_obj.product_id.id, item_obj.product_uom_qty, item_obj.product_uom.id, False, False, item_obj.name, item_obj.order_id.partner_id.id, False, False, item_obj.order_id.date_order, item_obj.product_packaging.id, False, False, contexto_novo)

                valores = impostos['value']
                valores['vr_unitario_custo'] = valor

                dados = {}
                for chave in valores:
                    if not isinstance(valores[chave], DicionarioBrasil):
                        dados[chave] = valores[chave]

                item_pool.write(cr, uid, [item_obj.id], dados, context={'calculo_resumo': True})

                    #orc_obj.percentual_acessorios_id.write(dados, context={'calculo_resumo': True})

                #item_pool.after_insert_update(cr, uid, item_obj.id)

    def action_wait(self, cr, uid, ids, context={}):
        #print('vai fazer')
        #
        # Antes de confirmar a liberação do pedido, verificamos as validações de permissão
        # da locação e venda
        #
        self.valida_aprovacao_locacao(cr, uid, ids, context=context)
        self.valida_aprovacao_venda(cr, uid, ids, context=context)

        res = super(sale_order, self).action_wait(cr, uid, ids, context=context)

        self.pool.get('sale.order').imprime_pdfs_aprovacao(cr, uid, ids)
        #for o in self.browse(cr, uid, ids):
            #if not o.order_line:
                #raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which has no line.'))
            #if (o.order_policy == 'manual'):
                #self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            #else:
                #self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            #self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
            #message = _("The quotation '%s' has been converted to a sales order.") % (o.name,)
            #self.log(cr, uid, o.id, message)

        #res = True
        #print('já fez')

        for orc_obj in self.browse(cr, uid, ids):
            if not orc_obj.order_line:
                continue

            #
            # Replica os itens para a tabela de itens aprovados
            #
            item_pool = self.pool.get('sale.order.line')
            item_aprovado_pool = self.pool.get('sale.order.line.aprovado')
            for item_obj in orc_obj.order_line:
                dados = {'item_aprovado_id': item_obj.id}
                for campo in item_pool._columns:
                    if campo in ['order_line_id', 'order_line_ids', 'property_ids', 'move_ids', 'tax_id']:
                        continue

                    if '_id' in campo or campo in ['product_uos', 'product_uom', 'product_packaging']:
                        if not getattr(item_obj, campo):
                            dados[campo] = False
                        else:
                            dados[campo] = getattr(item_obj, campo).id
                    else:
                        dados[campo] = getattr(item_obj, campo)

                item_aprovado_pool.create(cr, 1, dados)

            #self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})

            #self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])

            #message = "A proposta comercial '{pedido}' foi convertida em pedido.".format(pedido=o.name)
            #self.log(cr, uid, o.id, message)

            ##
            ## Agora, retorna os itens para edição
            ##
            #cr.execute("update sale_order_line set state = 'draft' where order_id = {order_id};".format(order_id=o.id))
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        #super(sale_order, self).cancel(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService("workflow")

        if context is None:
            context = {}

        sale_order_line_obj = self.pool.get('sale.order.line')

        proc_obj = self.pool.get('procurement.order')

        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                if pick.state not in ('draft', 'cancel', 'done'):
                    raise osv.except_osv(
                        u'Não foi possível cancelar o pedido de venda!',
                        u'É preciso cancelar ou concluir todas as ordens de entrega no estoque, vinculadas a este pedido')

                if pick.state in ('cancel', 'done'):
                    for mov in pick.move_lines:
                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        if proc_ids:
                            for proc in proc_ids:
                                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)

            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)

            sale_order_line_obj.write(cr, uid, [l.id for l in  sale.order_line],
                    {'state': 'cancel'})

            message = u"O pedido de venda '%s' foi cancelado." % sale.name

            self.log(cr, uid, sale.id, message)

        self.write(cr, uid, ids, {'state': 'cancel'})

        return True

    def action_cancel_draft(self, cr, uid, ids, *args):
        res = super(sale_order, self).action_cancel_draft(cr, uid, ids, *args)

        if res:
            for id in ids:
                cr.execute("delete from sale_order_line_aprovado where order_id = {order_id};".format(order_id=id))

        return res

    def encerrar_pedido(self, cr, uid, ids, context={}):
        #
        # Encerra o pedido e libera para o faturamento
        #
        for orc_obj in self.browse(cr, uid, ids):
            orc_obj.write({'state': 'done'})

    def forca_cancelamento(self, cr, uid, ids, context={}):
        if uid != 1:
            raise osv.except_osv(u'Erro', u'Somente o administrador tem permissão de realizar essa função!')

        #
        # Encerra o pedido e libera para o faturamento
        #
        for orc_obj in self.browse(cr, uid, ids):
            cr.execute("update sale_order set state = 'cancel' where id = " + str(orc_obj.id) + ";")

    def onchange_sale_order_original_id(self, cr, uid, ids, sale_order_original_id, context={}):
        if not sale_order_original_id:
            return {}

        sale_original_obj = self.browse(cr, uid, sale_order_original_id)

        valores = {}
        res = {'value': valores}

        valores['partner_id'] = sale_original_obj.partner_id.id
        valores['shop_id'] = sale_original_obj.shop_id.id if sale_original_obj.shop_id else False
        valores['invoiced'] = sale_original_obj.invoiced
        valores['shipped'] = sale_original_obj.shipped
        valores['company_id'] = sale_original_obj.company_id.id
        valores['pricelist_id'] = sale_original_obj.pricelist_id.id
        valores['partner_order_id'] = sale_original_obj.partner_order_id.id
        valores['partner_shipping_id'] = sale_original_obj.partner_shipping_id.id
        valores['project_id'] = sale_original_obj.project_id.id if sale_original_obj.project_id else False
        valores['orcamento_aprovado'] = sale_original_obj.orcamento_aprovado
        valores['operacao_fiscal_produto_id'] = sale_original_obj.operacao_fiscal_produto_id.id if sale_original_obj.operacao_fiscal_produto_id else False
        valores['operacao_fiscal_servico_id'] = sale_original_obj.operacao_fiscal_servico_id.id if sale_original_obj.operacao_fiscal_produto_id else False

        dados = sale_original_obj.onchange_partner_id(sale_original_obj.partner_id.id)
        valores.update(dados['value'])
        dados = sale_original_obj.onchange_hr_department_id(sale_original_obj.hr_department_id.id)
        valores.update(dados['value'])

        return res

    def aprovar_complementar(self, cr, uid, ids, context={}):
        #
        # Ao aprovar um orçamento complementar, insere os produtos novos na lista
        # de separação do estoque e no orçamento original
        #
        move_pool = self.pool.get('stock.move')
        sale_pool = self.pool.get('sale.order')
        item_pool = self.pool.get('sale.order.line')

        complementar_item_ids = {}

        for sale_obj in self.browse(cr, uid, ids):
            if not sale_obj.sale_order_original_id:
                continue

            if sale_obj.sale_order_original_id.state == 'done':
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta complementar vinculada a uma proposta original já concluída!')

            if sale_obj.sale_order_original_id.state == 'cancel':
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta complementar vinculada a uma proposta original já cancelada!')

            if sale_obj.sale_order_original_id.saldo_obra_liberado:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta complementar vinculada a uma proposta original cujo saldo da obra já tenha sido alimentado!')

            if not sale_obj.state == 'draft':
                continue

            original_obj = sale_obj.sale_order_original_id

            if not (original_obj.pdf_versao_cliente and original_obj.pdf_versao_detalhada):
                original_obj.imprime_pdfs_aprovacao()

            #
            # Guardamos os ids dos itens complementares, vamos precisar mais abaixo
            #
            complementar_item_ids[sale_obj.id] = []
            for item_obj in sale_obj.order_line:
                complementar_item_ids[sale_obj.id].append(item_obj.id)

            #
            # Agora, inserimos os itens deste orçamento no orçamento original
            #
            for item_obj in sale_obj.order_line:
                if (not item_obj.order_line_id) and (not item_obj.autoinsert):
                    novo_item_id = item_pool.copy(cr, uid, item_obj.id, default={'order_id': original_obj.id, 'order_line_id': False}, context={'complementar': True})
                    novo_item_obj = item_pool.browse(cr, uid, novo_item_id)

                    item_pool.write(cr, uid, [novo_item_id], {'order_id': original_obj.id}, context={'complementar': True})

        #
        # Verificamos agora se, durante as cópias dos itens, algum item vazou
        # para esta proposta complementar
        #
        for sale_obj in self.browse(cr, uid, ids):
            if not sale_obj.sale_order_original_id:
                continue

            if not sale_obj.state == 'draft':
                continue

            original_obj = sale_obj.sale_order_original_id

            if not (original_obj.pdf_versao_cliente and original_obj.pdf_versao_detalhada):
                original_obj.imprime_pdfs_aprovacao()

            for item_obj in sale_obj.order_line:
                if item_obj.order_line_id and item_obj.order_line_id.id not in complementar_item_ids[sale_obj.id]:
                    item_obj.write({'order_id': sale_obj.sale_order_original_id.id}, context={'complementar': True})

            #
            # Vamos a lista de separação original
            #
            separacao_original_obj = False
            for picking_obj in original_obj.picking_ids:
                if picking_obj.type == 'out':
                    separacao_original_obj = picking_obj
                    break

            if separacao_original_obj:
                for item_obj in sale_obj.order_line:
                    #
                    # Não manda acessórios e mão de obra
                    #
                    if item_obj.orcamento_categoria_id.id not in [4, 6, 9]:
                        dados = sale_pool._prepare_order_line_move(cr, uid, sale_obj, item_obj, separacao_original_obj.id, sale_obj.date_order)
                        dados['orcamento_categoria_id'] = item_obj.orcamento_categoria_id.id
                        move_pool.create(cr, uid, dados)

            sale_obj.write({'state': 'done'}, context={'complementar': True})

    def valida_aprovacao_locacao(self, cr, uid, ids, context={}):
        user_pool = self.pool.get('res.users')
        item_comissao_pool = self.pool.get('orcamento.comissao_item')
        usuario_obj = user_pool.browse(cr, 1, uid)
        nivel_usuario = usuario_obj.nivel_aprovacao_comercial or 0

        for orc_obj in self.browse(cr, uid, ids, context=context):
            if orc_obj.orcamento_aprovado != 'locacao':
                continue

            #if orc_obj.partner_vr_limite_credito <= 0 and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o crédito do cliente ainda não foi analisado, ou está indeferido!')

            #if orc_obj.pendencia_financeira and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o cliente possui pendências financeiras!')

            #if orc_obj.mensalidade_excede_limite and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o valor das mensalidades excede o limite de crédito mensal do cliente!')

            if not orc_obj.partner_id.cnpj_cpf:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o CNPJ/CPF do cliente preenchido!')

            if not orc_obj.partner_id.cep:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o CEP do cliente preenchido!')

            if not orc_obj.partner_id.numero:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o nº do endereço do cliente preenchido!')

            if orc_obj.dt_validade and orc_obj.dt_validade < str(hoje()):
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta fora do prazo de validade!')

            if not orc_obj.data_assinatura:
                raise osv.except_osv('Erro!', u'Não é possível aprovar uma proposta de locação sem a informação da data de início do serviço')

            if not orc_obj.data_inicio:
                raise osv.except_osv('Erro!', u'Não é possível aprovar uma proposta de locação sem a informação da data de início da cobrança')

            if orc_obj.data_inicio[:7] == orc_obj.data_assinatura[:7]:
                raise osv.except_osv('Erro!', u'Não é possível aprovar uma proposta de locação em que a data de início da cobrança ocorre no mesmo mê do início do serviço')

            if not orc_obj.duracao:
                raise osv.except_osv('Erro!', u'Não é possível aprovar uma proposta de locação sem a informação da duração')

            #
            # Verifica os itens de locação, analisando
            # bonificações e meses para retorno do investimento
            #
            tem_bonificacao = False
            tem_todos_bonificados = False
            for loc_obj in orc_obj.orcamento_locacao_ids:
                if loc_obj.orcamento_categoria_id.id == CATEGORIA_MAO_DE_OBRA_ID:
                    continue

                #
                # Ignora o que não tenha valor
                #
                if not loc_obj.vr_total_minimo:
                    continue

                categoria_obj = loc_obj.orcamento_categoria_id
                comissao_obj = categoria_obj.comissao_locacao_id

                #
                # Verifica se tem bonificação
                #
                if not loc_obj.vr_mensal:
                    if not tem_bonificacao:
                        tem_bonificacao = True
                        tem_todos_bonificados = True

                elif tem_bonificacao:
                    tem_todos_bonificados = False

                #
                # Analisa os meses para retorno do investimento
                #
                if (not tem_bonificacao) and loc_obj.meses_retorno_investimento:
                    #
                    # Busca o nível de acesso correspondente aos meses
                    #
                    if comissao_obj:
                        item_comissao_ids = item_comissao_pool.search(cr, uid, [('comissao_id', '=', comissao_obj.id), ('meses_retorno_investimento', '<=', loc_obj.meses_retorno_investimento)], order='meses_retorno_investimento desc')

                        if not len(item_comissao_ids):
                            raise osv.except_osv(u'Erro', u'A categoria %s tem um número de meses para retorno do investimento inválido!' % categoria_obj.nome)

                        item_comissao_obj = item_comissao_pool.browse(cr, 1, item_comissao_ids[0])

                        if item_comissao_obj.grupo_aprovacao_id and item_comissao_obj.grupo_aprovacao_id.nivel:
                            #
                            # Se o nível do usuário for menor do que o necessário
                            #
                            if item_comissao_obj.grupo_aprovacao_id.nivel > nivel_usuario:
                                raise osv.except_osv(u'Erro', u'Você não tem permissão de realizer essa operação com a categoria %s!' % categoria_obj.nome)

            if tem_bonificacao:
                if not tem_todos_bonificados:
                    raise osv.except_osv(u'Erro', u'Você precisa bonificar todas as categorias!')

                if nivel_usuario <= 1:
                    raise osv.except_osv(u'Erro', u'Você não tem permissão de realizar essa operação em orçamentos bonificados!')

    def valida_aprovacao_venda(self, cr, uid, ids, context={}):
        user_pool = self.pool.get('res.users')
        usuario_obj = user_pool.browse(cr, 1, uid)

        for orc_obj in self.browse(cr, uid, ids, context=context):
            if orc_obj.orcamento_aprovado != 'venda':
                continue

            #if orc_obj.partner_vr_limite_credito <= 0 and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o crédito do cliente ainda não foi analisado, ou está indeferido!')

            #if orc_obj.pendencia_financeira and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o cliente possui pendências financeiras!')

            #if orc_obj.mensalidade_excede_limite and not orc_obj.motivo_liberacao_venda_sem_limite:
                #raise osv.except_osv(u'Erro', u'Não é permitido aprovar a proposta, pois o valor das parcelas excede o limite de crédito mensal do cliente!')

            if not orc_obj.partner_id.cnpj_cpf:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o CNPJ/CPF do cliente preenchido!')

            if not orc_obj.partner_id.cep:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o CEP do cliente preenchido!')

            if not orc_obj.partner_id.numero:
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta sem o nº do endereço do cliente preenchido!')

            if orc_obj.dt_validade and orc_obj.dt_validade < str(hoje()):
                raise osv.except_osv(u'Erro', u'Não é permitido aprovar uma proposta fora do prazo de validade!')

            if not orc_obj.hr_department_id:
                raise osv.except_osv(u'Erro', u'Para aprovar, é obrigatório o preenchimento do campo Departamento/Posto, na aba Outras Informações, Item Referências!')

            if orc_obj.bonificacao_venda:
                #if len(orc_obj.operacao_fiscal_produto_id.user_ids):
                    #usuario_permitido = False

                    #for user_obj in orc_obj.operacao_fiscal_produto_id.user_ids:
                        #if user_obj.id == uid:
                            #usuario_permitido = True
                            #break

                    #if not usuario_permitido:
                        #raise osv.except_osv(u'Erro', u'Você não tem permissão de realizar essa operação com orçamentos bonificados!')

                if (usuario_obj.nivel_aprovacao_comercial or 0) < 5:
                    raise osv.except_osv(u'Erro', u'Você não tem permissão de realizar essa operação com orçamentos bonificados!')

        return True

    def valida_criacao_alteracao(self, cr, uid, ids, dados):
        user_pool = self.pool.get('res.users')
        usuario_obj = user_pool.browse(cr, 1, uid)
        nivel_usuario = usuario_obj.nivel_aprovacao_comercial or 0

        #
        # Valida que vendedores e líderes de unidade não podem salvar proposta sem informar o valor de backup
        #
        if 'produto_chip_id' in dados and dados['produto_chip_id']:
            #
            # Na inclusão
            #
            if not ids:
                if 'qtd_becape_chip' not in dados or 'vr_becape_chip' not in dados or (not dados['qtd_becape_chip']) or (not dados['vr_becape_chip']):
                    #
                    # Somente de gerentes pra cima podem salvar proposta sem valor no backup
                    #
                    if nivel_usuario < 3:
                        raise osv.except_osv(u'Erro', u'Você não tem permissão de criar/salvar esta proposta, sem informar a quantidade e o valor do backup!')
            else:
                if ('qtd_becape_chip' in dados and (not dados['qtd_becape_chip'])) or ('vr_becape_chip' in dados and (not dados['vr_becape_chip'])):
                    #
                    # Somente de gerentes pra cima podem salvar proposta sem valor no backup
                    #
                    if nivel_usuario < 3:
                        raise osv.except_osv(u'Erro', u'Você não tem permissão de criar/salvar esta proposta, sem informar a quantidade e o valor do backup!')
        elif ids:
            if ('qtd_becape_chip' in dados and (not dados['qtd_becape_chip'])) or ('vr_becape_chip' in dados and (not dados['vr_becape_chip'])):
                #
                # Somente de gerentes pra cima podem salvar proposta sem valor no backup
                #
                if nivel_usuario < 3:
                    raise osv.except_osv(u'Erro', u'Você não tem permissão de criar/salvar esta proposta, sem informar a quantidade e o valor do backup!')

        #
        # Valida que vendedores e líderes de unidade, não podem salvar proposta com
        # monitoramento eletrônico a menos de R$ 70,00
        #
        if 'monitoramento_eletronico' in dados and dados['monitoramento_eletronico']:
            if dados['monitoramento_eletronico'] < 70 and nivel_usuario < 3:
                raise osv.except_osv(u'Erro', u'Você não tem permissão de criar/salvar esta proposta, com valor de monitoramento eletrônico abaixo de R$ 70,00!')


    def onchange_bonificacao_venda(self, cr, uid, ids, bonificacao_venda, company_id):
        res = {}
        valores = {}
        res['value'] = valores

        company_pool = self.pool.get('res.company')
        operacao_pool = self.pool.get('sped.operacao')

        if bonificacao_venda:
            #bonificacao_ids = operacao_pool.search(cr, uid, [('bonifica_pedido', '=', True)])

            #if len(bonificacao_ids):
            valores['operacao_fiscal_produto_id'] = 163
            valores['operacao_fiscal_ids'] = [163, 419]

        else:
            operacoes = company_pool.read(cr, uid, [company_id], ['operacao_id', 'operacao_pessoa_fisica_id', 'operacao_ativo_id', 'operacao_faturamento_antecipado_id'])

            if len(operacoes):
                operacao_fiscal_produto_id = operacoes[0]['operacao_id'][0]
                valores['operacao_fiscal_produto_id'] = operacao_fiscal_produto_id

                valores['operacao_fiscal_ids'] = []

                if operacoes[0]['operacao_id'][0]:
                    valores['operacao_fiscal_ids'].append(operacoes[0]['operacao_id'][0])
                if operacoes[0]['operacao_pessoa_fisica_id'][0]:
                    valores['operacao_fiscal_ids'].append(operacoes[0]['operacao_pessoa_fisica_id'][0])
                if operacoes[0]['operacao_ativo_id'][0]:
                    valores['operacao_fiscal_ids'].append(operacoes[0]['operacao_ativo_id'][0])
                if operacoes[0]['operacao_faturamento_antecipado_id'][0]:
                    valores['operacao_fiscal_ids'].append(operacoes[0]['operacao_faturamento_antecipado_id'][0])

        return res

    def lista_itens_rateio_desconto(self, cr, uid, sale_obj):
        itens_rateio = []
        vr_total_rateio_desconto = D(0)

        for item_obj in sale_obj.order_line:
            if not getattr(item_obj, 'usa_unitario_minimo', False):
                if item_obj.vr_total_venda_impostos:
                    if item_obj.orcamento_categoria_id and item_obj.orcamento_categoria_id.id not in [CATEGORIA_ACESSORIOS_ID, CATEGORIA_MAO_DE_OBRA_ID]:
                        itens_rateio.append(item_obj)
                        vr_total_rateio_desconto += D(item_obj.vr_total_venda_impostos)

        vr_total_rateio_desconto = vr_total_rateio_desconto.quantize(D('0.01'))

        return itens_rateio, vr_total_rateio_desconto

    def simula_parcelas(self, cr, uid, ids, context={}):
        for orc_obj in self.pool.get('sale.order').browse(cr, uid, ids):
            texto_mao_obra = u''
            texto_equipamento = u''
            parcela_excede_limite = False
            motivo_liberacao_venda_sem_limite = u''

            valor_mao_obra = D(0)
            for item_obj in orc_obj.order_line:
                if item_obj.orcamento_categoria_id.id == 6:
                    valor_mao_obra += D(item_obj.vr_total_venda_impostos or 0)

            entrada_mao_obra = D(orc_obj.mao_de_obra_instalacao_valor_entrada or 0)
            entrada_equipamento = D(orc_obj.valor_entrada or 0)
            data_base = hoje()

            if entrada_mao_obra > 0 or entrada_equipamento > 0:
                data_base += relativedelta(days=+10)

            parcelas_mao_obra = []
            if orc_obj.mao_de_obra_instalacao_payment_term_id:
                condicao_obj = orc_obj.mao_de_obra_instalacao_payment_term_id
                texto_mao_obra += u'\nParcelamento da mão-de-obra\n'
                texto_mao_obra += u'Parcela | Vencimento |    Valor\n'

                valor = valor_mao_obra
                parcelas_mao_obra = condicao_obj.calcula(valor, entrada=entrada_mao_obra, data_base=data_base)

                i = 1
                total = D(0)
                for parcela in parcelas_mao_obra:
                    texto_mao_obra += '  ' + str(i).zfill(3) + '   | '
                    texto_mao_obra += formata_data(parcela.data) + ' | '
                    texto_mao_obra += formata_valor(parcela.valor).rjust(10)
                    total += parcela.valor
                    texto_mao_obra += '\n'
                    i += 1

                    if parcela.valor > orc_obj.partner_vr_limite_credito:
                        parcela_excede_limite = True

                if len(parcelas_mao_obra) == 1:
                    if str(parcelas_mao_obra[0].data)[:10] == orc_obj.date_order:
                        parcela_excede_limite = False
                        motivo_liberacao_venda_sem_limite = u'Venda com parcela a vista'

                texto_mao_obra += '        |            | ----------\n'
                texto_mao_obra += '                       '
                texto_mao_obra += formata_valor(total).rjust(10)
                texto_mao_obra += '\n'


            if len(parcelas_mao_obra):
                data_base = parcelas_mao_obra[-1].data

            parcelas_venda = []
            if orc_obj.payment_term:
                condicao_obj = orc_obj.payment_term
                texto_equipamento += u'\nParcelamento dos equipamentos\n'
                texto_equipamento += u'Parcela | Vencimento |    Valor\n'

                valor = D(orc_obj.vr_total_venda_impostos or 0)
                #parcelas = condicao_obj.calcula(valor, entrada=entrada_equipamento + entrada_mao_obra, data_base=data_base)
                valor -= valor_mao_obra
                parcelas = condicao_obj.calcula(valor, entrada=entrada_equipamento, data_base=data_base)

                total = D(0)
                j = 1
                for i in range(len(parcelas)):
                    parcela = parcelas[i]

                    #if i < len(parcelas_mao_obra):
                        #parcela_mao_obra = parcelas_mao_obra[i]

                        #if parcela.valor > parcela_mao_obra.valor:
                            #total += parcela.valor - parcela_mao_obra.valor
                        #else:
                            #total -= parcela.valor
                            #parcela.valor = 0

                        #if parcela.valor > parcela_mao_obra.valor:
                            #parcelas_venda.append([parcela.data, parcela.valor - parcela_mao_obra.valor])

                            #texto_equipamento += '  ' + str(j).zfill(3) + '   | '
                            #texto_equipamento += formata_data(parcela.data) + ' | '
                            #texto_equipamento += formata_valor(parcela.valor - parcela_mao_obra.valor).rjust(10)
                            #texto_equipamento += '\n'
                            #j += 1

                    #else:
                    if True:
                        texto_equipamento += '  ' + str(j).zfill(3) + '   | '
                        texto_equipamento += formata_data(parcela.data) + ' | '
                        texto_equipamento += formata_valor(parcela.valor).rjust(10)
                        texto_equipamento += '\n'
                        total += parcela.valor
                        parcelas_venda.append([parcela.data, parcela.valor])
                        j += 1

                        if parcela.valor > orc_obj.partner_vr_limite_credito:
                            parcela_excede_limite = True

                texto_equipamento += '        |            | ----------\n'
                texto_equipamento += '                       '
                texto_equipamento += formata_valor(total).rjust(10)
                texto_equipamento += '\n'

                if len(parcelas) == 1 and (not parcela_excede_limite):
                    if str(parcelas[0].data)[:10] == orc_obj.date_order:
                        parcela_excede_limite = False
                        motivo_liberacao_venda_sem_limite = u'Venda com parcela a vista'

            dados = {
                'simulacao_parcelas': texto_equipamento + texto_mao_obra,
                'parcela_excede_limite': parcela_excede_limite,
                'motivo_liberacao_venda_sem_limite': motivo_liberacao_venda_sem_limite,
            }

            orc_obj.write(dados)

        return parcelas_venda

    def onchange_partner_id(self, cr, uid, ids, partner_id, context={}):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id:
            return res

        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

        #if partner_obj.finan_contrato_ativo_ids:
            #contrato_obj = partner_obj.finan_contrato_ativo_ids[0]

            #if getattr(contrato_obj, 'hr_department_id', False):
                #res['value']['hr_department_id'] = contrato_obj.hr_department_id.id

            #if getattr(contrato_obj, 'vendedor_id', False):
                #res['value']['user_id'] = contrato_obj.vendedor_id.id

            #if getattr(contrato_obj, 'grupo_economico_id', False):
                #res['value']['grupo_economico_id'] = contrato_obj.grupo_economico_id.id

            #if getattr(contrato_obj, 'res_partner_category_id', False):
                #res['value']['res_partner_category_id'] = contrato_obj.res_partner_category_id.id

        #else:

        if getattr(partner_obj, 'user_id', False):
            res['value']['user_id'] = partner_obj.user_id.id

        if getattr(partner_obj, 'hr_department_id', False):
            res['value']['hr_department_id'] = partner_obj.hr_department_id.id

            #if partner_obj.hr_department_id.manager_id:
                #res['value']['user_id'] = partner_obj.hr_department_id.manager_id.id

        if getattr(partner_obj, 'grupo_economico_id', False):
            res['value']['grupo_economico_id'] = partner_obj.grupo_economico_id.id

        if getattr(partner_obj, 'partner_category_id', False):
            res['value']['res_partner_category_id'] = partner_obj.partner_category_id.id

        if 'bonificacao_venda' in context and context['bonificacao_venda']:
            res['value']['operacao_fiscal_ids'] = [419, 163]

        elif 'company_id' in context:
            operacoes = []

            company_obj = self.pool.get('res.company').browse(cr, 1, context['company_id'])

            if company_obj.operacao_id:
                operacoes.append(company_obj.operacao_id.id)

            if company_obj.operacao_pessoa_fisica_id:
                operacoes.append(company_obj.operacao_pessoa_fisica_id.id)

            if company_obj.operacao_ativo_id:
                operacoes.append(company_obj.operacao_ativo_id.id)

            if company_obj.operacao_faturamento_antecipado_id:
                operacoes.append(company_obj.operacao_faturamento_antecipado_id.id)

            res['value']['operacao_fiscal_ids'] = operacoes

        return res

    def onchange_user_id(self, cr, uid, ids, user_id, context={}):
        if not user_id:
            return {}

        #
        # Verifica se o vendedor a ser definido na proposta é o vendedor que está
        # inserindo a proposta
        #
        if user_id != uid:
            raise osv.except_osv(u'Aviso!', u'Você não é o gestor de contas responsável pelo atendimento a esse cliente ou ao posto a que pertence o cliente. Caso você não tenha permissão de gerente de contas, não prossiga com a inclusão da proposta, e verifique justo a gerência qual o procedimento a ser adotado!')

    def recalcula(self, cr, uid, ids, context={}):
        for sale_order_obj in self.pool.get('sale.order').browse(cr, 1, ids):
            ##
            ## Ajustamos o usuário pra ser o dono do cliente
            ##
            #if sale_order_obj.partner_id.user_id:
                #uid = sale_order_obj.partner_id.user_id.id

            locacao_ids = self.pool.get('orcamento.orcamento_locacao').search(cr, uid, [('sale_order_id', 'in', [sale_order_obj.id])])

            self.pool.get('orcamento.orcamento_locacao').write(cr, uid, locacao_ids, {'recalculo': int(random.random() * 100000000)})

            self.pool.get('sale.order').write(cr, uid, [sale_order_obj.id], {'recalculo': int(random.random() * 100000000)})

        return {'value': {}, 'message': u'Recalculado!'}

    def action_libera_faturamento(self, cr, uid, ids, context={}):
        ids_para_liberar = []

        for order_obj in self.pool.get('sale.order').browse(cr, uid, ids):
            if order_obj.orcamento_aprovado == 'venda' and order_obj.state == 'manual':
                #
                # Verifica se o vendedor a ser definido na proposta é o vendedor que é o dono
                # do cliente/carteira
                #
                if order_obj.partner_id.user_id and order_obj.partner_id.user_id.id != order_obj.user_id.id:
                    raise osv.except_osv(u'Aviso!', u'O gestor de contas vinculado à proposta não é o gestor de contas da carteira do cliente; somente será permitido liberar o faturamento caso o gestor de contas seja alterado para “%s”!' % order_obj.partner_id.user_id.name)

                ids_para_liberar.append(order_obj.id)

        #print('ids_para_liberar')
        #print(ids_para_liberar)
        self.pool.get('sale.order').encerrar_pedido(cr, uid, ids_para_liberar)

        return {}

    def onchange_hr_department_id(self, cr, uid, ids, hr_department_id):
        res = {}
        valores = {}
        res['value'] = valores

        #if not hr_department_id:
            #return

        #posto_pool = self.pool.get('hr.department')
        #posto_obj = posto_pool.browse(cr, uid, hr_department_id)

        #if posto_obj.manager_id and posto_obj.manager_id.user_id:
            #valores['user_id'] = posto_obj.manager_id.user_id.id

        return res

    def imprime_pdfs_aprovacao(self, cr, uid, ids, context={}):
        import os
        import base64
        from finan.wizard.finan_relatorio import Report, JASPER_BASE_DIR

        for ped_obj in self.browse(cr, uid, ids):
            #
            # Versão que foi para o cliente
            #
            rel = Report(u'Orçamento - versão cliente', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_cliente.jrxml')
            nome_arq = u'orcamento_cliente_' + ped_obj.name.strip() + u'.pdf'
            rel.parametros['REGISTRO_IDS'] = '(' +  str(ped_obj.id) + ')'
            pdf, formato = rel.execute()

            dados = {
                'nome_pdf_versao_cliente': nome_arq,
                'pdf_versao_cliente': base64.encodestring(pdf)
            }

            #
            # Versão detalhada - uso interno
            #
            rel = Report(u'Orçamento - versão detalhada', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_detalhado.jrxml')
            rel.parametros['REGISTRO_IDS'] = '(' +  str(ped_obj.id) + ')'
            nome_arq = u'orcamento_detalhado_' + ped_obj.name.strip() + u'.pdf'
            pdf, formato = rel.execute()

            dados['nome_pdf_versao_detalhada'] = nome_arq
            dados['pdf_versao_detalhada'] = base64.encodestring(pdf)

            #
            # Mão-de-obra
            #
            rel = Report(u'Orçamento - mão-de-obra', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_mao_obra.jrxml')
            rel.parametros['REGISTRO_IDS'] = '(' +  str(ped_obj.id) + ')'
            nome_arq = u'mao_de_obra_' + ped_obj.name.strip() + u'.pdf'
            pdf, formato = rel.execute()

            dados['nome_pdf_mao_de_obra'] = nome_arq
            dados['pdf_versao_mao_de_obra'] = base64.encodestring(pdf)

            ped_obj.write(dados, context={'complementar': True})

    def migrar_mao_de_obra(self, cr, uid, ids, context={}):
        for locacao_obj in self.browse(cr, uid, ids):
            if locacao_obj.orcamento_aprovado != 'locacao':
                raise osv.except_osv(u'Erro', u'Não é permitido migrar a mão-de-obra de uma proposta de venda!')

            if not locacao_obj.proposta_venda_id:
                raise osv.except_osv(u'Erro', u'Não é permitido migrar a mão-de-obra sem informar a proposta de venda!')

            #
            # Primeiro, desativa os itens que são inseridos automaticamente
            #
            locacao_obj.remove_automatico_itens()

            #
            # Agora, vamos vincular os itens de mão de obra na proposta de venda
            #
            for item_obj in locacao_obj.order_line:
                if item_obj.orcamento_categoria_id.id == 6:
                    item_obj.write({'order_id': locacao_obj.proposta_venda_id.id})

            locacao_obj.proposta_venda_id.write({'recalculo': int(random.random() * 100000000)})
            locacao_obj.write({'recalculo': int(random.random() * 100000000)})

        return True

    def preencher_checklist(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('checklist.contrato.item')

        for sale_obj in self.pool.get('sale.order').browse(cr, uid, ids):
            if sale_obj.checklist_ids:
                raise osv.except_osv(u'Erro', u'Não é permitido alterar o checklist; exclua primeiro os itens de checklist existentes!')

            if not sale_obj.checklist_id:
                raise osv.except_osv(u'Aviso', u'Selecione primeiro um modelo de checklist para preencher!')

            for item_obj in sale_obj.checklist_id.item_ids:
                item_pool.copy(cr, uid, item_obj.id, {'sale_order_id': sale_obj.id, 'clecklist_id': False})

        return True

    def imprimir_checklist(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            sl.id,
            sl.name as numero,
            rp.name as cliente,
            cci.ordem as ordem,
            cci.atividade as descricao,
            cci.data_conclusao as data_conclusao,
            cci.cargo as cargo,
            ru.name as usuario,
            cci.obs

            from sale_order sl
            checklist_contrato_item cci on cci.sale_order_id = sl.id
            join sale_order sl on sl.id = cci.sale_order_id
            join res_partner rp on rp.id = sl.partner_id
            left join res_users ru on ru.id = cci.user_id

            where
            sl.id =  """ + str(rel_obj.id)

        rel = Report('Relatório de Checklist Proposta Comercial', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_contrato_relatorio_checklist.jrxml')
        rel.parametros['SQL'] = sql
        rel.parametros['UID'] = uid

        nome = 'CHECKLIST_' + rel_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'sale.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def abre_oportunidade(self, cr, uid, ids, context={}):
        lead_pool = self.pool.get('crm.lead')

        res = {
            'type': 'ir.actions.act_window',
            'name': u'Oportunidade',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'view_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm', 'crm_case_form_view_oppor')[1],
            'target': 'inline',  # Abre na mesma janela, sem ser no meio da tela
        }

        for sale_obj in self.browse(cr, uid, ids):
            if not sale_obj.crm_lead_id:
                dados = {
                    'partner_id': sale_obj.partner_id.id,
                    'name': u'Proposta ' + sale_obj.name,
                    'user_id': sale_obj.user_id.id,
                    'partner_address_id': sale_obj.partner_order_id.id if sale_obj.partner_order_id else False,
                    'section_id': sale_obj.section_id.id if sale_obj.section_id else False,
                    'categ_id': sale_obj.categ_id.id if sale_obj.categ_id else False,
                    'data_prospeccao': sale_obj.date_order,
                    'ref': 'sale.order,' + str(sale_obj.id),
                    'type': 'opportunity',
                    'planned_revenue': sale_obj.vr_mensal,
                    'receita_venda': sale_obj.vr_total_venda_impostos,
                    'state': 'draft',
                }
                crm_lead_id = lead_pool.create(cr, uid, dados)
                dados = lead_pool.onchange_partner_id(cr, uid, [crm_lead_id], sale_obj.partner_id.id, False)
                lead_pool.write(cr, uid, [crm_lead_id], dados['value'])
                dados = lead_pool.onchange_partner_address_id(cr, uid, [crm_lead_id], sale_obj.partner_order_id.id, False)
                lead_pool.write(cr, uid, [crm_lead_id], dados['value'])
                sale_obj.write({'crm_lead_id': crm_lead_id})

            else:
                crm_lead_id = sale_obj.crm_lead_id.id

            res['res_id'] = crm_lead_id

            if 'salvando' in context:
                return

            return res


sale_order()



class sale_order_line_aprovado(osv.Model):
    _name = 'sale.order.line.aprovado'
    _inherit = 'sale.order.line'

    def _descricao(self, cr, uid, ids, nome_campo, arg, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids, context=context):
            descricao = ''

            if item_obj.product_id:
                descricao = getattr(item_obj.product_id, 'nome_generico', '')

                if not descricao:
                    descricao = item_obj.product_id.name or ''

            if item_obj.order_line_id:
                descricao += ' [ '

                if hasattr(item_obj.order_line_id.product_id, 'nome_generico') and getattr(item_obj.order_line_id.product_id, 'nome_generico', False):
                    descricao += item_obj.order_line_id.product_id.nome_generico
                else:
                    descricao += item_obj.order_line_id.product_id.name
                descricao += ' ]'

            res[item_obj.id] = descricao

        return res

    _columns = {
        'item_aprovado_id': fields.many2one('sale.order.line', u'Item aprovado'),
        'name': fields.function(_descricao, string=u'Descrição', type='char', size=256, select=True, store=True),
    }

    #
    # Desabilita possíveis validações ao criar, gravar ou excluir um item
    #
    def create(self, cr, uid, dados, context={}):
        super(osv.Model, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        super(osv.Model, self).write(cr, uid, ids, dados, context=context)

    def unlink(self, cr, uid, ids, context={}):
        super(osv.Model, self).unlink(cr, uid, ids, context=context)
