# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, hoje, formata_data, ultimo_dia_mes, idade_meses
from pybrasil.valor import formata_valor
import numpy
import regex


TIPO_TAXA = [
    ('0', u'Juros simples'),
    ('1', u'Juros compostos'),
    ('2', u'Tabela price'),
]

JUROS_SIMPLES = '0'
JUROS_COMPOSTOS = '1'
TABELA_PRICE = '2'

TIPO_MES = [
    ('001', u'Todo mês (mensal)'),
    ('002', u'A cada 2 meses (bimestral)'),
    ('003', u'A cada 3 meses (trimestral)'),
    ('006', u'A cada 6 meses (semestral)'),
    ('012', u'A cada ano (anual)'),
    ('024', u'A cada 2 anos (bienal)'),
    ('060', u'A cada 5 anos (qüinqüenal)'),
]


class Parcela(object):
    def __init__(self, *args, **kwargs):
        self.data = kwargs.get('data', None)
        self.valor = D(kwargs.get('valor', 0))
        self.valor_original = D(kwargs.get('valor_original', 0))
        self.juros = D(kwargs.get('juros', 0))
        self.amortizacao = D(kwargs.get('amortizacao', 0))
        self.divida_amortizada = D(kwargs.get('divida_amortizada', 0))
        self.saldo_devedor = D(kwargs.get('saldo_devedor', 0))

    def __repr__(self):
        return str(self.data) + '; ' + str(self.valor)


