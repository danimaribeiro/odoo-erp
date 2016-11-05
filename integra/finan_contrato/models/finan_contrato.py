# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia, agora, formata_data, data_por_extenso
from pybrasil.valor import formata_valor


NATUREZA = (
    ('R', 'Receber'),
    ('P', 'Pagar'),

    ('PP', 'Parcelamento a Pagar'),
    ('RP', 'Parcelamento a Receber'),

    ('PR', 'Renegociação a Pagar'),
    ('RR', 'Renegociação a Receber'),

    ('IR', 'Inclusão de contrato a Receber'),
    ('IP', 'Inclusão de contrato a Pagar'),
    ('RI', 'Recebimento de imoveis'),

    ('TR', 'Terceirizado a Receber'),
)

DIAS_VENCIMENTO = [
    [ '1', ' 1'],
    [ '2', ' 2'],
    [ '3', ' 3'],
    [ '4', ' 4'],
    [ '5', ' 5'],
    [ '6', ' 6'],
    [ '7', ' 7'],
    [ '8', ' 8'],
    [ '9', ' 9'],
    ['10', '10'],
    ['11', '11'],
    ['12', '12'],
    ['13', '13'],
    ['14', '14'],
    ['15', '15'],
    ['16', '16'],
    ['17', '17'],
    ['18', '18'],
    ['19', '19'],
    ['20', '20'],
    ['21', '21'],
    ['22', '22'],
    ['23', '23'],
    ['24', '24'],
    ['25', '25'],
    ['26', '26'],
    ['27', '27'],
    ['28', '28'],
    ['29', '29'],
    ['30', '30']
]