class account_payment_term(osv.osv):
    _name = 'account.payment.term'
    #_inherit = 'account.payment.term'
    _description = u'Condições de pagamento'

    _columns = {
        'name': fields.char(u'Condição de pagamento', size=64, translate=False, required=True),
        'active': fields.boolean(u'Ativa', help=u'Se a condição de pagamento estiver inativa, ela irá ser escondida da seleção.'),
        'note': fields.text(u'Descrição', translate=False),
        'line_ids': fields.one2many('account.payment.term.line', 'payment_id', u'Parcelas'),
        'taxa_juros': fields.float(string=u'Taxa de Juros', digits=(18, 5)),
        'tipo_taxa': fields.selection(TIPO_TAXA, string=u'Tipo de juros'),
        'tipo_mes': fields.selection(TIPO_MES, string=u'Período'),
        #'valor_teto': fields.float(string=u'Valor teto para uso'),
        #'juros_montante': fields.boolean(u'Juros global?'),
        #'juros_composto': fields.boolean(u'Juros compostos?'),

        'taxa_administracao': fields.float(u'Taxa de administração'),
        'taxa_abertura_credito': fields.float(u'Tarifa de abertura de crédito (TAC)'),
        'taxa_iof': fields.float(u'Alíquota do IOF'),

        'valor_minimo': fields.float(u'Valor mínimo', digits=(18,2)),
    }

    _defaults = {
        'active': True,
        #'tipo_taxa': JUROS_COMPOSTOS,
        'tipo_mes': '001',
        #'juros_montante': True,
        #'juros_composto': True,
    }

    _order = 'name'

    def gerar_meses(self, cr, uid, ids, context={}):
        PARCELA_DIAS = regex.compile(r'.*((([0-9]+))\/?)+.*')
        PARCELA_VEZES = regex.compile(r'.*([Xx×]).*')
        LIMPA = regex.compile(r'[^0-9]')
        item_pool = self.pool.get('account.payment.term.line')

        for condicao_obj in self.browse(cr, uid, ids, context=context):
            #if not (PARCELA_DIAS.match(condicao_obj.name) or PARCELA_VEZES.match(condicao_obj.name)):
                #continue

            for linha_obj in condicao_obj.line_ids:
                linha_obj.unlink()

            periodo = int(condicao_obj.tipo_mes or '001')

            match = PARCELA_VEZES.match(condicao_obj.name)

            #print(PARCELA_DIAS.match(condicao_obj.name), match)

            #print(match)

            if match is None:
                match = PARCELA_DIAS.match(condicao_obj.name)

                if match is None:
                    continue

                dias = condicao_obj.name.split('/')
                #print('dias', dias)
                total = len(dias)
                i = 1
                for dia in dias:
                    dia = LIMPA.sub('', dia)

                    dados = {
                        'payment_id': condicao_obj.id,
                        'sequence': i,
                        'name': str(i) + u'ª parcela',
                        'value': 'divisao',
                        'days': int(dia),
                        'multiplica': 1,
                        'divide': total,
                        'meses': 0
                    }

                    i += 1

                    if i > total:
                        dados['value'] = 'balance'

                    item_pool.create(cr, uid, dados)

            else:
                match = PARCELA_VEZES.match(condicao_obj.name)
                divisor = match.group(1)
                partes = unicode(condicao_obj.name).split(divisor)

                if ' ' in partes[0]:
                    partes = partes[0].split(' ')
                else:
                    partes = [partes[0]]

                vezes = partes[-1]
                #print(vezes, 'vezes')
                vezes = int(vezes)

                for i in range(1, vezes + 1):
                    dados = {
                        'payment_id': condicao_obj.id,
                        'sequence': i,
                        'name': str(i) + u'ª parcela',
                        'value': 'divisao',
                        'days': 0,
                        'multiplica': 1,
                        'divide': vezes,
                        'meses': i * periodo,
                    }

                    if i == vezes:
                        dados['value'] = 'balance'

                    #print(dados)

                    item_pool.create(cr, uid, dados)

        return True

    ###def gera_parcelas(self, cr, uid, ids, context={}):
        ###valores = {}
        ###retorno = {'value': valores}
        ###lb_pool = self.pool.get('account.payment.term.line')

        ###for cp_obj in self.browse(cr, uid, ids):
            ###if not len(cp_obj.line_ids):
                ###continue

            ###i = 0
            ###for line_obj in cp_obj.line_ids:
                ###if i == 0:
                    ###i += 1
                    ###continue

                ###line_obj.unlink()

            ###lb_obj = cp_obj.line_ids[0]

            ###vezes = lb_obj.divide or 1
            ###tamanho = len(str(vezes))

            ###vezes -= 1

            ###lb_obj.write({'name': u'1'.zfill(tamanho) + u'ª parcela'})
            ###dados = {
                ###'payment_id': cp_obj.id,
                ###'name': u'',
                ###'sequence': lb_obj.sequence,
                ###'value': 'divisao',
                ###'value_amount': lb_obj.value_amount,
                ###'days': lb_obj.days,
                ###'days2': lb_obj.days2,
                ###'multiplica': lb_obj.multiplica,
                ###'divide': lb_obj.divide,
            ###}

            ###if vezes > 0:
                ###for i in range(vezes):
                    ###dados['name'] = str(i+2).zfill(tamanho) + u'ª parcela'
                    ###dados['days'] = (dados['days'] or 0) + 30
                    ###dados['sequence'] += 5

                    ###if i == (vezes - 1):
                        ###dados[value] = 'balance'

                    ###lb_pool.create(cr, uid, dados)

        ###return retorno

    def compute(self, cr, uid, ids, valor, date_ref=False, entrada=0, context={}):
        if not date_ref:
            data_base = hoje()
        else:
            data_base = parse_datetime(date_ref)

        valor = D(valor).quantize(D('0.01'))
        entrada = D(entrada).quantize(D('0.01'))
        valor_original = valor - entrada
        result = []

        for condicao_obj in self.browse(cr, uid, ids, context=context):
            for parcela_obj in condicao_obj.line_ids:
                valor_parcela = D(0)

                if parcela_obj.value == 'fixed':
                    valor_parcela = D(parcela_obj.value_amount or 0)
                    valor_parcela = valor_parcela.quantize(D('0.01'))

                elif parcela_obj.value == 'procent':
                    valor_parcela = valor_original * D(parcela_obj.value_amount or 0) / D('100')
                    valor_parcela = valor_parcela.quantize(D('0.01'))

                elif parcela_obj.value == 'balance':
                    valor_parcela = valor

                elif parcela_obj.value == 'divisao':
                    valor_parcela = valor

                    if parcela_obj.divide and parcela_obj.multiplica:
                        valor_parcela = valor_original * D(parcela_obj.multiplica or 0) / D(parcela_obj.divide or 1)
                    elif parcela_obj.multiplica:
                        valor_parcela = valor_original * D(parcela_obj.multiplica or 0)
                    elif parcela_obj.divide:
                        valor_parcela = valor_original / D(parcela_obj.divide or 1)

                    valor_parcela = valor_parcela.quantize(D('0.01'))

                valor -= valor_parcela
                #print(valor_parcela, valor)

                if valor_parcela:
                    if parcela_obj.meses:
                        meses = parcela_obj.meses
                        dia_fixo = parcela_obj.days2 or 0

                        #
                        # No caso da conta em meses, colocamos o dia fixo primeiro
                        # Se o dia fixo for negativo, ele conta a partir do último dia do mês
                        #
                        data_parcela = data_base + relativedelta(months=meses)

                        if dia_fixo > 0:
                            data_parcela += relativedelta(day=dia_fixo)
                        elif dia_fixo < 0:
                            data_parcela = ultimo_dia_mes(data_parcela)

                            dia_fixo += 1  # -1 significa exatamente o último dia do mês

                            if dia_fixo < 0:
                                data_parcela += relativedelta(days=dia_fixo)

                    else:
                        #
                        # Define a data da parcela como sendo a data de referência
                        # + x dias
                        #
                        dias = parcela_obj.days or 0
                        dia_fixo = parcela_obj.days2 or 0
                        data_parcela = data_base + relativedelta(days=dias)

                        #
                        # days2 é um dia fixo do mês
                        # se o valor for negativo, conta x dias a partir do final do mês
                        #
                        if dia_fixo < 0:
                            #
                            # Pega o dia 1º do próximo mês
                            #
                            dia_primeiro = data_parcela + relativedelta(day=1, months=1)
                            data_parcela = dia_primeiro + relativedelta(days=dia_fixo)

                        #
                        # e se for positivo, é o dia x do mês seguinte
                        #
                        elif dia_fixo > 0:
                            data_parcela += relativedelta(day=dia_fixo, months=1)

                    result.append((data_parcela.strftime('%Y-%m-%d'), valor_parcela))
                    #valor -= valor_parcela

        return result

    def monta_parcela(self, condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada=0):
        parcela = Parcela()

        if parcela_obj.value == 'fixed':
            parcela.valor = D(parcela_obj.value_amount)

        elif parcela_obj.value == 'entrada':
            parcela.valor = D(entrada)

        elif parcela_obj.value == 'procent':
            parcela.valor = (valor_original - entrada) * D(parcela_obj.value_amount) / D('100')

        elif parcela_obj.value == 'balance':
            parcela.valor = valor

        elif parcela_obj.value == 'divisao':
            parcela.valor = valor
            if parcela_obj.divide and parcela_obj.multiplica:
                parcela.valor = (valor_original - entrada) * D(parcela_obj.multiplica) / D(parcela_obj.divide)
            elif parcela_obj.multiplica:
                parcela.valor = (valor_original - entrada) * D(parcela_obj.multiplica)
            elif parcela_obj.divide:
                parcela.valor = (valor_original - entrada) / D(parcela_obj.divide)

        parcela.valor = parcela.valor.quantize(D('0.01'))
        parcela.valor_original = parcela.valor.quantize(D('0.01'))

        if parcela.valor:
            if parcela_obj.meses:
                meses = parcela_obj.meses
                dia_fixo = parcela_obj.days2 or 0

                #
                # No caso da conta em meses, colocamos o dia fixo primeiro
                # Se o dia fixo for negativo, ele conta a partir do último dia do mês
                #
                data_parcela = data_base + relativedelta(months=meses)

                if dia_fixo > 0:
                    data_parcela += relativedelta(day=dia_fixo)
                elif dia_fixo < 0:
                    data_parcela = ultimo_dia_mes(data_parcela)

                    dia_fixo += 1  # -1 significa exatamente o último dia do mês

                    if dia_fixo < 0:
                        data_parcela += relativedelta(days=dia_fixo)

            else:
                #
                # Define a data da parcela como sendo a data de referência
                # + x dias
                #
                dias = parcela_obj.days or 0
                dia_fixo = parcela_obj.days2 or 0
                data_parcela = data_base + relativedelta(days=dias)

                #
                # days2 é um dia fixo do mês
                # se o valor for negativo, conta x dias a partir do final do mês
                #
                if dia_fixo < 0:
                    #
                    # Pega o dia 1º do próximo mês
                    #
                    dia_primeiro = data_parcela + relativedelta(day=1, months=1)
                    data_parcela = dia_primeiro + relativedelta(days=dia_fixo)

                #
                # e se for positivo, é o dia x do mês seguinte
                #
                elif dia_fixo > 0:
                    data_parcela += relativedelta(day=dia_fixo, months=1)

                meses = idade_meses(data_base, data_parcela)

            parcela.data = data_parcela

            if taxa_juros:
                if condicao_obj.tipo_taxa == JUROS_SIMPLES:
                    pass

                elif condicao_obj.tipo_taxa == JUROS_COMPOSTOS:
                    pass

                elif condicao_obj.tipo_taxa == TABELA_PRICE:
                    parcela.juros = condicao_obj.saldo_devedor * taxa_juros
                    parcela.juros = parcela.juros.quantize(D('0.01'))
                    parcela.amortizacao = parcela.valor - parcela.juros
                    condicao_obj.divida_amortizada += parcela.amortizacao
                    parcela.divida_amortizada = condicao_obj.divida_amortizada
                    condicao_obj.saldo_devedor -= parcela.amortizacao
                    parcela.saldo_devedor = condicao_obj.saldo_devedor
                    parcela.valor_original = parcela.amortizacao

                    #print('juros', parcela.juros)
                    #print('amortizacao', parcela.amortizacao)
                    #print('divida_amortizada', parcela.divida_amortizada)
                    #print('saldo devedor', parcela.saldo_devedor)

                #if condicao_obj.juros_composto:
                    #taxa_aplicada = (1 + taxa_juros) ** meses
                    #parcela.juros = (parcela.valor * taxa_aplicada) - parcela.valor
                    #parcela.valor *= taxa_aplicada

                #else:
                    #taxa_aplicada = taxa_juros * meses
                    #parcela.juros = parcela.valor * taxa_aplicada
                    #print(parcela.valor, parcela.juros, meses)
                    #parcela.valor += parcela.juros
                    #print(parcela.valor)

        return parcela

    def calcula(self, cr, uid, ids, valor, data_base=None, entrada=0, context={}):
        data_base = parse_datetime(data_base or hoje())
        valor_original = D(valor).quantize(D('0.01'))
        valor = D(valor).quantize(D('0.01'))
        entrada = D(entrada or 0).quantize(D('0.01'))
        #entrada = D('10000').quantize(D('0.01'))
        res = []

        for condicao_obj in self.browse(cr, uid, ids, context=context):
            taxa_administracao = valor_original * D(condicao_obj.taxa_administracao or 0) / D(100)
            taxa_administracao = taxa_administracao.quantize(D('0.01'))
            condicao_obj.saldo_devedor = D(valor or 0)
            condicao_obj.divida_amortizada = D(0)

            taxa_abertura_credito = D(0)
            taxa_iof = D(0)

            taxa_juros = D(condicao_obj.taxa_juros or 0) / D(100)

            ###
            ### Juro anual
            ###
            ##if condicao_obj.tipo_taxa == JUROS_SIMPLES:
                ##if condicao_obj.juros_composto:
                    ###
                    ### Converte para uma taxa mensal equivalente
                    ###
                    ##taxa_juros = (1 + taxa_juros) ** (D(1) / D(12))
                    ##taxa_juros -= 1
                ##else:
                    ##taxa_juros /= 12

            ###
            ### Juro mensal
            ###
            ##elif condicao_obj.tipo_taxa == JUROS_COMPOSTOS:
                ##if condicao_obj.juros_composto:
                    ###
                    ### Converte para uma taxa diária equivalente
                    ###
                    ##taxa_juros = (1 + taxa_juros) ** (D(1) / D(30))
                    ##taxa_juros -= 1
                ##else:
                    ##taxa_juros /= 30

            if taxa_juros:
                #
                # Ultima parcela tem o máximo de dias/meses a considerar
                #
                parc_obj = condicao_obj.line_ids[-1]

                if parc_obj.meses:
                    meses = parc_obj.meses
                else:
                    dias = D(parc_obj.days or 0)
                    meses = dias / D(30)

                #print('meses', meses)

                if condicao_obj.tipo_taxa == JUROS_COMPOSTOS:
                    valor_parcela = numpy.pmt(taxa_juros, meses, (valor_original - entrada) * -1)
                    valor_parcela = valor_parcela.quantize(D('0.01'))
                    valor_original = entrada + (valor_parcela * meses)
                    valor = entrada + (valor_parcela * meses)

                elif condicao_obj.tipo_taxa == TABELA_PRICE:
                    valor_parcela = numpy.pmt(taxa_juros, meses, (valor_original - entrada) * -1)
                    valor_parcela = valor_parcela.quantize(D('0.01'))

                else:
                    valor_original = entrada + ((valor_original - entrada) * taxa_juros)
                    valor = entrada + ((valor - entrada) * taxa_juros)

            tem_entrada = False
            if entrada > 0:
                parcela = Parcela()
                parcela.data = data_base
                parcela.valor = entrada
                res.append(parcela)
                valor_original -= entrada
                valor -= entrada
                entrada = 0
                tem_entrada = True

            #
            # Calculamos as datas e juros de cada parcela
            #
            valor_total = taxa_administracao
            for parcela_obj in condicao_obj.line_ids:
                #
                # Esta parcela é a entrada?
                #
                #print('parcela a', parcela_obj.meses, parcela_obj.days, tem_entrada, parcela_obj.divide)
                if (not parcela_obj.meses) and (not parcela_obj.days) and tem_entrada:
                    continue

                if tem_entrada and parcela_obj.value == 'divisao':
                    parcela_obj.divide -= 1

                    if not parcela_obj.divide:
                        parcela_obj.divide = 1

                #print('parcela d', parcela_obj.meses, parcela_obj.days, entrada, tem_entrada, parcela_obj.divide)

                if condicao_obj.tipo_taxa == TABELA_PRICE:
                    parcela_obj.value = 'fixed'
                    parcela_obj.value_amount = valor_parcela

                parcela = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada)
                valor -= parcela.valor_original
                #print(parcela)
                valor_total += parcela.valor
                taxa_abertura_credito += D(condicao_obj.taxa_abertura_credito or 0)

                res.append(parcela)

            ###print(valor_total)
            ##valor_total += taxa_abertura_credito
            ###print(valor_total)
            ##taxa_iof = valor_total * D(condicao_obj.taxa_iof or 0) / D(100)
            ##valor_total += taxa_iof
            ###print(valor_total)

            ###
            ### Recalculamos as parcelas, com o valor dos juros já embutido
            ###
            ##if condicao_obj.tipo_taxa != TABELA_PRICE:
                ##valor_original = valor_total
                ##valor = valor_total
            ##else:
                ##valor = valor_original

            ##for parcela_obj in condicao_obj.line_ids:
                ##if condicao_obj.tipo_taxa == TABELA_PRICE:
                    ##parcela_obj.value = 'fixed'
                    ##parcela_obj.value_amount = valor_parcela
                    ##parcela = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, taxa_juros, entrada)

                ##else:
                    ##parcela = self.monta_parcela(condicao_obj, parcela_obj, valor_original, valor, data_base, 0, entrada)

                ##valor -= parcela.valor_original
                ###print(parcela)
                ##res.append(parcela)

        return res

    def gera_exemplo(self, cr, uid, ids, context={}):
        texto = u'Parcela | Vencimento |    Valor\n'

        parcelas = self.calcula(cr, uid, ids, 100000)

        i = 1
        total = D(0)
        for parcela in parcelas:
            texto += '  ' + str(i).zfill(3) + '     | '
            texto += formata_data(parcela.data) + ' | '
            texto += formata_valor(parcela.valor).rjust(10)
            total += parcela.valor
            texto += '\n'
            i += 1

        texto += '        |            | ----------\n'
        texto += '                       '
        texto += formata_valor(total).rjust(10)
        texto += '\n'

        dados = {
            'note': texto
        }

        self.pool.get('account.payment.term').write(cr, uid, ids, dados)

        return dados


account_payment_term()


class account_payment_term_line(osv.Model):
    _name = 'account.payment.term.line'
    #_inherit = 'account.payment.term.line'
    _rec_order = 'payment_id, sequence, name'
    _description = 'Payment Term Line'

    _columns = {
        'name': fields.char(u'Nome da parcela', size=32, required=True),
        'sequence': fields.integer(u'Ordem', required=True, help='The sequence field is used to order the payment term lines from the lowest sequences to the higher ones'),
        'value': fields.selection([('divisao', u'Multiplicação e divisão'),
                                   ('procent', u'Percentual'),
                                   ('balance', u'Saldo'),
                                   ('fixed', u'Valor fixo'),
                                   #('entrada', u'Entrada'),
                                   ], u'Valor determinado por',
                                   required=True, help='''Select here the kind of valuation related to this payment term line. Note that you should have your last line with the type 'Balance' to ensure that the whole amount will be threated.'''),
        'value_amount': fields.float(u'Valor a pagar (%% ou fixo)', help='For percent enter a ratio between 0-1.'),
        'days': fields.float(u'Dias da data', required=False, help='Number of days to add before computation of the day of month.' \
            'If Date=15/01, Number of Days=22, Day of Month=-1, then the due date is 28/02.'),
        'days2': fields.integer(u'Dia fixo do mês', required=False, help="Day of the month, set -1 for the last day of the current month. If it's positive, it gives the day of the next month. Set 0 for net days (otherwise it's based on the beginning of the month)."),
        'payment_id': fields.many2one('account.payment.term', 'Payment Term', required=True, select=True, ondelete='cascade'),
        'multiplica': fields.integer(u'Multiplica por'),
        'divide': fields.integer(u'Divide por'),
        'meses': fields.integer(u'Meses da data'),
    }
    _defaults = {
        'value': 'divisao',
        'sequence': 5,
        'days2': 0,
        'multiplica': 1,
        'divide': 1,
        'meses': 0,
    }
    _order = 'sequence'

    #def _check_percent(self, cr, uid, ids, context=None):
        #obj = self.browse(cr, uid, ids[0], context=context)
        #if obj.value == 'procent' and ( obj.value_amount < 0.0 or obj.value_amount > 1.0):
            #return False
        #return True

    #_constraints = [
        #(_check_percent, 'Percentages for Payment Term Line must be between 0 and 1, Example: 0.02 for 2% ', ['value_amount']),
    #]


account_payment_term_line()