class finan_contrato(osv.Model):
    _description = u'Contrato'
    _name = 'finan.contrato'
    _inherit = 'mail.thread'

    def monta_nome(self, cr, uid, id):
        contrato_obj = self.browse(cr, uid, id)
        partner_pool = self.pool.get('res.partner')

        nome = contrato_obj.numero + ' - '
        partner_nome = contrato_obj.partner_id.name_get()
        nome += partner_nome[0][1]

        nome += ' - '
        nome += contrato_obj.company_id.name or ''

        if contrato_obj.valor_mensal:
            nome += ' - R$ ' + formata_valor(contrato_obj.valor_mensal)

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res.append((id, self.monta_nome(cr, uid, id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('numero', 'ilike', texto),
            ('partner_id', 'ilike', texto)
        ]

        return procura

    def _get_carencia_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.carencia_texto:
                res[contrato_obj.id] = int(contrato_obj.carencia_texto)
            else:
                res[contrato_obj.id] = 0

        return dict(res)

    def _get_carencia_dias_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.carencia_dias_texto:
                res[contrato_obj.id] = int(contrato_obj.carencia_dias_texto)
            else:
                res[contrato_obj.id] = 0

        return dict(res)

    def _gerou_lancamentos(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            res[contrato_obj.id] = len(contrato_obj.lancamento_ids)

        return res

    def _valor_faturamento(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            soma = D(0)
            for itens_obj in contrato_obj.contrato_produto_ids:
                if not itens_obj.data:
                    valor = D(str(itens_obj.quantidade)) * D(str(itens_obj.vr_unitario))
                    soma += valor.quantize(D('0.01'))

            res[contrato_obj.id] = soma.quantize(D('0.01'))

        return res

    def _faturamento_diferente(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            res[contrato_obj.id] = contrato_obj.valor_faturamento != contrato_obj.valor_mensal
            #vm = D(0)
            #soma = D(0)
            #for itens_obj in contrato_obj.contrato_produto_ids:
                #valor = D(str(itens_obj.quantidade)) * D(str(itens_obj.vr_unitario))
                #soma += valor.quantize(D('0.01'))
            #soma = soma.quantize(D('0.01'))

            #if contrato_obj.valor_mensal:
                #vm = D(str(contrato_obj.valor_mensal))
                #vm = vm.quantize(D('0.01'))

            ##print(soma, vm)


        return res

    def _ano_vencimento(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for contrato in self.browse(cursor, user_id, ids):
            if contrato.data_renovacao:
                retorno[contrato.id] = contrato.data_renovacao[:4]
            else:
                retorno[contrato.id] = ''

        return retorno

    def _ano_mes_vencimento(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for contrato in self.browse(cursor, user_id, ids):
            if contrato.data_renovacao:
                retorno[contrato.id] = contrato.data_renovacao[:7]
            else:
                retorno[contrato.id] = ''

        return retorno

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.cnpj_cpf:
                res[obj.id] = obj.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict'),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', relation='res.company', string=u'Empresa mãe', store=True),

        'cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'CNPJ/CPF', store=True),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True),

        'nome': fields.function(_get_nome_funcao, type='char', size=256, string=u'Contrato', fnct_search=_procura_nome),
        'numero': fields.char(u'Número', size=30),
        'ativo': fields.boolean(u'Ativo?'),
        'suspenso': fields.boolean(u'Suspenso (financeiro)?'),
        'partner_id': fields.many2one('res.partner', u'Parceiro', ondelete='restrict'),

        'partner_municipio_id': fields.related('partner_id', 'municipio_id', type='many2one', relation='sped.municipio', string=u'Município do cliente', store=True),
        'partner_bairro': fields.related('partner_id', 'bairro', type='char', string=u'Bairro do cliente', store=True),

        'data_assinatura': fields.date(u'Data de início do serviço'),
        'data_distrato': fields.date(u'Data de distrato'),

        'contrato_antigo_ids': fields.many2many('finan.contrato', 'finan_contrato_antigo', 'contrato_id', 'antigo_id', string=u'Contratos antigos'),

        'data_inicio': fields.date(u'Data do primeiro vencimento após o início do serviço'),
        'duracao': fields.integer(u'Duração em meses'),
        'carencia_texto': fields.char(u'Carência em meses', size=5),
        'carencia': fields.function(_get_carencia_funcao, type='integer', string=u'Carência em meses', store=True),
        'carencia_dias_texto': fields.char(u'Carência em dias', size=5),
        'carencia_dias': fields.function(_get_carencia_dias_funcao, type='integer', string=u'Carência em dias', store=True),
        'dia_vencimento': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento'),
        'tipo_valor_base': fields.selection((('M', 'Mensal'), ('T', 'Total')), u'Valor base é '),
        'valor_mensal': CampoDinheiro(u'Valor mensal'),
        'valor': CampoDinheiro(u'Valor total'),
        'data_reajuste': fields.date(u'Data de reajuste'),
        'data_encerramento': fields.date(u'Data de término pro-rata'),
        'obs': fields.text(u'Observações'),
        'res_partner_address_id': fields.many2one('res.partner.address', u'Endereço de cobrança', ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', ondelete='restrict'),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira', ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio', ondelete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict'),
        'nf_sem_boleto': fields.boolean(u'Emitir a NFS-e/Recido de locação sem o boleto vinculado?'),
        'operacao_fiscal_produto_id': fields.many2one('sped.operacao', u'Operação fiscal para produtos', ondelete='restrict'),
        'operacao_fiscal_servico_id': fields.many2one('sped.operacao', u'Operação fiscal para serviços', ondelete='restrict'),
        'natureza': fields.selection(NATUREZA, u'Natureza'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
        'pro_rata': fields.boolean('Pro-rata?'),
        'provisionado': fields.boolean(u'Provisionar lançamentos?'),
        'res_currency_id': fields.many2one('res.currency', u'Índice para reajuste', ondelete='restrict'),
        #'motivo_distrato': fields.text(u'Motivo do distrato'),
        'motivo_distrato_id': fields.many2one('finan.motivo_distrato', u'Motivo do distrato', ondelete='restrict'),

        'data_renovacao': fields.date(u'Data de renovação'),
        'ano_mes_renovacao': fields.function(_ano_mes_vencimento, string=u'Mês de renovação', method=True, type='char', store=True),
        'ano_renovacao': fields.function(_ano_vencimento, string=u'Ano de renovação', method=True, type='char', store=True),

        'lancamento_ids': fields.one2many('finan.lancamento', 'contrato_id', u'Lançamentos financeiros', ondelete='cascade'),
        'lancamento_parcelado_id': fields.many2one('finan.lancamento', u'Lançamentos parcelado', ondelete='cascade'),

        'contrato_produto_ids': fields.one2many('finan.contrato_produto', 'contrato_id', u'Produtos e serviços (todos)', ondelete="cascade"),
        'contrato_produto_mensal_ids': fields.one2many('finan.contrato_produto', 'contrato_id', u'Produtos e serviços (mensais)', ondelete="cascade", domain=[['data', '=', False]]),
        'contrato_produto_eventual_ids': fields.one2many('finan.contrato_produto', 'contrato_id', u'Produtos e serviços (eventuais)', ondelete="cascade", domain=[['data', '!=', False]]),
        'contrato_inventario_ids': fields.one2many('finan.contrato_inventario', 'contrato_id', u'Inventário no cliente', ondelete="cascade"),
        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'finan.contrato')], ondelete="cascade"),
        'municipio_id': fields.many2one('sped.municipio', u'Município do fato gerador', ondelete='restrict'),
        'gerou_lancamentos': fields.function(_gerou_lancamentos, type='integer', string=u'Gerou os lançamentos?', store=True),
        'valor_faturamento': fields.function(_valor_faturamento, type='float', string=u'Valor faturamento?', store=True),
        'faturamento_diferente': fields.function(_faturamento_diferente, type='boolean', string=u'Faturamento diferente?', store=True),

        'diferenca_meses_referencia': fields.integer(u'Mês de referência (-1 = anterior, 0 = o mesmo, 1 = próximo)'),

        'sale_order_id': fields.many2one('sale.order', u'Orçamento', select=True, ondelete='restrict'),
        'vendedor_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'endereco_prestacao_id': fields.many2one('res.partner.address', u'Endereço de prestação', ondelete='restrict'),
        'res_partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelete='restrict'),

        'motivo_baixa_id': fields.many2one('finan.motivobaixa', u'Motivo para a bonificação do pro-rata', select=True),
        'sensores': fields.integer(u'Sensores'),
    }

    #_sql_constraints = [
        #('company_numero_unique', 'unique(company_id, numero, natureza)',
            #u'O número do contrato/parcelamento não pode se repetir!'),
    #]

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'finan.contrato', context=context),
        'ativo': True,
        'suspenso': False,
        'natureza': 'R',
        'pro_rata': False,
        'provisionado': True,
        'tipo_valor_base': 'M',
        'data_assinatura': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_inicio': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        #'numero': lambda self, cr, uid, context: self.ultimo_numero(cr, uid, context),
        'dia_vencimento': '5',
        'diferenca_meses_referencia': -1,
        'carencia_texto': '0',
        'carencia_dias_texto': '0',
    }

    _rec_name = 'nome'
    _order = 'company_id, numero'


    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores

        company_pool = self.pool.get('res.company')
        company_obj = company_pool.browse(cr, uid, company_id)

        if company_obj.partner_id:
            valores['raiz_cnpj'] = company_obj.raiz_cnpj
            #valores['cnpj_cpf'] = company_obj.partner_id.cnpj_cpf
        else:
            raise osv.except_osv(u'Inválido !', u'Não existe Cnpj/Cpf na Empresa selecionada!')

        return retorno

    def nada(self, cr, uid, ids, context={}):
        return True

    def ultimo_numero(self, cr, uid, company_id, context):
        if not context:
            return ''

        if (not 'natureza' in context):
            return ''

        if context['natureza'] != 'R' and context['natureza'] != 'IR' and context['natureza'] != 'RI' and context['natureza'] != 'TR':
            return ''

        #cr.execute("select coalesce(max(numero), '') from finan_contrato where natureza = 'R' and company_id = " + str(company_id) + ';')
        cr.execute("select coalesce(max(numero), '') from finan_contrato where natureza = '{natureza}';".format(natureza=context['natureza']))
        ultimo_numero = cr.fetchone()[0]

        if '-' in ultimo_numero:
            ano, numero = ultimo_numero.split('-')
            try:
                numero = str(int(numero) + 1)
            except:
                numero = '1'
        else:
            ano = str(datetime.now().year)
            numero = '1'

        if ano != str(datetime.now().year):
            ano = str(datetime.now().year)
            numero = '1'

        return ano + '-' + numero.zfill(4)

    def ajusta_data_inicio_carencia_renovacao(self, contrato_obj, forca_proximo_periodo=None):
        #
        # Na data de início, a data informada pode ser a de início real do contrato
        # nesse caso, buscar uma data de início em que o período de duração esteja
        # do mês atual em diante
        #
        data_inicio = parse_datetime(contrato_obj.data_inicio).date()

        #
        # Não é mais necessário ajustar a data de início da cobrança, o que o usuário
        # informar é o real do início da cobrança
        #
        ###
        ### Caso o dia de vencimento seja menor do que o dia do início, força a data de início da cobrança
        ### para o mês seguinte
        ###
        ##if contrato_obj.dia_vencimento == '30' and data_inicio.month == 2:
            ##contrato_obj.dia_vencimento = '28'

        ##data_vencimento = date(data_inicio.year, data_inicio.month, int(contrato_obj.dia_vencimento))
        ##if int(contrato_obj.dia_vencimento) < data_inicio.day:
            ##data_vencimento += relativedelta(months=+1)

        ##data_inicio = data_vencimento

        if forca_proximo_periodo:
            hoje = parse_datetime(forca_proximo_periodo).date()
        else:
            #hoje = datetime.now().date()
            hoje = parse_datetime('2016-06-01').date()

        #print('hoje', hoje, 'forca_proximo_periodo', forca_proximo_periodo)
        carencia = contrato_obj.carencia
        ciclos = 0

        if contrato_obj.natureza in ('R', 'P', 'TR') and data_inicio <= hoje:
            #
            # Vamos ver quantos meses tem de diferença entre a data de início e a data
            # de hoje; se houver menos do que os meses de duração do contrato, assume
            # a data de início real
            #
            meses = idade_meses_sem_dia(data_inicio, hoje)
            #meses = ((hoje.year - data_inicio.year) * 12) + hoje.month - data_inicio.month

            #
            # Exemplo, data_inicio = 2009-04-01, hoje = 2014-02-25
            # meses = 63
            # duracao = 36
            # ciclos = 63 // 36 = 1 -> Se passou 1 ciclo de vencimento
            #
            ciclos = meses // contrato_obj.duracao

            data_inicio = data_inicio + relativedelta(months=+(ciclos * contrato_obj.duracao))

            carencia = meses % contrato_obj.duracao

        #print(data_inicio, carencia, ciclos, meses)

        return data_inicio, carencia, ciclos

    def lista_vencimentos(self, contrato_obj, forca_proximo_periodo=None):
        lista_venc = []

        data_inicio, carencia, renovacao = self.ajusta_data_inicio_carencia_renovacao(contrato_obj, forca_proximo_periodo)
        dia_vencimento = int(contrato_obj.dia_vencimento)

        pro_rata = 0
        if contrato_obj.pro_rata:
            pro_rata = 1

        #for i in range(0, contrato_obj.duracao + pro_rata):
        for i in range(0, contrato_obj.duracao):
            data_vencimento = data_inicio + relativedelta(months=+i, day=dia_vencimento)

            lista_venc += [data_vencimento]

        return lista_venc[carencia:]

    def pro_rata(self, contrato_obj, termino=False, forca_proximo_periodo=None):
        if termino:
            data_base = parse_datetime(contrato_obj.data_encerramento).date()
        else:
            data_base = parse_datetime(contrato_obj.data_assinatura).date()

        primeiro_dia = primeiro_dia_mes(data_base)
        ultimo_dia = ultimo_dia_mes(data_base)

        dias_no_mes = ultimo_dia - primeiro_dia
        dias_no_mes = dias_no_mes.days + 1
        if termino:
            dias_periodo = data_base - primeiro_dia
            dias_periodo = dias_periodo.days + 1
        else:
            dias_periodo = ultimo_dia - data_base
            dias_periodo = dias_periodo.days + 1 # conta junto a data base

        pro_rata = D(str(dias_periodo)) / D(str(dias_no_mes))

        return pro_rata

    def gera_provisao(self, cr, uid, ids, context={}):
        for contrato_obj in self.browse(cr, uid, ids, context=context):
            #
            # Exclui as provisões anteriores
            #
            forca_proximo_periodo = context.get('forca_proximo_periodo', None)

            if forca_proximo_periodo:
                data_inicio, carencia, renovacao = self.ajusta_data_inicio_carencia_renovacao(contrato_obj, forca_proximo_periodo)

            else:
                self.exclui_provisao_renovacao_alteracao(cr, uid, ids, context)
                data_inicio, carencia, renovacao = self.ajusta_data_inicio_carencia_renovacao(contrato_obj)

            dados = {
                'company_id': contrato_obj.company_id.id,
                'tipo': contrato_obj.natureza[0],  # Primeira letra do tipo P/R
                'contrato_id': contrato_obj.id,
                'provisionado': contrato_obj.provisionado,
                'conta_id': contrato_obj.conta_id.id,
                'documento_id': contrato_obj.documento_id.id,
                'res_partner_bank_id': contrato_obj.res_partner_bank_id.id,
                'sugestao_bank_id': contrato_obj.res_partner_bank_id.id,
                'centrocusto_id': contrato_obj.centrocusto_id.id,
                'partner_id': contrato_obj.partner_id.id,
                'res_partner_address_id': contrato_obj.res_partner_address_id.id,
                'formapagamento_id': contrato_obj.formapagamento_id.id,
                'historico': contrato_obj.obs,

                #
                # Dados necessários para controle de documentos a receber ou a pagar
                #
                #'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                #'numero_documento': fields.char(u'Número do documento', size=30),
                'data_documento': str(data_inicio),

                #
                # Boletos
                #
                'carteira_id': contrato_obj.carteira_id.id,
                'historico': contrato_obj.obs,
            }

            if contrato_obj.lancamento_parcelado_id:
                dados['historico'] = contrato_obj.lancamento_parcelado_id.historico

                if contrato_obj.lancamento_parcelado_id.sugestao_bank_id:
                    dados['sugestao_bank_id'] = contrato_obj.lancamento_parcelado_id.sugestao_bank_id.id

                if len(contrato_obj.lancamento_parcelado_id.rateio_ids):
                    rateio_ids = []
                    for rateio_obj in contrato_obj.lancamento_parcelado_id.rateio_ids:
                        novo_rateio = {}
                        for campo in rateio_obj._all_columns:
                            if campo == 'lancamento_id':
                                continue

                            novo_rateio[campo] = getattr(rateio_obj, campo, False)

                            if campo.endswith('_id'):
                                if novo_rateio[campo]:
                                    novo_rateio[campo] = novo_rateio[campo].id
                                else:
                                    novo_rateio[campo] = False

                            #print(campo)
                            if campo == 'valor_documento' or campo == 'valor':
                                #print('zerou')
                                novo_rateio[campo] = D(0)

                        rateio_ids.append((0, False, novo_rateio))

                    dados['rateio_ids'] = rateio_ids

            #
            # Cria as novas provisões
            #
            parcela = 1 + carencia
            vencimentos = self.lista_vencimentos(contrato_obj, forca_proximo_periodo)

            total_parcelas = len(vencimentos) + carencia

            diferenca_primeira_parcela = D('0')
            diferenca_ultima_parcela = D('0')
            if contrato_obj.tipo_valor_base == 'M':
                valor_mensal = D(str(contrato_obj.valor_mensal))

            else:
                valor_mensal = D(str(contrato_obj.valor)) / D(str(total_parcelas))
                valor_mensal = valor_mensal.quantize(D('0.01'))
                valor = valor_mensal * D(str(total_parcelas))

                #
                # Centavos a mais vão na primeira parcela, a menos na última
                #
                if D(str(contrato_obj.valor)) > valor:
                    diferenca_primeira_parcela = D(str(contrato_obj.valor)) - valor
                else:
                    diferenca_ultima_parcela = D(str(contrato_obj.valor)) - valor

            #if (not contrato_obj.pro_rata) and contrato_obj.carencia_dias:
                #data_base = data_inicio
                #data_carencia = data_base + timedelta(days=contrato_obj.carencia_dias)
                #data_carencia = data_carencia.toordinal()
                #data_base = data_base.toordinal()
                #dias_no_mes = ultimo_dia_mes(data_base) - primeiro_dia_mes(data_base)
                #dias_no_mes = dias_no_mes.days + 1
                #proporcao_carencia_dias = D(str(contrato_obj.carencia_dias)) / dias_no_mes
                #diferenca_primeira_parcela -= valor_mensal * proporcao_carencia_dias

            valor = 0
            for data_vencimento in vencimentos:
                dados['valor_documento'] = valor_mensal

                if contrato_obj.natureza == 'P':
                    data_doc = data_vencimento + relativedelta(months=(contrato_obj.diferenca_meses_referencia or -1))
                    #print(data_doc, data_vencimento)
                    dados['data_documento'] = data_doc.strftime('%Y-%m-%d')

                #
                # Se o contrato for pelo valor total, ver se tem diferença a acrescentar
                # na primeira parcela
                #
                if parcela == 1:
                    dados['valor_documento'] += diferenca_primeira_parcela
                elif parcela == len(vencimentos):
                    dados['valor_documento'] += diferenca_ultima_parcela

                dados['numero_documento'] = contrato_obj.numero.strip()
                dados['numero_documento'] += '-' + str(renovacao + 1).zfill(2)
                dados['numero_documento'] += '-' + str(parcela).zfill(2)
                dados['numero_documento'] += '/' + str(total_parcelas).zfill(2)
                dados['numero_documento_original'] = dados['numero_documento']
                dados['data_vencimento'] = data_vencimento.strftime('%Y-%m-%d')
                dados['data_vencimento_original'] = data_vencimento.strftime('%Y-%m-%d')

                #
                # Calcula o pro-rata do 1º mês
                #
                #print(renovacao, parcela)

                if contrato_obj.pro_rata and renovacao == 0:
                    if parcela == 1:
                        pro_rata = self.pro_rata(contrato_obj)
                    #elif parcela == len(vencimentos):
                        #pro_rata = self.pro_rata(contrato_obj, termino=True)
                    else:
                        pro_rata = 1

                    dados['valor_documento'] = D(str(contrato_obj.valor_mensal)) * pro_rata

                valor += dados['valor_documento']
                dados['valor_original_contrato'] = contrato_obj.valor_mensal

                #
                # Verifica se já não tem um lançamento, quitado ou com nota emitida
                #
                #sql_ja_existe = '''
                #select l.id from finan_lancamento l where
                #l.contrato_id = {contrato_id}
                #and l.numero_documento_original = '{numero_documento_original}';
                #'''.format(**dados)
                #cr.execute(sql_ja_existe)
                #ja_existe_ids = cr.fetchall()

                busca_ja_existe = [
                    #('company_id', '=', dados['company_id']),
                    #('tipo', '=', dados['tipo']),
                    ('contrato_id', '=', dados['contrato_id']),
                    #('partner_id', '=', dados['partner_id']),
                    ('numero_documento_original', '=', dados['numero_documento_original']),
                ]

                ja_existe_ids = self.pool.get('finan.lancamento').search(cr, 1, busca_ja_existe)
                #print(dados['numero_documento_original'], len(ja_existe_ids), ja_existe_ids)
                if len(ja_existe_ids) == 0:
                    lancamento_id = self.pool.get('finan.lancamento').create(cr, uid, dados)

                    if 'centrocusto_id' in dados and dados['centrocusto_id']:
                        lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id)

                        contexto_rateio = {
                            'contrato_id': contrato_obj.id,
                        }

                        if contrato_obj.hr_department_id:
                            contexto_rateio['hr_department_id'] = contrato_obj.hr_department_id.id

                        rateio = lancamento_obj.onchange_centrocusto_id(dados['centrocusto_id'], dados['valor_documento'], 0, dados['company_id'], dados['conta_id'], dados['partner_id'], dados['data_vencimento'], dados['data_documento'], context=contexto_rateio)
                        if 'value' in rateio:
                            rateio_ids = [[5, False, False]]
                            for rat in rateio['value']['rateio_ids']:
                                rateio_ids.append([0, False, rat])

                            lancamento_obj.write({'rateio_ids': rateio_ids})

                parcela += 1

            self.write(cr, uid, [contrato_obj.id], {'valor': valor, 'valor_mensal': valor_mensal})

            #
            # Trata agora o pro-rata do final do mês de pro-rata;
            # exemplo, contrato começa no dia 11/09/2015, pro-rata termina
            # no dia 11/10/2015; o sistema vai gerar a 1ª parcela proporcional, que será
            # bonificada,
            #
            if contrato_obj.pro_rata:
                if contrato_obj.data_encerramento[:8] != contrato_obj.data_assinatura[:8]:
                    if not contrato_obj.motivo_baixa_id:
                        raise osv.except_osv(u'Aviso!', u'Para contratos com pro-rata de mais de 1 mês, é obrigatório o motivo da bonificação das primeiras parcelas antes do término do pro-rata. Contrato ' + contrato_obj.numero)

                    if not contrato_obj.contrato_produto_mensal_ids:
                        raise osv.except_osv(u'Aviso!', u'Para contratos com pro-rata de mais de 1 mês, é obrigatória a informação dos produtos a serem faturados. Contrato ' + contrato_obj.numero)

                vencimento_final_prorata = parse_datetime(contrato_obj.data_encerramento).date()
                vencimento_final_prorata += relativedelta(day=1)
                vencimento_final_prorata += relativedelta(months=+1)

                parcela = 0 + carencia
                for data_vencimento in vencimentos:
                    if str(data_vencimento)[:7] > str(vencimento_final_prorata)[:7]:
                        break

                    if contrato_obj.data_encerramento[:8] == contrato_obj.data_assinatura[:8]:
                        if not contrato_obj.motivo_baixa_id:
                            break

                    parcela += 1

                    dados['numero_documento'] = contrato_obj.numero.strip()
                    dados['numero_documento'] += '-' + str(renovacao + 1).zfill(2)
                    dados['numero_documento'] += '-' + str(parcela).zfill(2)
                    dados['numero_documento'] += '/' + str(total_parcelas).zfill(2)
                    dados['numero_documento_original'] = dados['numero_documento']

                    busca_ja_existe = [
                        ('contrato_id', '=', contrato_obj.id),
                        ('numero_documento_original', '=', dados['numero_documento_original']),
                    ]

                    ja_existe_ids = self.pool.get('finan.lancamento').search(cr, 1, busca_ja_existe)

                    if not ja_existe_ids:
                        continue

                    #
                    # Parcelas antes do final do pro-rata, bonifica
                    #
                    if str(data_vencimento)[:8] < str(vencimento_final_prorata)[:8]:
                        self.pool.get('finan.lancamento').write(cr, uid, ja_existe_ids, {'data_baixa': contrato_obj.data_assinatura, 'motivo_baixa_id': contrato_obj.motivo_baixa_id.id, 'provisionado': False})

                    #
                    # Parcela no final do pro-rata, bonifica parcial através do item eventual
                    # de faturamento
                    #
                    else:
                        #
                        # Verifica se já tem itens eventuais para o vencimento; se tiver, ignora
                        #
                        itens_eventuais_ids = self.pool.get('finan.contrato_produto').search(cr, uid, [('contrato_id', '=', contrato_obj.id), ('data', '=', str(data_vencimento)[:10])])

                        if itens_eventuais_ids:
                            continue

                        vencimento_final_prorata = parse_datetime(contrato_obj.data_encerramento).date()
                        dias_no_mes = ultimo_dia_mes(vencimento_final_prorata).day
                        dias = vencimento_final_prorata.day
                        proporcao = D(dias) / D(dias_no_mes)

                        itens_desconto = []

                        for produto_obj in contrato_obj.contrato_produto_mensal_ids:
                            dados = {
                                'contrato_id': contrato_obj.id,
                                'data': data_vencimento,
                                'product_id': produto_obj.product_id.id,
                                'quantidade': produto_obj.quantidade or 1,
                                'vr_unitario': D(produto_obj.vr_unitario or 0) * proporcao * -1,
                            }

                            dados['vr_unitario'] = dados['vr_unitario'].quantize(D('0.01'))

                            itens_desconto.append([0, False, dados])

                        self.write(cr, uid, [contrato_obj.id], {'contrato_produto_ids': itens_desconto})

            if str(data_inicio) != contrato_obj.data_inicio:
                self.write(cr, uid, [contrato_obj.id], {'data_renovacao': str(data_inicio)})

    def exclui_provisao_distrato(self, cr, uid, ids, context=None):
        for contrato_obj in self.browse(cr, uid, ids, context=context):
            #
            # A data de vencimento do pro-rata do distrato deve ser a do mês
            # subsequente ao do mês do distrato!!!!
            #
            # Exclui as provisões após a data do distrato,
            # e transforma a última parcela no valor pro-rata
            # do ultimo vencimento até o dia do distrato
            #
            #
            data_vencimento_distrato = parse_datetime(contrato_obj.data_distrato).date()
            data_vencimento_distrato += relativedelta(day=int(contrato_obj.dia_vencimento))
            data_vencimento_distrato += relativedelta(months=+1)
            data_vencimento_distrato = str(data_vencimento_distrato)

            #print('data_vencimento_distrato')
            #print(data_vencimento_distrato)

            vencimento_anterior = None
            vencimento_posterior = None
            vencimento_distrato = None
            distrato_efetivado = False
            for lancamento_obj in contrato_obj.lancamento_ids:
                if lancamento_obj.data_vencimento_original == data_vencimento_distrato:
                    if not lancamento_obj.provisionado:
                        distrato_efetivado = True
                    else:
                        vencimento_distrato = lancamento_obj

            numero_distrato = contrato_obj.numero.strip() + '-distrato'

            #
            # Dias do período do distrato
            #
            dias_periodo = parse_datetime(contrato_obj.data_distrato).date().day
            ultimo_dia = ultimo_dia_mes(contrato_obj.data_distrato).day
            valor_diario = D(str(contrato_obj.valor_mensal)) / D(ultimo_dia)
            valor_parcela_distrato = valor_diario * D(str(dias_periodo))
            valor_parcela_distrato = valor_parcela_distrato.quantize(D('0.01'))

            if (not distrato_efetivado) and vencimento_distrato:
                dados = {
                    'numero_documento': numero_distrato,
                    'valor_documento': valor_parcela_distrato,
                }
                vencimento_distrato.write(dados)

            #
            # Exclui agora todos os vencimentos posteriores ao distrato
            #
            for lancamento_obj in contrato_obj.lancamento_ids:
                if lancamento_obj.provisionado and lancamento_obj.data_vencimento_original > data_vencimento_distrato:
                    lancamento_obj.unlink()

    def exclui_provisao_renovacao_alteracao(self, cr, uid, ids, context=None):
        for contrato_obj in self.browse(cr, uid, ids, context=context):
            #
            # Exclui os lançamentos não pagos e não faturados, ainda em provisão
            #
            for lancamento_obj in contrato_obj.lancamento_ids:
                if lancamento_obj.tipo == 'R' and lancamento_obj.provisionado and (not lancamento_obj.sped_documento_id) and (not lancamento_obj.nosso_numero):
                    lancamento_obj.unlink()
                elif lancamento_obj.tipo == 'P' and (not lancamento_obj.sped_documento_id) and lancamento_obj.situacao in ('A vencer', 'Vencido', 'Vence hoje'):
                    lancamento_obj.unlink()

    def create(self, cr, uid, dados, context={}):
        if ('numero' not in dados) or (not dados['numero']):
            dados['numero'] = self.ultimo_numero(cr, uid, dados['company_id'], context)

        res = super(finan_contrato, self).create(cr, uid, dados, context)

        if 'data_distrato' in dados and dados['data_distrato']:
            self.exclui_provisao_distrato(cr, uid, [res], context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if 'numero' in dados and (not dados['numero'] or dados['numero'].strip() == ''):
            contrato_obj = self.browse(cr, uid, ids[0])
            if 'company_id' in dados:
                company_id = dados['company_id']
            else:
                company_id = contrato_obj.company_id.id

            dados['numero'] = self.ultimo_numero(cr, uid, company_id, context)

        res = super(finan_contrato, self).write(cr, uid, ids, dados, context)

        if 'data_distrato' in dados and dados['data_distrato']:
            self.exclui_provisao_distrato(cr, uid, ids, context)

        if 'lancamento_ids' not in dados:
            contrato_obj = self.browse(cr, uid, ids[0])
            if not contrato_obj.gerou_lancamentos:
                return {'warning': u'Você não gerou os lançamentos financeiros do contrato!'}

        return res

    def gera_provisao_wizard(self, cr, uid, ids, context=None):
        resposta = self.gera_provisao(cr, uid, ids, context)

        if 'lancamento_id' in context:
            lancamento_id = context['lancamento_id']
            dados = {
                'data_baixa': date.today().strftime('%Y-%m-%d'),
                'motivo_baixa': 'Lançamento baixado devido a parcelamento',
            }

            self.pool.get('finan.lancamento').write(cr, uid, [lancamento_id], dados, context)

        return resposta

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            contrato_id = ids[0]

        if not contrato_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'finan', 'finan_nota_wizard')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'finan.nota',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'finan.contrato', 'active_ids': [contrato_id]},
        }

        return retorno

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        original_obj = self.browse(cr, uid, id)

        if original_obj.natureza == 'R':
            if not context:
                context = {}

            context['natureza'] = 'R'

            default.update({
                'numero': self.ultimo_numero(cr, uid, original_obj.company_id.id, context),
                'lancamento_ids': [],
                'contrato_inventario_ids': [],
                'mail_message_ids': [],
            })

        else:
            default.update({
                'numero': '',
                'lancamento_ids': []
            })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res

    def onchange_data_assinatura(self, cr, uid, ids, data_assinatura, duracao=None):
        valores = {}
        retorno = {'value': valores}
        valores['data_inicio'] = data_assinatura

        if duracao:
            data_assinatura = datetime.strptime(data_assinatura[:10], '%Y-%m-%d').date()
            data_renovacao = data_assinatura + relativedelta(months=duracao)
            valores['data_renovacao'] = data_renovacao.strftime('%Y-%m-%d')

        return retorno

    def gera_todas_parcelas(self, cr, uid, ids, context={}):
        contrato_pool = self.pool.get('finan.contrato')
        lancamento_pool = self.pool.get('finan.lancamento')

        if 'active_ids' in context:
            ids = context.get('active_ids', [])

        contrato_ids = self.search(cr, uid, [('ativo', '=', True),('id', 'in', ids)], order='numero')

        i = 1
        for contrato_obj in contrato_pool.browse(cr, uid, contrato_ids):
            if contrato_obj.data_distrato:
                continue

            if contrato_obj.natureza == 'RI':
                continue

            #
            # Aprovar contrato
            #
            if contrato_obj.natureza == 'IR':
                contrato_obj.write({'natureza': 'R', 'numero': contrato_pool.ultimo_numero(cr, uid, contrato_obj.company_id.id, {'natureza': 'R'})})

            #
            # Ajusta o nº de controle da parcela do contrato, para os lançamentos
            # que não estão mais provisionados
            #
            for lancamento_obj in contrato_obj.lancamento_ids:
                if lancamento_obj.provisionado:
                    continue

                idade_parcela = idade_meses_sem_dia(contrato_obj.data_inicio, lancamento_obj.data_vencimento_original or lancamento_obj.data_vencimento) + 1
                ciclo = (idade_parcela // contrato_obj.duracao) + 1
                parcelas_no_ciclo = contrato_obj.duracao

                #if ciclo == 1 and contrato_obj.pro_rata:
                    #parcelas_no_ciclo = contrato_obj.duracao + 1
                    #parcela_no_ciclo = idade_parcela % (contrato_obj.duracao + 1)

                    #if parcela_no_ciclo == 0:
                        #parcela_no_ciclo = contrato_obj.duracao + 1
                        #ciclo -= 1

                #else:
                parcela_no_ciclo = idade_parcela % contrato_obj.duracao

                if parcela_no_ciclo == 0:
                    parcela_no_ciclo = contrato_obj.duracao
                    ciclo -= 1

                numero_documento_original = contrato_obj.numero.strip()
                numero_documento_original += '-' + str(ciclo).zfill(2)
                numero_documento_original += '-' + str(parcela_no_ciclo).zfill(2)
                numero_documento_original += '/' + str(parcelas_no_ciclo).zfill(2)

                #print(lancamento_obj.data_vencimento_original or lancamento_obj.data_vencimento, ciclo, parcela_no_ciclo, parcelas_no_ciclo, lancamento_obj.numero_documento_original)

                if lancamento_obj.numero_documento_original != numero_documento_original:
                    lancamento_obj.write({'numero_documento_original': numero_documento_original})

            contrato_obj.gera_provisao(context=context)
            c_obj = contrato_pool.browse(cr, uid, contrato_obj.id)
            ultimo_vencimento_id = lancamento_pool.search(cr, uid, [('contrato_id', '=', c_obj.id)], order='data_vencimento_original desc, data_vencimento desc')
            ultimo_vencimento = lancamento_pool.browse(cr, uid, ultimo_vencimento_id[0])
            data_ultimo_vencimento = parse_datetime(ultimo_vencimento.data_vencimento_original or ultimo_vencimento.data_vencimento)
            data_ultimo_vencimento = data_ultimo_vencimento + relativedelta(months=+1)
            contrato_obj.gera_provisao(context={'forca_proximo_periodo': data_ultimo_vencimento})
            #print('gerou provisao', id, i, len(ids), data_ultimo_vencimento)
            i += 1
            cr.commit()

        return False

    def acao_demorada_ajusta_parcelas_contratos(self, cr, uid, ids=[], context={}):
        if len(ids) == 0:
            sql = """
select
    c.id,
    count(l.id)
from
    finan_contrato c
    left join finan_lancamento l on l.contrato_id = c.id
where
    c.data_distrato is null
    and c.natureza = 'R'
group by
    c.id
having
    count(l.id) < 6;
            """
            cr.execute(sql)
            for id, contagem in cr.fetchall():
                ids.append(id)
            #ids = self.pool.get('finan.contrato').search(cr, uid, [('data_distrato', '=', False), ('natureza', '=', 'R')])

        self.pool.get('finan.contrato').gera_todas_parcelas(cr, uid, ids)


    def ajuste_conta_financeira(self, cr, uid, ids, context=None):
        if not len(ids):
            return {}

        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.conta_id.id:

                conta_id = contrato_obj.conta_id.id
                contrato_id = contrato_obj.id

                for lanc_obj in contrato_obj.lancamento_ids:

                    sql = """
                    update finan_lancamento set conta_id = {conta_id}
                    where id = {lancamento_id}
                    and contrato_id = {contrato_id}
                    """
                    sql = sql.format(conta_id=conta_id, lancamento_id=lanc_obj.id,contrato_id=contrato_id)
                    #print(sql)
                    cr.execute(sql)

        return

    def onchange_partner_id(self, cr, uid, ids, partner_id, context={}):
        res = {}
        res['value'] = {}

        if not partner_id:
            return res

        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

        if getattr(partner_obj, 'hr_department_id', False):
            res['value']['hr_department_id'] = partner_obj.hr_department_id.id

        if getattr(partner_obj, 'grupo_economico_id', False):
            res['value']['grupo_economico_id'] = partner_obj.grupo_economico_id.id

        if getattr(partner_obj, 'partner_category_id', False):
            res['value']['res_partner_category_id'] = partner_obj.partner_category_id.id

        return res


    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        modelo_pool = self.pool.get('lo.modelo')

        for contrato_obj in self.browse(cr, uid, ids):
            modelos_objs = modelo_pool.search(cr, uid, [('tabela','=','finan.contrato')])

            for modelo_obj in modelo_pool.browse(cr, uid, modelos_objs):
                dados = {
                    'finan_contrato_obj': contrato_obj,
                    'cliente_obj': contrato_obj.partner_id,
                    'comprador_obj': contrato_obj.partner_id,
                }

                variaveis = {
                }

                nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                nome_arquivo += '_' + contrato_obj.numero

                attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.contrato'), ('res_id', '=', contrato_obj.id), ('name', 'like', nome_arquivo)])
                attachment_pool.unlink(cr, uid, attachment_ids)

                nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                nome_arquivo += '.'
                nome_arquivo += modelo_obj.formato or 'doc'

                arquivo = modelo_obj.gera_modelo(dados,formato=modelo_obj.formato, novas_variaveis=variaveis)

                dados = {
                    'datas': arquivo,
                    'name': nome_arquivo,
                    'datas_fname': nome_arquivo,
                    'res_model': 'finan.contrato',
                    'res_id': contrato_obj.id,
                    'file_type': 'application/msword',
                }
                attachment_pool.create(cr, uid, dados)

        return


finan_contrato()


class finan_contrato_produto(osv.Model):
    _description = u'Itens do contrato'
    _name = 'finan.contrato_produto'

    def _vr_total(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(0)

            valor = D(item_obj.quantidade or 0)
            valor *= D(item_obj.vr_unitario or 0)
            valor = valor.quantize(D('0.01'))

            res[item_obj.id] = valor

        return res

    _columns = {
        'data': fields.date(u'Data', select=True),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="cascade"),
        'product_id': fields.many2one('product.product', u'Produto/serviço', required=True, ondelete='restrict'),
        'res_partner_address_id': fields.many2one('res.partner.address', u'Endereço de prestação', ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'quantidade': CampoQuantidade(u'Quantidade'),
        'vr_unitario': CampoValorUnitario(u'Valor unitário'),
        'vr_total': fields.function(_vr_total, type='float', string=u'Valor total', digits=(18,2)),
    }

    _defaults = {
        'quantidade': 1,
    }

    def onchange_quantidade_vr_unitario(self, cr, uid, ids, quantidade, vr_unitario, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        valor = D(quantidade or 0)
        valor *= D(vr_unitario or 0)
        valor = valor.quantize(D('0.01'))

        valores['vr_total'] = valor

        return res

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []

        res = []
        for produto_obj in self.browse(cr, uid, ids):
            nome = u''
            if produto_obj.product_id and produto_obj.product_id.name:
                nome = produto_obj.product_id.name or u''

            res.append((produto_obj.id, nome))

        return res

    def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=100):
        produto_ids = self.search(cr, uid, [('product_id.name', 'ilike', name)], limit=limit, context=context)

        return self.name_get(cr, uid, produto_ids, context=context)


finan_contrato_produto()


class finan_contrato_inventario(osv.Model):
    _description = u'Produtos do contrato'
    _name = 'finan.contrato_inventario'

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="cascade"),
        'product_id': fields.many2one('product.product', u'Produto/serviço', required=True, ondelete='restrict'),
        'data': fields.date(u'Data'),
        'quantidade': CampoQuantidade(u'Quantidade'),
        'vr_unitario': CampoValorUnitario(u'Valor unitário'),
        'vr_total': CampoDinheiro(u'Valor total'),
        #'standard_price': fields.related('product_id', 'standard_price', type='float', string=u'Preço de custo', relation='product.product', store=True),
    }


finan_contrato_inventario()
