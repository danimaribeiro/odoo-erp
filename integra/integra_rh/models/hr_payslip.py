# -*- coding:utf-8 -*-

from integra_rh.wizard.relatorio import *
from hr_salary_rule import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pybrasil.valor.decimal import Decimal as D, ROUND_DOWN, ROUND_UP
from integra_rh.constantes_rh import TIPO_AFASTAMENTO
from hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from osv import fields, osv
from collections import OrderedDict
import os
import base64
from pybrasil.base import DicionarioBrasil
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime, idade, agora, hoje as hoje_brasil, dia_util_pagamento, primeiro_dia_mes, ultimo_dia_mes, formata_data
from copy import copy
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


TIPO_FERIAS = [
    ('N', 'Normal'),
    ('C', 'Coletiva'),
    ('A', 'Antecipada'),
]

GUARDA_IMPOSTO = True

MESES = (
    ('01', u'janeiro'),
    ('02', u'fevereiro'),
    ('03', u'março'),
    ('04', u'abril'),
    ('05', u'maio'),
    ('06', u'junho'),
    ('07', u'julho'),
    ('08', u'agosto'),
    ('09', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

TIPO_HOLERITE = (
    ('N', u'Normal'),
    ('F', u'Férias'),
    ('R', u'Rescisão'),
    ('D', u'Décimo terceiro'),
    ('A', u'Aviso prévio'),
    ('M', u'Licença maternidade'),
    ('C', u'Auxílio doença/acidente de trabalho'),
    #('M', u'Médias'),
)

GUARDA_LIQUIDO = True


class hr_payslip(osv.osv):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    _description = 'Pay Slip'
    _order = 'date_from desc, date_to desc, employee_id'
    _rec_name = 'descricao'

    def onchange_contract_id_ferias(self, cr, uid, ids, contract_id,  context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            if nome_campo == 'data_inicial':
                res[holerite_obj.id] = holerite_obj.date_from
            elif nome_campo == 'data_final':
                res[holerite_obj.id] = holerite_obj.date_to

        return res


    def _muda_nome_date_para_data(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            if nome_campo == 'data_inicial':
                res[holerite_obj.id] = holerite_obj.date_from
            elif nome_campo == 'data_final':
                res[holerite_obj.id] = holerite_obj.date_to

        return res

    def _saldo_ferias(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            res[holerite_obj.id] = 30 - holerite_obj.dias_ferias

        return res

    def _check_dates(self, cr, uid, ids, context=None):
        for payslip in self.browse(cr, uid, ids, context=context):
            #print('validando datas holerite', payslip.date_from, payslip.date_to, payslip.tipo)
            if payslip.date_from > payslip.date_to:
                return False
        return True

    def _valor_liquido(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            proventos = D(0)
            deducoes = D(0)
            arred_mes = D(0)
            for item_obj in holerite_obj.line_ids:
                if item_obj.holerite_anterior_line_id:
                    continue

                proventos += D(item_obj.provento)
                deducoes += D(item_obj.deducao)

                if item_obj.code == 'ARREDONDAMENTO_MES':
                    arred_mes = D(item_obj.provento)

            valor = proventos - deducoes
            valor = valor.quantize(D('0.01'))

            liquido = proventos - deducoes
            if nome_campo == 'valor_liquido':
                res[holerite_obj.id] = proventos - deducoes
            elif nome_campo == 'proventos':
                res[holerite_obj.id] = proventos
            elif nome_campo == 'deducoes':
                res[holerite_obj.id] = deducoes
            elif nome_campo == 'valor_arredondamento':
                liquido -= arred_mes
                if liquido != int(liquido):
                    res[holerite_obj.id] = 1 - (liquido - int(liquido))

        return res

    def _imposto(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if holerite_obj.line_ids:
                for item_obj in holerite_obj.line_ids:
                    if nome_campo == 'valor_inss' and item_obj.code in ('INSS', 'INSS_DIF_13'):
                        valor = D(item_obj.total)
                    elif nome_campo == 'valor_inss_13' and item_obj.code == 'INSS_13':
                        valor = D(item_obj.total)
                    elif nome_campo == 'valor_inss_outras' and item_obj.code == 'INSS_OUTRAS_ENTIDADES':
                        valor = D(item_obj.total)
                    elif nome_campo == 'valor_inss_rat' and item_obj.code == 'INSS_RAT':
                        valor = D(item_obj.total)
                    elif nome_campo == 'valor_inss_empresa' and item_obj.code == 'INSS_EMPRESA_TOTAL':
                        valor = D(item_obj.total)
                    elif nome_campo == 'aliquota_inss' and item_obj.code in ('INSS', 'INSS_DIF_13'):
                        valor = D(item_obj.rate)
                    elif nome_campo == 'aliquota_inss_13' and item_obj.code == 'INSS_13':
                        valor = D(item_obj.rate)
                    elif nome_campo == 'valor_fgts' and item_obj.code == 'FGTS':
                        valor = D(item_obj.total)
                    elif nome_campo == 'aliquota_fgts' and item_obj.code == 'FGTS':
                        valor = D(item_obj.rate)
                    elif nome_campo == 'base_irpf' and item_obj.code == 'IRPF':
                        valor = D(item_obj.amount)
                    elif nome_campo == 'valor_irpf' and item_obj.code == 'IRPF':
                        valor = D(item_obj.total)
                    elif nome_campo == 'aliquota_irpf' and item_obj.code == 'IRPF':
                        valor = D(item_obj.rate)
                    elif nome_campo == 'deducao_dependente' and item_obj.code == 'DEDUCAO_DEPENDENTES':
                        valor = D(item_obj.total)

            res[holerite_obj.id] = valor

        return res

    def _get_data_pagamento_irpf(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            data_base = False
            data_pagamento = False
            data_vencimento = False
            data_pagamento_funcionario = False
            estado = holerite_obj.contract_id.company_id.municipio_id.estado
            cidade = holerite_obj.contract_id.company_id.municipio_id.nome

            if holerite_obj.tipo == 'N':
                data_base = parse_datetime(holerite_obj.date_to).date() + relativedelta(days=+5)

            elif holerite_obj.tipo == 'R':
                if holerite_obj.data_pagamento:
                    data_base = parse_datetime(holerite_obj.data_pagamento).date()
                else:
                    if holerite_obj.simulacao:
                        data_base = parse_datetime(holerite_obj.data_afastamento_simulacao).date()
                    else:
                        data_base = parse_datetime(holerite_obj.data_afastamento).date()

            elif holerite_obj.tipo == 'F':
                data_base = parse_datetime(holerite_obj.date_from).date() + relativedelta(days=-2)

            elif holerite_obj.tipo == 'D':
                data_base = parse_datetime(holerite_obj.date_from).date() + relativedelta(day=20)

            if data_base:
                if holerite_obj.tipo in ['R', 'F', 'D']:
                    data_pagamento = dia_util_pagamento(data_base, holerite_obj.company_id.partner_id.estado, holerite_obj.company_id.partner_id.municipio_id.codigo_ibge[:7], antecipa=True)
                else:
                    data_pagamento = dia_util_pagamento(data_base, holerite_obj.company_id.partner_id.estado, holerite_obj.company_id.partner_id.municipio_id.codigo_ibge[:7])

                #
                # A data de vencimento é o dia 20 do mês seguinte ao mês do pagamento
                # antecipado se for feriado ou final de semana
                #
                data_vencimento = data_pagamento + relativedelta(day=20) + relativedelta(months=+1)
                data_vencimento = dia_util_pagamento(data_vencimento, holerite_obj.company_id.partner_id.estado, holerite_obj.company_id.partner_id.municipio_id.codigo_ibge[:7], antecipa=True)

            if nome_campo == 'data_pagamento_irpf':
                res[holerite_obj.id] = data_pagamento
            elif nome_campo == 'data_vencimento_irpf':
                res[holerite_obj.id] = data_vencimento
            elif nome_campo == 'data_pagamento':
                res[holerite_obj.id] = data_base

        return res

    _constraints = [(_check_dates, "Payslip 'Date From' must be before 'Date To'.", ['date_from', 'date_to'])]

    def _get_descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for holerite_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(holerite_obj.date_from)
            data_final = parse_datetime(holerite_obj.date_to)

            nome = str(holerite_obj.id)
            if holerite_obj.tipo == 'N':
                nome = u'%s' % holerite_obj.employee_id.nome
                mes = MESES_DIC[holerite_obj.mes]
                nome += ' - ' + mes + '/' + str(holerite_obj.ano)

            elif holerite_obj.tipo == 'F':
                nome = u'Férias de %s' % holerite_obj.employee_id.nome

                if holerite_obj.simulacao:
                    data_inicio_periodo_aquisitivo = parse_datetime(holerite_obj.data_inicio_periodo_aquisitivo)
                    data_fim_periodo_aquisitivo = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo)
                    nome += ' de ' + data_inicio_periodo_aquisitivo.strftime('%d/%m/%Y')
                    nome += ' a ' + data_fim_periodo_aquisitivo.strftime('%d/%m/%Y')
                else:
                    nome += ' de ' + data_inicial.strftime('%d/%m/%Y')
                    nome += ' a ' + data_final.strftime('%d/%m/%Y')

            elif holerite_obj.tipo == 'R':
                nome = u'Rescisão de %s' % holerite_obj.employee_id.nome

            elif holerite_obj.tipo == 'D':
                nome = u'13º de %s' % holerite_obj.employee_id.nome
                data_inicio_periodo_aquisitivo = parse_datetime(holerite_obj.data_inicio_periodo_aquisitivo)
                data_fim_periodo_aquisitivo = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo)

                if data_inicio_periodo_aquisitivo and data_fim_periodo_aquisitivo:
                    nome += ' de ' + data_inicio_periodo_aquisitivo.strftime('%d/%m/%Y')
                    nome += ' a ' + data_fim_periodo_aquisitivo.strftime('%d/%m/%Y')

            elif holerite_obj.tipo == 'A':
                nome = u'Aviso prévio de %s' % holerite_obj.employee_id.nome
                nome += ' de ' + data_inicial.strftime('%d/%m/%Y')
                nome += ' a ' + data_final.strftime('%d/%m/%Y')

            elif holerite_obj.tipo == 'M':
                nome = u'Licença Maternidade de %s' % holerite_obj.employee_id.nome
                data_inicio_periodo_aquisitivo = parse_datetime(holerite_obj.data_inicio_periodo_aquisitivo)
                data_fim_periodo_aquisitivo = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo)
                nome += ' de ' + data_inicio_periodo_aquisitivo.strftime('%d/%m/%Y')
                nome += ' a ' + data_fim_periodo_aquisitivo.strftime('%d/%m/%Y')

            elif holerite_obj.tipo == 'C':
                nome = u'Médias do período anterior ao afastamento de %s' % holerite_obj.employee_id.nome
                data_inicio_periodo_aquisitivo = parse_datetime(holerite_obj.data_inicio_periodo_aquisitivo)
                data_fim_periodo_aquisitivo = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo)
                nome += ' de ' + data_inicio_periodo_aquisitivo.strftime('%d/%m/%Y')
                nome += ' a ' + data_fim_periodo_aquisitivo.strftime('%d/%m/%Y')

            #print(nome.encode('utf-8'))

            res[holerite_obj.id] = nome

        return res


    _columns = {
        'data_inicial': fields.function(_muda_nome_date_para_data, method=True, type='date', string=u'Data inicial'),
        'data_final': fields.function(_muda_nome_date_para_data, method=True, type='date', string=u'Data final'),
        'proventos': fields.function(_valor_liquido, method=True, type='float', string=u'Valor líquido', store=GUARDA_LIQUIDO),
        'deducoes': fields.function(_valor_liquido, method=True, type='float', string=u'Valor líquido', store=GUARDA_LIQUIDO),
        'valor_liquido': fields.function(_valor_liquido, method=True, type='float', string=u'Valor líquido', store=GUARDA_LIQUIDO),
        'valor_arredondamento': fields.function(_valor_liquido, method=True, type='float', string=u'Valor arredondamento', store=GUARDA_LIQUIDO),
        'valor_inss': fields.function(_imposto, method=True, type='float', string=u'Valor INSS', store=GUARDA_IMPOSTO),
        'valor_inss_13': fields.function(_imposto, method=True, type='float', string=u'Valor INSS 13º', store=GUARDA_IMPOSTO),
        'valor_inss_empresa': fields.function(_imposto, method=True, type='float', string=u'Valor INSS Empresa', store=GUARDA_IMPOSTO),
        'valor_inss_outras': fields.function(_imposto, method=True, type='float', string=u'Valor INSS outras', store=GUARDA_IMPOSTO),
        'valor_inss_rat': fields.function(_imposto, method=True, type='float', string=u'Valor INSS RAT', store=GUARDA_IMPOSTO),
        'aliquota_inss': fields.function(_imposto, method=True, type='float', string=u'Alíquota INSS', store=GUARDA_IMPOSTO),
        'aliquota_inss_13': fields.function(_imposto, method=True, type='float', string=u'Alíquota INSS 13º', store=GUARDA_IMPOSTO),
        'valor_fgts': fields.function(_imposto, method=True, type='float', string=u'Valor FGTS', store=GUARDA_IMPOSTO),
        'aliquota_fgts': fields.function(_imposto, method=True, type='float', string=u'Alíquota FGTS', store=GUARDA_IMPOSTO),
        'base_irpf': fields.function(_imposto, method=True, type='float', string=u'Base IRPF', store=GUARDA_IMPOSTO),
        'valor_irpf': fields.function(_imposto, method=True, type='float', string=u'Valor IRPF', store=GUARDA_IMPOSTO),
        'aliquota_irpf': fields.function(_imposto, method=True, type='float', string=u'Alíquota IRPF', store=GUARDA_IMPOSTO),
        'deducao_dependente': fields.function(_imposto, method=True, type='float', string=u'Dedução de dependentes', store=GUARDA_IMPOSTO),
        'data_pagamento_irpf': fields.function(_get_data_pagamento_irpf, method=True, type='date', string=u'Data base IRPF', store=GUARDA_IMPOSTO, select=True),
        'data_vencimento_irpf': fields.function(_get_data_pagamento_irpf, method=True, type='date', string=u'Data vencimento IRPF', store=GUARDA_IMPOSTO, select=True),

        'state': fields.selection([
            ('draft', u'Rascunho'),
            #('verify', 'Waiting'),
            ('done', u'Fechado'),
            #('cancel', 'Rejected'),
        ], u'Situação', select=True, readonly=True),

        'name': fields.function(_get_descricao, type='char', size=128, string=u'Descrição', store=True, select=True),
        'descricao': fields.function(_get_descricao, type='char', size=128, string=u'Descrição', store=True, select=True),
        # 'struct_id': fields.many2one('hr.payroll.structure', 'Structure', readonly=True, states={'draft': [('readonly', False)]}, help='Defines the rules that have to be applied to this payslip, accordingly to the contract chosen. If you let empty the field contract, this field isn\'t mandatory anymore and thus the rules applied will be all the rules set on the structure of all contracts of the employee valid for the chosen period'),
        # 'name': fields.char('Description', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'number': fields.char('Reference', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        # 'date_from': fields.date('Date From', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        # 'date_to': fields.date('Date To', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        # 'state': fields.selection([
        #    ('draft', 'Draft'),
        #    ('verify', 'Waiting'),
        #    ('done', 'Done'),
        #    ('cancel', 'Rejected'),
        # ], 'State', select=True, readonly=True,
        #    help='* When the payslip is created the state is \'Draft\'.
        #    \n* If the payslip is under verification, the state is \'Waiting\'.
        #    \n* If the payslip is confirmed then state is set to \'Done\'.
        #    \n* When user cancel payslip the state is \'Rejected\'.'),
        # 'line_ids': fields.one2many('hr.payslip.line', 'slip_id', 'Payslip Line', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'line_ids': one2many_mod2('hr.payslip.line', 'slip_id', 'Payslip Lines', readonly=True, states={'draft':[('readonly',False)]}),
        # 'company_id': fields.many2one('res.company', 'Company', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'worked_days_line_ids': fields.one2many('hr.payslip.worked_days', 'payslip_id', 'Payslip Worked Days', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'input_line_ids': fields.one2many('hr.payslip.input', 'payslip_id', 'Payslip Inputs', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'paid': fields.boolean('Made Payment Order ? ', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        # 'note': fields.text('Description', readonly=True, states={'draft':[('readonly',False)]}),
        # 'details_by_salary_rule_category': fields.function(_get_lines_salary_rule_category, method=True, type='one2many', relation='hr.payslip.line', string='Details by Salary Rule Category'),
        # 'credit_note': fields.boolean('Credit Note', help="Indicates this payslip has a refund of another", readonly=True, states={'draft': [('readonly', False)]}),
        # 'payslip_run_id': fields.many2one('hr.payslip.run', 'Payslip Batches', readonly=True, states={'draft': [('readonly', False)]}),

        'company_id': fields.many2one('res.company', u'Empresa/unidade', ondelete='restrict'),
        'contract_id': fields.many2one('hr.contract', u'Contrato', ondelete='restrict'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário', ondelete='restrict'),
        'tipo': fields.selection(TIPO_HOLERITE, string=u'Tipo', select=True),
        'data_aviso_ferias': fields.date(u'Data do aviso de férias'),
        'data_inicio_periodo_aquisitivo': fields.date(u'Início do período aquisitivo'),
        'data_fim_periodo_aquisitivo': fields.date(u'Fim do período aquisitivo'),
        'tipo_ferias': fields.selection(TIPO_FERIAS, u'Tipo de férias'),
        'dias_ferias': fields.float(u'Dias de férias'),
        'dias_saldo_salario': fields.float(u'Dias de saldo de salário'),
        'saldo_ferias': fields.function(_saldo_ferias, type='float', string=u'Saldo de férias', store=True),
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        # 'data_inicial_afastamento': fields.date(u'Data de afastamento'),
        # 'data_final_afastamento': fields.date(u'Data de retorno'),
        # 'afastamento_id': fields.many2one('hr.afastamento', u'Afastamento'),
        # 'afastamento_rule_id': fields.related('afastamento_id', 'rule_id', type='many2one', string=u'Rubrica de afastamento', relation='hr.salary.rule'),
        'afastamento_ids': fields.one2many('hr.payslip_afastamento', 'payslip_id', u'Afastamentos'),
        'dias_afastamento': fields.integer(u'Dias de afastamento'),
        'holerite_anterior_id': fields.many2one('hr.payslip', u'Holerite anterior'),
        'data_aviso_previo': fields.date(u'Data do aviso prévio'),
        'aviso_previo_indenizado': fields.boolean(u'Aviso prévio indenizado?'),
        'aviso_previo_trabalhado_parcial': fields.boolean(u'Aviso prévio trabalhado parcial?'),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', relation='res.company', string=u'Empresa mãe', store=True, select=True),
        'data_admissao': fields.related('contract_id', 'date_start', type='date', relation='res.company', string=u'Data de admissão'),
        'salario': fields.related('contract_id', 'wage', type='float', string=u'Salário base'),
        # 'dispensa_empregador': fields.boolean(u'Dispensa pelo empregador?'),
        'dispensa_empregador': fields.related('struct_id', 'dispensa_empregador', type='boolean', string=u'Dispensa pelo empregador?'),
        # 'afastamento_imediato': fields.related('struct_id', 'afastamento_imediato', type='boolean', string=u'Afastamento imediato'),
        'afastamento_imediato': fields.boolean(u'Afastamento imediato'),
        # 'codigo_afastamento': fields.related('struct_id', 'codigo_afastamento', type='selection', string=u'Código de afastamento', selection=TIPO_AFASTAMENTO),
        'codigo_afastamento': fields.related('struct_id', 'codigo_afastamento', type='char', string=u'Código de afastamento'),
        'codigo_saque': fields.related('struct_id', 'codigo_saque', type='char', string=u'Código de saque'),
        'saldo_fgts': fields.float(u'Saldo FGTS'),
        'multa_fgts': fields.float(u'Multa FGTS'),
        'dias_aviso_previo': fields.integer(u'Dias de aviso prévio'),
        'data_homologacao': fields.date(u'Data de homologação'),
        'data_pagamento': fields.date(u'Data de pagamento'),
        'ultimo_salario': fields.float(u'Último salário'),
        'meses_decimo_terceiro': fields.float(u'Meses para décimo terceiro'),
        'escolhe_contrato': fields.boolean(u'Escolhe contrato?'),
        'data_afastamento': fields.date(u'Data afastamento'),
        'data_afastamento_simulacao': fields.date(u'Data afastamento Simulaçao'),

        'data_inicial_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De vencimento'),
        'data_inicial_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A vencimento'),
        'date_to_simulacao': fields.date(u'Data afastamento Simulaçao'),
        'simulacao': fields.boolean(string=u'Simulação?'),
        'provisao': fields.boolean(string=u'Provisão?'),
        'complementar': fields.boolean(string=u'Complementar?'),
        'data_complementar': fields.date(u'Data complementar'),
        'abono_pecuniario_ferias': fields.boolean(string=u'Abono?'),
        'media_inclui_mes': fields.boolean(string=u'Médias incluem o próprio mês?'),
        'contract_ferias_id': fields.many2one('hr.contract_ferias', u'Controle de férias'),
        'proporcional': fields.boolean(u'Proporcional?'),
        'vencida': fields.boolean(u'Vencida?'),
        'pagamento_dobro': fields.boolean(u'Em dobro?'),
        'pagamento_dobro_dias': fields.integer(u'Dias em dobro'),
        'programacao': fields.boolean(u'Férias programadas?'),
    }

    _defaults = {
        'tipo_ferias': 'N',
        'tipo': 'N',
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]).zfill(2),
        'date_from': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        'date_to': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],
        'aviso_previo_indenizado': False,
        'dispensa_empregador': True,
        'multa_fgts': 0,
        'dias_aviso_previo': 0,
        'escolhe_contrato': False,
        'dias_afastamento': 0,
        'simulacao': False,
        'provisao': False,
        'abono_pecuniario_ferias': False,
        'media_inclui_mes': False,
        'pagamento_dobro_dias': 0,
    }

    def efetivar_simulacao(self, cr, uid, ids, context={}):
        for holerite_obj in self.browse(cr, uid, ids):
            if holerite_obj.provisao:
                raise osv.except_osv(u'Inválido!', u'Não é permitido efetivar uma provisão!')

            if not holerite_obj.simulacao:
                raise osv.except_osv(u'Inválido!', u'Não é permitido executar a ação num cálculo já efetivo!')

            if holerite_obj.programacao:
                holerite_obj.compute_sheet()
                holerite_obj.write({'programacao': False})

            else:
                holerite_obj.write({'simulacao': False})

        return {}

    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['date_from'] = data_inicial
        valores['date_to'] = data_final

        data_inicial = parse_datetime(data_inicial).date()
        data_final = parse_datetime(data_final).date()

        dias_saldo_salario = data_final.toordinal() - data_inicial.toordinal() + 1

        if data_final.day == 31:
            dias_saldo_salario -= 1

        if dias_saldo_salario > 30:
            dias_saldo_salario = 30
        elif data_final.month == 2:
           if data_final.day == 28:
               dias_saldo_salario += 2
           else:
               dias_saldo_salario += 1

        valores['dias_saldo_salario'] = dias_saldo_salario

        return retorno

    def onchange_struct_id(self, cr, uid, ids, struct_id, context={}):
        valores = {}
        retorno = {'value': valores}

        if not struct_id:
            return retorno

        struct_obj = self.pool.get('hr.payroll.structure').browse(cr, uid, struct_id)
        valores['afastamento_imediato'] = struct_obj.afastamento_imediato
        valores['dispensa_empregador'] = struct_obj.dispensa_empregador
        valores['codigo_afastamento'] = struct_obj.codigo_afastamento

        return retorno

    def compute_sheet(self, cr, uid, ids, context={}):
        linhas_holerite_pool = self.pool.get('hr.payslip.line')
        sequence_pool = self.pool.get('ir.sequence')
        rubrica_pool = self.pool.get('hr.salary.rule')

        #
        # Ajusta os cálculos padrão do sistema, antes de mais nada
        #
        rubrica_pool.busca_calculos_padrao(cr, uid)

        for holerite_obj in self.browse(cr, uid, ids, context=context):
            print('vai calcular holerite', holerite_obj.id, holerite_obj.tipo, holerite_obj.simulacao)
            numero = holerite_obj.number or sequence_pool.get(cr, uid, 'salary.slip')

            #
            # Caso de férias e 13º, calcula as médias automaticamente
            #
            if holerite_obj.tipo in ['F', 'D', 'A', 'M', 'C']:
                holerite_obj._calcula_medias(context={})
                if holerite_obj.tipo == 'F':
                    holerite_obj._calcula_medias(ultimos_meses=True, context=context)

            #
            # Faz cada cálculo 2 vezes, para poder pegar o arredondamento
            #
            for i in range(2):
                #
                # Exclui as linhas calculadas anteriormente
                #
                calculo_antigo_ids = linhas_holerite_pool.search(cr, uid, [('slip_id', '=', holerite_obj.id), ('digitado', '=', False)], context=context)
                linhas_holerite_pool.unlink(cr, uid, calculo_antigo_ids, context=context)

                #
                # Calcula agora cada regra a ser aplicada
                #
                linhas_calculadas = []

                for valores in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, [holerite_obj.contract_id.id], holerite_obj.id, context=context):
                    linhas_calculadas += [[0, False, valores]]

                #
                # E, por fim, grava os valores calculados no holerite
                #
                self.write(cr, uid, [holerite_obj.id], {'line_ids': linhas_calculadas, 'number': numero})
                cr.commit()

                #
                # Quando for o mês 12, holerite normal, simular a folha completa, para
                # trazer o valor para apurar a diferença das médias
                #
                if (holerite_obj.tipo == 'N' and '-12-' in holerite_obj.date_to and (not holerite_obj.simulacao)):
                    holerite_obj.contract_id.decimo_terceiro_proporcional(holerite_obj.data_inicial, holerite_obj.data_final, calcula=True, inclui_mes=True, mantem_calculo=True)

                elif holerite_obj.tipo == 'R':
                    holerite_obj.contract_id.decimo_terceiro_proporcional(primeiro_dia_mes(holerite_obj.data_afastamento), holerite_obj.data_afastamento, calcula=True, inclui_mes=True, mantem_calculo=True, data_rescisao=holerite_obj.data_afastamento, dias_aviso_previo=holerite_obj.dias_aviso_previo)
                    holerite_obj.contract_id.ferias_proporcionais(holerite_obj.data_inicial, holerite_obj.data_final, exclui_simulacao=False, data_rescisao=holerite_obj.data_afastamento)
                    holerite_obj.contract_id.ferias_vencidas(holerite_obj.data_inicial, holerite_obj.data_final, exclui_simulacao=False, data_rescisao=holerite_obj.data_afastamento)

                    if holerite_obj.aviso_previo_indenizado:
                        holerite_obj.contract_id.ferias_proporcionais(holerite_obj.data_aviso_previo, holerite_obj.data_final, data_rescisao=holerite_obj.data_afastamento, exclui_simulacao=False, aviso_previo=True)

        return True

    def _ajusta_ferias(self, cr, uid, ids, tipo, date_from, date_to, contract_obj, struct_id=False):
        input_pool = self.pool.get('hr.payslip.input')

        valores = {}

        data_inicial = parse_datetime(date_from).date()
        data_final = parse_datetime(date_to).date()
        dias_saldo_salario = data_final.toordinal() - data_inicial.toordinal() + 1
        dias_corridos = data_final.toordinal() - data_inicial.toordinal() + 1

        if data_final.day == 31:
            dias_saldo_salario -= 1
            dias_corridos -= 1

        if dias_saldo_salario > 30:
            dias_saldo_salario = 30
        elif data_final.month == 2:
            if data_final.day == 28:
                dias_saldo_salario += 2
            else:
                dias_saldo_salario += 1

        valores['dias_saldo_salario'] = dias_saldo_salario

        if not contract_obj.struct_id:
            raise osv.except_osv(u'Erro!', u'O contrato do funcionário não tem uma estrutura de salário configurada!')

        #
        # Apaga os vínculos de afastamentos anteriores
        #
        holerite_afastamento_pool = self.pool.get('hr.payslip_afastamento')
        if ids:
            holerite_afastamento_ids = holerite_afastamento_pool.search(cr, uid, [('payslip_id', '=', ids[0])])
            holerite_afastamento_pool.unlink(cr, uid, holerite_afastamento_ids)

        #
        # Vamos analisar se há afastamento no período, quais as datas, e se
        # o afastamento é pelo período completo
        #
        afastamento_pool = self.pool.get('hr.afastamento')
        afastamento_ids = afastamento_pool.search(cr, uid, [('employee_id', '=', contract_obj.employee_id.id), ('contract_id', '=', contract_obj.id)], order='data_inicial desc')

        dias_afastamento = 0
        estrutura_afastamento_id = False
        holerite_afastamento_ids = []
        for afastamento_obj in afastamento_pool.browse(cr, uid, afastamento_ids):
            data_inicial_afastamento = parse_datetime(afastamento_obj.data_inicial).date()

            if data_inicial_afastamento < data_inicial:
                data_inicial_afastamento = data_inicial

            if afastamento_obj.data_final:
                data_final_afastamento = parse_datetime(afastamento_obj.data_final).date() + relativedelta(days=-1)
            else:
                #data_final_afastamento = hoje_brasil()
                data_final_afastamento = data_final

            if data_final_afastamento > data_final:
                data_final_afastamento = data_final

            dias_deste_afastamento = data_final_afastamento.toordinal() - data_inicial_afastamento.toordinal() + 1
            if data_final_afastamento.day == 31:
                dias_deste_afastamento -= 1

            if data_final_afastamento.month == 2:
                if data_final_afastamento.day == 28:
                    dias_deste_afastamento += 2
                elif data_final_afastamento.day == 29:
                    dias_deste_afastamento += 1

            if dias_deste_afastamento > 30:
                dias_deste_afastamento = 30

            if dias_deste_afastamento <= 0:
                continue

            dados = {
                'afastamento_id': afastamento_obj.id,
                'rule_id': afastamento_obj.rule_id.id,
                'data_inicial_afastamento': str(data_inicial_afastamento),
                'data_final_afastamento': str(data_final_afastamento),
                'dias_afastamento': dias_deste_afastamento,
            }

            if ids:
                holerite_afastamento_ids += [[0, ids[0], dados]]

            else:
                holerite_afastamento_ids += [[0, False, dados]]

            dias_afastamento += dias_deste_afastamento

            if not estrutura_afastamento_id:
                estrutura_afastamento_id = afastamento_obj.rule_id.estrutura_afastamento_id.id

        valores['dias_afastamento'] = dias_afastamento
        valores['afastamento_ids'] = holerite_afastamento_ids

        #
        # Afastamento total no mês, usa a estrutura de salário alternativa
        #
        if tipo == 'N':
            if dias_afastamento >= dias_corridos:
                valores['struct_id'] = estrutura_afastamento_id

            else:
                valores['struct_id'] = contract_obj.struct_id.id

        #
        # Testamos agora se o funcionário estava de férias parcial ou total
        # no mês
        #
        ferias_ids = self.search(cr, uid, [('contract_id', '=', contract_obj.id), ('tipo', '=', 'F'), ('simulacao', '=', False)], order='date_from desc, date_to desc')

        dias_ferias = 0
        for ferias_obj in self.browse(cr, uid, ferias_ids):
            #
            # Quantos dias ele estava de férias no período em questão
            #
            data_inicial_ferias = parse_datetime(ferias_obj.date_from).date()
            data_final_ferias = parse_datetime(ferias_obj.date_to).date()

            if ferias_obj.abono_pecuniario_ferias:
                data_final_ferias += relativedelta(days=10)

            if data_inicial_ferias < data_inicial:
                data_inicial_ferias = data_inicial

            if data_final_ferias > data_final:
                data_final_ferias = data_final

            dias_ferias = data_final_ferias.toordinal() - data_inicial_ferias.toordinal() + 1

            if dias_ferias <= 0:
                continue

            #
            # Verificamos novamente os dias de férias, desconsiderando o abono
            #
            data_inicial_ferias = parse_datetime(ferias_obj.date_from).date()
            data_final_ferias = parse_datetime(ferias_obj.date_to).date()

            if data_inicial_ferias < data_inicial:
                data_inicial_ferias = data_inicial

            if data_final_ferias > data_final:
                data_final_ferias = data_final

            dias_ferias = data_final_ferias.toordinal() - data_inicial_ferias.toordinal() + 1

            valores['holerite_anterior_id'] = ferias_obj.id
            break

        if dias_ferias <= 0:
            dias_ferias = 0

        valores['dias_ferias'] = dias_ferias

        #
        # Se estava de férias o mês todo, usa a estrutura específica de retorno de férias
        #
        if tipo == 'N':
            estrutura_obj = self.pool.get('hr.payroll.structure').browse(cr, uid, valores['struct_id'])

            #
            # Alterado de novo pelo Alex no dia 02/03/2016, pra voltar do jeito
            # que estava antes.... Ver chamado da Protefort, referente à folha
            # do Valdecir Casemiro
            #
            ##
            ## Alterado dia 04/03/2015 para considerar dias_corridos sempre 30, pois
            ## em fevereiro, mesmo com 28 dias corridos, não deve considerar a estrutura
            ## de retorno de férias, mas sim dar 2 dias de saldo de salário...
            ##
            ##if dias_ferias >= dias_corridos and estrutura_obj.estrutura_retorno_ferias_id:
            #if dias_ferias >= 30 and estrutura_obj.estrutura_retorno_ferias_id:
                #valores['struct_id'] = estrutura_obj.estrutura_retorno_ferias_id.id
            if dias_ferias >= dias_corridos and estrutura_obj.estrutura_retorno_ferias_id:
                valores['struct_id'] = estrutura_obj.estrutura_retorno_ferias_id.id

        ###
        ### Em fevereiro, caso haja afastamento ou férias,
        ### o saldo de salário é sobre os dias corridos, e não
        ### sobre 30 dias fixo
        ###
        ##if dias_afastamento > 0 or dias_ferias > 0:
            ##dias_saldo_salario = dias_corridos

        dias_saldo_salario -= dias_afastamento
        dias_saldo_salario -= dias_ferias
        valores['dias_saldo_salario'] = dias_saldo_salario

        #
        # Busca as variáveis lançadas para o período
        #
        print('vai buscar as variaveis')
        print(date_from, date_to, date_from[:8] + '01', contract_obj.id, contract_obj.employee_id.name)
        input_ids = input_pool.search(cr, uid, [('contract_id', '=', contract_obj.id), ('payslip_id', '=', False), ('data_inicial', '>=', date_from[:8] + '01'), ('data_final', '<=', date_to)])
        valores['input_line_ids'] = input_ids
        print('buscou as variaveis')
        print(input_ids)

        return valores

    def onchange_employee_id(self, cr, uid, ids, tipo, employee_id, date_from, date_to, contract_id=False, simulacao=False, provisao=False, context={}, programacao=False):
        contract_pool = self.pool.get('hr.contract')
        # worked_days_pool = self.pool.get('hr.payslip.worked_days')
        input_pool = self.pool.get('hr.payslip.input')
        linhas_holerite_pool = self.pool.get('hr.payslip.line')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if context is None:
            context = {}

        #
        # Exclui as linhas calculadas anteriormente
        #
        for id in ids:
            calculo_antigo_ids = linhas_holerite_pool.search(cr, uid, [('slip_id', '=', id)], context=context)
            linhas_holerite_pool.unlink(cr, uid, calculo_antigo_ids, context=context)

        valores = {
            'line_ids': [],
            'input_line_ids': [],
            'worked_days_line_ids': [],
            'contract_id': False,
        }
        res = {
            'value': valores
        }

        if (not employee_id):
            return res

        #
        # Busca o contrato ativo do funcionário, e, caso haja mais de 1,
        # dá um erro
        #
        valores['escolhe_contrato'] = False

        if date_to:
            contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), '|', ('date_end', '=', False), ('date_end', '>=', date_to)])
        elif tipo == 'R':
            contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id)])
        else:
            contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), ('date_end', '=', False)])

        if len(contract_ids) > 1:
            valores['escolhe_contrato'] = True
        elif len(contract_ids) == 0:
            raise osv.except_osv(u'Erro!', u'O funcionário não tem nenhum contrato ativo!')

        if contract_id:
            contract_ids = [contract_id]

        contract_id = contract_ids[0]
        contract_obj = contract_pool.browse(cr, uid, contract_id)
        valores['contract_id'] = contract_obj.id
        valores['company_id'] = contract_obj.company_id.id
        valores['data_admissao'] = contract_obj.date_start
        valores['salario'] = contract_obj.wage

        if date_from and date_from < contract_obj.date_start:
            date_from = contract_obj.date_start
            valores['date_from'] = date_from

        #
        # Alterado dia 22/05/2014, para considerar também rescisões
        #
        #if tipo == 'N':
        #
        # Alterado dia 30//10/2014 para tratar o décimo terceiro
        #
        #if tipo != 'F' and date_from and date_to:
        if tipo in ('N', 'M', 'C') and date_from and date_to:
            valores.update(self.pool.get('hr.payslip')._ajusta_ferias(cr, uid, ids, tipo, date_from, date_to, contract_obj, False))

        elif tipo == 'F':
            if not contract_obj.struct_id:
                raise osv.except_osv(u'Erro!', u'O contrato do funcionário não tem uma estrutura de salário configurada!')

            if not contract_obj.struct_id.estrutura_ferias_id:
                raise osv.except_osv(u'Erro!', u'A estrutura de salário do contrato do funcionário não tem uma estrutura de férias configurada!')

            valores['struct_id'] = contract_obj.struct_id.estrutura_ferias_id.id

            #
            # Define a data do início do período aquisitivo, baseado
            # na data de admissão ou das últimas férias
            #
            ultimas_ferias_ids = self.search(cr, uid, [('contract_id', '=', contract_obj.id), ('tipo', '=', 'F'), ('simulacao', '=', False)], order='date_from desc, date_to desc', limit=1)

            if ultimas_ferias_ids:
                ultimas_ferias_obj = self.browse(cr, uid, ultimas_ferias_ids[0])

                if (ultimas_ferias_obj.saldo_ferias > 0) and (not ultimas_ferias_obj.abono_pecuniario_ferias):
                    data_inicio_periodo_aquisitivo = parse_datetime(ultimas_ferias_obj.data_inicio_periodo_aquisitivo).date()
                    data_fim_periodo_aquisitivo = parse_datetime(ultimas_ferias_obj.data_fim_periodo_aquisitivo).date()

                    valores['dias_ferias'] = ultimas_ferias_obj.saldo_ferias

                else:
                    #
                    # Buscar o próximo período aquisitivo
                    #
                    if programacao:
                        proximas_ferias_ids = self.pool.get('hr.contract_ferias').search(cr, uid, [('contract_id', '=', contract_obj.id), ('data_inicial_periodo_aquisitivo', '>', ultimas_ferias_obj.data_fim_periodo_aquisitivo), ('perdido_afastamento', '=', False)], order='data_inicial_periodo_aquisitivo', limit=1)
                    else:
                        proximas_ferias_ids = self.pool.get('hr.contract_ferias').search(cr, uid, [('contract_id', '=', contract_obj.id), ('data_inicial_periodo_aquisitivo', '>', ultimas_ferias_obj.data_fim_periodo_aquisitivo), ('perdido_afastamento', '=', False), ('vencida', '=', True)], order='data_inicial_periodo_aquisitivo', limit=1)

                    if proximas_ferias_ids:
                        proximas_ferias_obj = self.pool.get('hr.contract_ferias').browse(cr, uid, proximas_ferias_ids[0])
                        data_inicio_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_inicial_periodo_aquisitivo).date()

                        if proximas_ferias_obj.avos == 11:
                            data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo_cheio).date()
                            valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias) + D('2.5')

                        elif proximas_ferias_obj.avos == 12:
                            data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo_cheio).date()
                            valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias)
                            valores['pagamento_dobro'] = proximas_ferias_obj.pagamento_dobro
                            valores['pagamento_dobro_dias'] = proximas_ferias_obj.pagamento_dobro_dias

                        else:
                            data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo).date()
                            valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias)

                    elif programacao:
                        raise osv.except_osv(u'Erro!', u'O funcionário não tem nenhum período vencido a programar!')

                    else:
                        data_fim_periodo_aquisitivo_anterior = parse_datetime(ultimas_ferias_obj.data_fim_periodo_aquisitivo)
                        data_inicio_periodo_aquisitivo = data_fim_periodo_aquisitivo_anterior + relativedelta(days=+1)
                        data_fim_periodo_aquisitivo = data_inicio_periodo_aquisitivo + relativedelta(years=+1, days=-1)

            else:
                data_admissao = parse_datetime(contract_obj.date_start)

                proximas_ferias_ids = self.pool.get('hr.contract_ferias').search(cr, uid, [('contract_id', '=', contract_obj.id), ('data_inicial_periodo_aquisitivo', '>=', contract_obj.date_start), ('perdido_afastamento', '=', False)], order='data_inicial_periodo_aquisitivo', limit=1)

                if proximas_ferias_ids:
                    proximas_ferias_obj = self.pool.get('hr.contract_ferias').browse(cr, uid, proximas_ferias_ids[0])
                    data_inicio_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_inicial_periodo_aquisitivo).date()

                    if proximas_ferias_obj.avos == 11:
                        data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo_cheio).date()
                        valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias) + D('2.5')

                    elif proximas_ferias_obj.avos == 12:
                        data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo_cheio).date()
                        valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias)

                    else:
                        data_fim_periodo_aquisitivo = parse_datetime(proximas_ferias_obj.data_final_periodo_aquisitivo).date()
                        valores['dias_ferias'] = D(proximas_ferias_obj.saldo_dias)

            valores['data_inicio_periodo_aquisitivo'] = data_inicio_periodo_aquisitivo.strftime('%Y-%m-%d')
            valores['data_fim_periodo_aquisitivo'] = data_fim_periodo_aquisitivo.strftime('%Y-%m-%d')

            #employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            #if date_from and date_to:
                #data_inicial = parse_datetime(date_from)
                #data_final = parse_datetime(date_to)

                #if tipo == 'N':
                    #nome = u'%s' % employee_obj.name
                #elif tipo == 'F':
                    #nome = u'Férias de %s' % employee_obj.name
                #elif tipo == 'R':
                    #nome = u'Rescisão de %s' % employee_obj.name

                #primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
                #if str(data_inicial.date()) == primeiro_dia and str(data_final.date()) == ultimo_dia:
                    #nome += u' referente a ' + MESES_DIC[str(data_inicial.month)] + '/' + str(data_inicial.year)
                #else:
                    #nome += u' referente a ' + data_inicial.strftime('%d/%m/%Y')
                    #nome += u' até ' + data_final.strftime('%d/%m/%Y')

                #valores['name'] = nome

        elif tipo == 'D':
            if not contract_obj.struct_id:
                raise osv.except_osv(u'Erro!', u'O contrato do funcionário não tem uma estrutura de salário configurada!')

            if '-12-' not in date_from:
                if not contract_obj.struct_id.estrutura_adiantamento_decimo_terceiro_id:
                    raise osv.except_osv(u'Erro!', u'A estrutura de salário do contrato do funcionário não tem uma estrutura de adiantamento de 13º configurada!')
                else:
                    valores['struct_id'] = contract_obj.struct_id.estrutura_adiantamento_decimo_terceiro_id.id

            elif not contract_obj.struct_id.estrutura_decimo_terceiro_id:
                raise osv.except_osv(u'Erro!', u'A estrutura de salário do contrato do funcionário não tem uma estrutura de 13º configurada!')
            else:
                valores['struct_id'] = contract_obj.struct_id.estrutura_decimo_terceiro_id.id

            #
            # Define a data do início do período aquisitivo, baseado
            # na data de admissão ou do início do ano
            #
            meses_decimo_terceiro, data_inicial, data_final = contract_obj.decimo_terceiro_proporcional(date_from, date_to, calcula=False, retorna_datas=True, provisao=provisao)
            valores['data_inicio_periodo_aquisitivo'] = str(data_inicial)
            valores['data_fim_periodo_aquisitivo'] = str(data_final)
            valores['meses_decimo_terceiro'] = meses_decimo_terceiro

            ####
            #### Somente no caso de afastamentos desde janeiro (o ano todo), considerar que o
            #### funcionário, em princípio, vai continuar afastado, e não terá direito
            #### a 13º para novembro e dezembro (2/12 avos para novembro, 1/12 avos para dezembro)
            ####
            ###filtro_afastamento = {
                ###'data_inicial': str(data_inicial)[:10],
                ###'data_final': str(date_to)[:10],
                ###'contract_id': str(contract_obj.id),
            ###}

            ###if contract_obj.contrato_transf_id:
                ###filtro_afastamento['contract_id'] += ', ' + str(contract_obj.contrato_transf_id.id)

            ###sql = contract_obj._SQL_HOLERITE_AFASTADO.format(**filtro_afastamento)
            ####print(sql)
            ###cr.execute(sql)
            ###dados_afastamento = cr.fetchall()
            ###meses_afastado = len(dados_afastamento)
            ###print('meses afastado', meses_afastado, meses_decimo_terceiro)

            ###if meses_afastado > 0:
                ###if meses_afastado == 12 - meses_decimo_terceiro:
                    ###meses_decimo_terceiro = 0
                ###else:
                    ###meses_decimo_terceiro -= meses_afastado

            ###print(meses_decimo_terceiro)
            valores['meses_decimo_terceiro'] = meses_decimo_terceiro

            #employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            #if date_from and date_to:
                #data_inicial = parse_datetime(date_from)
                #data_final = parse_datetime(date_to)

                #if tipo == 'N':
                    #nome = u'%s' % employee_obj.name
                #elif tipo == 'F':
                    #nome = u'Férias de %s' % employee_obj.name
                #elif tipo == 'R':
                    #nome = u'Rescisão de %s' % employee_obj.name
                #elif tipo == 'D':
                    #nome = u'13º de %s' % employee_obj.name

                #primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
                #if str(data_inicial.date()) == primeiro_dia and str(data_final.date()) == ultimo_dia:
                    #nome += u' referente a ' + MESES_DIC[str(data_inicial.month)] + '/' + str(data_inicial.year)
                #else:
                    #nome += u' referente a ' + data_inicial.strftime('%d/%m/%Y')
                    #nome += u' até ' + data_final.strftime('%d/%m/%Y')

                #valores['name'] = nome

        return res

    def onchange_datas(self, cr, uid, ids, tipo, employee_id, contract_id, date_from, date_to, data_inicio_periodo_aquisitivo=None, data_fim_periodo_aquisitivo=None, data_aviso_previo=None, aviso_previo_indenizado=True, afastamento_imediato=False, dispensa_empregador=False, simulacao=False, aviso_previo_trabalhado_parcial=False, struct_id=False, saldo_dias=False, pagamento_dobro=False):
        #print('entrou aqui')
        # if tipo == 'F':
            # if date_from:
                # if data_inicio_periodo_aquisitivo and date_from < data_inicio_periodo_aquisitivo:
                    # raise osv.except_osv(u'Erro!', u'A data incial do período de gozo não pode ser anterior ao período aquisitivo!')
                # if data_fim_periodo_aquisitivo and date_from > data_fim_periodo_aquisitivo:
                    # raise osv.except_osv(u'Erro!', u'A data incial do período de gozo não pode ser posterior ao período aquisitivo!')

            # if date_to:
                # if data_inicio_periodo_aquisitivo and date_to < data_inicio_periodo_aquisitivo:
                    # raise osv.except_osv(u'Erro!', u'A data final do período de gozo não pode ser anterior ao período aquisitivo!')
                # if data_fim_periodo_aquisitivo and date_to > data_fim_periodo_aquisitivo:
                    # raise osv.except_osv(u'Erro!', u'A data final do período de gozo não pode ser posterior ao período aquisitivo!')

        if tipo in ['N', 'F', 'D'] and not date_from:
            return {}

        if tipo == 'R' and ((not date_to) and (not afastamento_imediato and not data_aviso_previo)):
            return {}

        if tipo == 'D' and not contract_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        contrato_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)

        #
        # Valida data de contratação
        #
        if date_from:
            if date_from < contrato_obj.date_start:
                date_from = contrato_obj.date_start
                valores['date_from'] = contrato_obj.date_start

        if tipo == 'R':
            data_admissao = parse_datetime(contrato_obj.date_start).date()

            if afastamento_imediato or aviso_previo_trabalhado_parcial:
                data_final = parse_datetime(date_to).date()
                data_inicial = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]
                date_from = data_inicial
                valores['date_from'] = date_from

                if afastamento_imediato:
                    valores['data_aviso_previo'] = date_to
                    valores['aviso_previo_indenizado'] = True

                valores['data_afastamento'] = date_to
                data_aviso_previo = parse_datetime(date_to).date()

            elif data_aviso_previo:
                data_aviso_previo = parse_datetime(data_aviso_previo).date()

                ##dias_aviso = 30
                ##idade_contrato = idade(data_admissao, data_aviso_previo)

                ##if dispensa_empregador:
                    ###
                    ### 30 dias corridos, incluindo o próprio dia do aviso
                    ### 3 dias a mais para cada ano trabalhado, com
                    ### limite até 90 dias
                    ###

                    ##if len(contrato_obj.company_id.avisoprevioproporcional_ids) > 0:
                        ##avisoproporcional_obj = contrato_obj.company_id.avisoprevioproporcional_ids[0]
                        ##for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                            ##if item_aviso_proporcional_obj.anos == idade_contrato:
                                ##dias_aviso = item_aviso_proporcional_obj.dias - 1

                        ##data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
                        ##nova_idade_contrato = idade(data_admissao, data_final)

                        ##if nova_idade_contrato != idade_contrato:
                            ##for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                                ##if item_aviso_proporcional_obj.anos == nova_idade_contrato:
                                    ##dias_aviso = item_aviso_proporcional_obj.dias - 1

                    ##else:
                        ##dias_aviso = 30 + (3 * idade_contrato)

                        ##if dias_aviso > 90:
                            ##dias_aviso = 90
                        ###
                        ### Tira 1 dia pq o dia do próprio aviso conta
                        ###
                        ##dias_aviso -= 1

                        ##data_final = data_aviso_previo + relativedelta(days=+dias_aviso)

                        ###
                        ### Verifica se a data de afastamento vai dar mais 1 ano no contrato
                        ###
                        ##nova_idade_contrato = idade(data_admissao, data_final)

                        ##if nova_idade_contrato != idade_contrato:
                            ##dias_aviso += 3

                            ##if dias_aviso > 90:
                                ##dias_aviso = 89

                ##if cr.dbname.upper() == 'PATRIMONIAL':
                    ##data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
                ##else:
                    ##data_final = data_aviso_previo + relativedelta(days=+dias_aviso+1)

                ##data_inicial = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]
                data_inicial, data_final, dias_aviso, data_afastamento = contrato_obj.calcula_data_aviso_previo(str(data_aviso_previo), dispensa_empregador)

                date_from = str(data_inicial)[:10]
                date_to = str(data_final)[:10]
                valores['date_from'] = date_from
                valores['date_to'] = date_to
                ##valores['dias_aviso_previo'] = dias_aviso + 1
                valores['dias_aviso_previo'] = dias_aviso
                valores['data_afastamento'] = date_to

                if afastamento_imediato or aviso_previo_indenizado:
                    valores['data_afastamento'] = str(data_aviso_previo)[:10]

                if (not dispensa_empregador) or aviso_previo_indenizado:
                    valores['data_pagamento'] = parse_datetime(valores['data_afastamento']) + relativedelta(days=9)
                else:
                    valores['data_pagamento'] = parse_datetime(valores['data_afastamento']) + relativedelta(days=1)

                valores['data_pagamento'] = str(valores['data_pagamento'])[:10]

            else:
                data_final = parse_datetime(date_to).date()
                date_from = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]

                dias_aviso = 30

                if dispensa_empregador:
                    #
                    # 30 dias corridos, incluindo o próprio dia do aviso
                    # 3 dias a mais para cada ano trabalhado, com
                    # limite até 90 dias
                    #
                    idade_contrato = idade(data_admissao, data_final)

                    if len(contrato_obj.company_id.avisoprevioproporcional_ids) > 0:
                        avisoproporcional_obj = contrato_obj.company_id.avisoprevioproporcional_ids[0]
                        for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                            if item_aviso_proporcional_obj.anos == idade_contrato:
                                dias_aviso = item_aviso_proporcional_obj.dias - 1

                    else:
                        dias_aviso = 30 + (3 * idade_contrato)

                        if dias_aviso > 90:
                            dias_aviso = 90

                        #
                        # Tira 1 dia pq o dia do próprio aviso conta
                        #
                        dias_aviso -= 1
                        dias_aviso *= -1

                data_aviso_previo = data_final + relativedelta(days=+dias_aviso)
                valores['data_aviso_previo'] = str(data_aviso_previo)[:10]
                valores['date_from'] = date_from
                valores['dias_aviso_previo'] = dias_aviso + 1

        data_inicial = parse_datetime(date_from).date()
        if tipo == 'R':
            print(valores['data_afastamento'], 'valores[data_afastamento]')
            valores.update(self.pool.get('hr.payslip')._ajusta_ferias(cr, uid, ids, tipo, str(primeiro_dia_mes(valores['data_afastamento'])), str(ultimo_dia_mes(valores['data_afastamento'])), contrato_obj, struct_id))
        elif tipo == 'N':
            valores.update(self.pool.get('hr.payslip')._ajusta_ferias(cr, uid, ids, tipo, date_from, date_to, contrato_obj, struct_id))

        if tipo == 'F':
            if not date_to:
                # date_to = data_inicial + relativedelta(months=+1, days=-1)
                #print(saldo_dias, 'aqui')
                if saldo_dias:
                    if saldo_dias == int(saldo_dias):
                        saldo_dias -= 1
                    else:
                        saldo_dias = int(saldo_dias)
                else:
                    saldo_dias = 29

                date_to = data_inicial + relativedelta(days=saldo_dias)
                date_to = date_to.strftime('%Y-%m-%d')
                valores['date_to'] = date_to
            else:
                data_maxima = data_inicial + relativedelta(days=+29)
                if date_to > data_maxima.strftime('%Y-%m-%d'):
                    raise osv.except_osv(u'Erro!', u'O período de férias não pode ultrapassar 1 mês!')

            data_final = parse_datetime(date_to).date()
            valores['dias_ferias'] = data_final.toordinal() - data_inicial.toordinal() + 1

            data_final_periodo_concessivo = parse_datetime(data_fim_periodo_aquisitivo).date()
            data_final_periodo_concessivo += relativedelta(years=+1)

            #if data_final > data_final_periodo_concessivo:
                #pagamento_dobro_dias = data_final - data_final_periodo_concessivo

                #print('dias para dobra das ferias')
                #print(data_final)
                #print(data_final_periodo_concessivo)
                #print(pagamento_dobro_dias)

                #if pagamento_dobro_dias.days >= 30:
                    #valores['pagamento_dobro'] = True
                    #valores['pagamento_dobro_dias'] = 30
                #else:
                    #valores['pagamento_dobro'] = True
                    #valores['pagamento_dobro_dias'] = pagamento_dobro_dias.days

                #print(pagamento_dobro, valores['pagamento_dobro'], valores['pagamento_dobro_dias'])

            valores_novos = self.pool.get('hr.payslip')._ajusta_ferias(cr, uid, ids, tipo, date_from, date_to, contrato_obj, struct_id)

            if 'dias_afastamento' in valores_novos and ('afastamento_ids' in valores_novos and len(valores_novos['afastamento_ids']) > 0):
                raise osv.except_osv(u'Erro!', u'Não é permitido lançamento de férias para funcionários afastados!')

        if tipo == 'D':
            data_inicial_periodo_aquisitivo = date_from[0:4] + '-01-01'

            if data_inicial_periodo_aquisitivo < contrato_obj.date_start:
                data_inicial_periodo_aquisitivo = contrato_obj.date_start

            valores['data_inicio_periodo_aquisitivo'] = data_inicial_periodo_aquisitivo
            valores['data_fim_periodo_aquisitivo'] = date_to

        # if date_to < date_from:

        employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id)

        data_final = parse_datetime(date_to).date()

        if employee_id:
            if tipo == 'N':
                nome = u'%s' % employee_obj.name
            elif tipo == 'F':
                nome = u'Férias de %s' % employee_obj.name
            elif tipo == 'R':
                nome = u'Rescisão de %s' % employee_obj.name
            elif tipo == 'D':
                nome = u'13º de %s' % employee_obj.name
            elif tipo == 'A':
                nome = u'Aviso prévio de %s' % employee_obj.name

            primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
            if str(data_inicial) == primeiro_dia and str(data_final) == ultimo_dia:
                nome += u' referente a ' + MESES_DIC[str(data_inicial.month).zfill(2)] + u'/' + str(data_inicial.year)
            else:
                nome += u' referente a ' + data_inicial.strftime('%d/%m/%Y')
                nome += u' até ' + data_final.strftime('%d/%m/%Y')

            valores['name'] = nome

        #
        # Cálculo das datas das férias
        #
        if tipo == 'F':
            data_aviso_ferias = data_inicial + relativedelta(months=-1)
            valores['data_aviso_ferias'] = data_aviso_ferias.strftime('%Y-%m-%d')

        if tipo == 'R' and aviso_previo_indenizado:
            primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_aviso_previo.year, data_aviso_previo.month)
            primeiro_dia = parse_datetime(primeiro_dia).date()
            dias_saldo_salario = data_aviso_previo.toordinal() - primeiro_dia.toordinal() + 1

        else:
            dias_saldo_salario = data_final.toordinal() - data_inicial.toordinal() + 1

        if dias_saldo_salario > 30:
            dias_saldo_salario = 30

        if 'dias_ferias' in valores:
            dias_saldo_salario -= valores['dias_ferias']

        valores['dias_saldo_salario'] = dias_saldo_salario

        #
        # A partir do dia 05/11, só cancela o contrato quando fecharem a rescisão
        #
        #if tipo == 'R' and not simulacao:
            #contrato_obj.write({'date_end': str(valores['data_afastamento'])})

        #
        # Meses para décimo terceiro
        #
        meses_decimo_terceiro, valor_proporcional = contrato_obj.decimo_terceiro_proporcional(str(date_from), str(date_to))
        valores['meses_decimo_terceiro'] = meses_decimo_terceiro

        return res

    ###def onchange_datas_simulacao(self, cr, uid, ids, tipo, employee_id, contract_id, date_from, date_to, data_inicio_periodo_aquisitivo=None, data_fim_periodo_aquisitivo=None, data_aviso_previo=None, aviso_previo_indenizado=True, afastamento_imediato=False, dispensa_empregador=False, simulacao=True, aviso_previo_trabalhado_parcial=False):
        #### if tipo == 'F':
            #### if date_from:
                #### if data_inicio_periodo_aquisitivo and date_from < data_inicio_periodo_aquisitivo:
                    #### raise osv.except_osv(u'Erro!', u'A data incial do período de gozo não pode ser anterior ao período aquisitivo!')
                #### if data_fim_periodo_aquisitivo and date_from > data_fim_periodo_aquisitivo:
                    #### raise osv.except_osv(u'Erro!', u'A data incial do período de gozo não pode ser posterior ao período aquisitivo!')

            #### if date_to:
                #### if data_inicio_periodo_aquisitivo and date_to < data_inicio_periodo_aquisitivo:
                    #### raise osv.except_osv(u'Erro!', u'A data final do período de gozo não pode ser anterior ao período aquisitivo!')
                #### if data_fim_periodo_aquisitivo and date_to > data_fim_periodo_aquisitivo:
                    #### raise osv.except_osv(u'Erro!', u'A data final do período de gozo não pode ser posterior ao período aquisitivo!')

        ###if tipo in ['N', 'F', 'D'] and not date_from:
            ###return {}

        ###if tipo == 'R' and ((not date_to) and (not afastamento_imediato and not data_aviso_previo)):
            ###return {}

        ###res = {}
        ###valores = {}
        ###res['value'] = valores

        ###contrato_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)

        ####
        #### Valida data de contratação
        ####
        ###if date_from:
            ###if date_from < contrato_obj.date_start:
                ###date_from = contrato_obj.date_start
                ###valores['date_from'] = contrato_obj.date_start

        ###if tipo == 'R':
            ###data_admissao = parse_datetime(contrato_obj.date_start).date()

            ###if afastamento_imediato or aviso_previo_trabalhado_parcial:
                ###data_final = parse_datetime(date_to).date()
                ###data_inicial = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]
                ###date_from = data_inicial
                ###valores['date_from'] = date_from

                ###if afastamento_imediato:
                    ###valores['data_aviso_previo'] = date_to
                    ###valores['aviso_previo_indenizado'] = True

                ###valores['data_afastamento_simulacao'] = date_to
                ###data_aviso_previo = parse_datetime(date_to).date()

            ###elif data_aviso_previo:
                ###data_aviso_previo = parse_datetime(data_aviso_previo).date()

                ###dias_aviso = 30
                ###idade_contrato = idade(data_admissao, data_aviso_previo)

                ###if dispensa_empregador:
                    ####
                    #### 30 dias corridos, incluindo o próprio dia do aviso
                    #### 3 dias a mais para cada ano trabalhado, com
                    #### limite até 90 dias
                    ####

                    ###if len(contrato_obj.company_id.avisoprevioproporcional_ids) > 0:
                        ###avisoproporcional_obj = contrato_obj.company_id.avisoprevioproporcional_ids[0]
                        ###for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                            ###if item_aviso_proporcional_obj.anos == idade_contrato:
                                ###dias_aviso = item_aviso_proporcional_obj.dias - 1

                        ###data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
                        ###nova_idade_contrato = idade(data_admissao, data_final)

                        ###if nova_idade_contrato != idade_contrato:
                            ###for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                                ###if item_aviso_proporcional_obj.anos == nova_idade_contrato:
                                    ###dias_aviso = item_aviso_proporcional_obj.dias - 1

                    ###else:
                        ###dias_aviso = 30 + (3 * idade_contrato)

                        ###if dias_aviso > 90:
                            ###dias_aviso = 90
                        ####
                        #### Tira 1 dia pq o dia do próprio aviso conta
                        ####
                        ###dias_aviso -= 1

                        ###data_final = data_aviso_previo + relativedelta(days=+dias_aviso)

                        ####
                        #### Verifica se a data de afastamento vai dar mais 1 ano no contrato
                        ####
                        ###nova_idade_contrato = idade(data_admissao, data_final)

                        ###if nova_idade_contrato != idade_contrato:
                            ###dias_aviso += 3

                            ###if dias_aviso > 90:
                                ###dias_aviso = 89

                ###data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
                ###data_inicial = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]
                ###date_from = str(data_inicial)[:10]
                ###date_to = str(data_final)[:10]
                ###valores['date_from'] = date_from
                ###valores['date_to'] = date_to
                ###valores['dias_aviso_previo'] = dias_aviso + 1
                ###valores['data_afastamento_simulacao'] = date_to

                ###if afastamento_imediato or aviso_previo_indenizado:
                    ###valores['data_afastamento_simulacao'] = str(data_aviso_previo)[:10]

                ###if (not dispensa_empregador) or aviso_previo_indenizado :
                    ###valores['data_pagamento'] = parse_datetime(valores['data_afastamento_simulacao']) + relativedelta(days=9)
                ###else:
                    ###valores['data_pagamento'] = parse_datetime(valores['data_afastamento_simulacao']) + relativedelta(days=1)

                ###valores['data_pagamento'] = str(valores['data_pagamento'])[:10]

            ###else:
                ###data_final = parse_datetime(date_to).date()
                ###date_from = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]

                ###dias_aviso = 30

                ###if dispensa_empregador:
                    ####
                    #### 30 dias corridos, incluindo o próprio dia do aviso
                    #### 3 dias a mais para cada ano trabalhado, com
                    #### limite até 90 dias
                    ####
                    ###idade_contrato = idade(data_admissao, data_final)

                    ###if len(contrato_obj.company_id.avisoprevioproporcional_ids) > 0:
                        ###avisoproporcional_obj = contrato_obj.company_id.avisoprevioproporcional_ids[0]
                        ###for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                            ###if item_aviso_proporcional_obj.anos == idade_contrato:
                                ###dias_aviso = item_aviso_proporcional_obj.dias - 1

                    ###else:
                        ###dias_aviso = 30 + (3 * idade_contrato)

                        ###if dias_aviso > 90:
                            ###dias_aviso = 90

                        ####
                        #### Tira 1 dia pq o dia do próprio aviso conta
                        ####
                        ###dias_aviso -= 1
                        ###dias_aviso *= -1

                ###data_aviso_previo = data_final + relativedelta(days=+dias_aviso)
                ###valores['data_aviso_previo'] = str(data_aviso_previo)[:10]
                ###valores['date_from'] = date_from
                ###valores['dias_aviso_previo'] = dias_aviso + 1

        ###data_inicial = parse_datetime(date_from).date()

        ###if tipo == 'F':
            ###if not date_to:
                #### date_to = data_inicial + relativedelta(months=+1, days=-1)
                ###date_to = data_inicial + relativedelta(days=+29)
                ###date_to = date_to.strftime('%Y-%m-%d')
                ###valores['date_to'] = date_to
            ###else:
                ###data_maxima = data_inicial + relativedelta(days=+29)
                ###if date_to > data_maxima.strftime('%Y-%m-%d'):
                    ###raise osv.except_osv(u'Erro!', u'O período de férias não pode ultrapassar 1 mês!')

            ###data_final = parse_datetime(date_to).date()
            ###valores['dias_ferias'] = data_final.toordinal() - data_inicial.toordinal() + 1

        #### if date_to < date_from:
            #### raise osv.except_osv(u'Erro!', u'A data inicial não pode ser anterior à data final!')

        ###employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id)

        ###data_final = parse_datetime(date_to).date()

        ###if employee_id:
            ###if tipo == 'N':
                ###nome = u'%s' % employee_obj.name
            ###elif tipo == 'F':
                ###nome = u'Férias de %s' % employee_obj.name
            ###elif tipo == 'R':
                ###nome = u'Rescisão de %s' % employee_obj.name
            ###elif tipo == 'D':
                ###nome = u'13º de %s' % employee_obj.name

            ###primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
            ###if str(data_inicial) == primeiro_dia and str(data_final) == ultimo_dia:
                ###nome += u' referente a ' + MESES_DIC[str(data_inicial.month).zfill(2)] + u'/' + str(data_inicial.year)
            ###else:
                ###nome += u' referente a ' + data_inicial.strftime('%d/%m/%Y')
                ###nome += u' até ' + data_final.strftime('%d/%m/%Y')

            ###valores['name'] = nome

        ####
        #### Cálculo das datas das férias
        ####
        ###if tipo == 'F':
            ###data_aviso_ferias = data_inicial + relativedelta(months=-1)
            ###valores['data_aviso_ferias'] = data_aviso_ferias.strftime('%Y-%m-%d')

        ###if tipo == 'R' and aviso_previo_indenizado:
            ###primeiro_dia, ultimo_dia = primeiro_ultimo_dia_mes(data_aviso_previo.year, data_aviso_previo.month)
            ###primeiro_dia = parse_datetime(primeiro_dia).date()
            ###dias_saldo_salario = data_aviso_previo.toordinal() - primeiro_dia.toordinal() + 1

        ###else:
            ###dias_saldo_salario = data_final.toordinal() - data_inicial.toordinal() + 1

        ###if dias_saldo_salario > 30:
            ###dias_saldo_salario = 30

        ###valores['dias_saldo_salario'] = dias_saldo_salario


        ####
        #### Meses para décimo terceiro
        ####
        ###meses_decimo_terceiro, valor_proporcional = contrato_obj.decimo_terceiro_proporcional(str(date_from), str(date_to))
        ###valores['meses_decimo_terceiro'] = meses_decimo_terceiro

        ###return res

    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        def _sum_salary_rule_category(localdict, category, amount):
            if isinstance(category, int):
                category_obj = self.pool.get('hr.salary.rule.category').browse(cr, uid, category)
            else:
                category_obj = category

            #if category_obj.parent_id:
                #localdict = _sum_salary_rule_category(localdict, category_obj.parent_id, amount)

            #
            # Pega todos os float do localdict e converte para Decimal
            #
            localdict['Decimal'] = D
            localdict['D'] = D

            for item, valor in localdict.iteritems():
                if isinstance(valor, float):
                    localdict[item] = D(valor)

            if not category_obj.code in localdict['categories'].dict:
                localdict['categories'].dict[category_obj.code] = D(0)

            localdict['categories'].dict[category_obj.code] += amount

            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, contract_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.contract_id = contract_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or D(0)

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.contract_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.contract_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.contract_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.contract_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.contract_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.contract_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []

        obj_rule = self.pool.get('hr.salary.rule')

        holerite_obj = self.pool.get('hr.payslip').browse(cr, uid, payslip_id, context=context)

        afastamentos = {}
        for afastamento_obj in holerite_obj.afastamento_ids:
            if afastamento_obj.rule_id.code in afastamentos:
                afastamentos[afastamento_obj.rule_id.code].dias_afastamento += afastamento_obj.dias_afastamento
            else:
                afastamentos[afastamento_obj.rule_id.code] = afastamento_obj

        worked_days = {}
        for worked_days_line in holerite_obj.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line

        inputs = {}
        for input_line in holerite_obj.input_line_ids:
            inputs[input_line.code] = input_line

        #print(inputs)

        medias = {}
        for media_line in holerite_obj.media_ids:
            if not media_line.titulo and media_line.rule_id:
                medias[media_line.rule_id.code] = media_line

        categories_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, holerite_obj.contract_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, holerite_obj.contract_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, holerite_obj.contract_id.id, holerite_obj)
        rules_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, rules)
        holerite_anterior = holerite_obj.holerite_anterior_id
        holerite_anterior_obj = Payslips(self.pool, cr, uid, holerite_obj.contract_id.id, holerite_anterior)
        afastamento_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, afastamentos)
        media_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, medias)

        categoria_pool = self.pool.get('hr.salary.rule.category')
        localdict = {
            'categories': categories_obj,
            'rules': rules_obj,
            'payslip': payslip_obj,
            'worked_days': worked_days_obj,
            'inputs': input_obj,
            'categoria': categories_obj,
            'holerite': payslip_obj,
            'variavel2': worked_days_obj,
            'variavel': input_obj,
            'regra': rules_obj,
            'holerite_anterior': holerite_anterior_obj,
            'afastamento': afastamento_obj,
            'medias': media_obj,
            'PROVENTO_TRIBUTADO': categoria_pool.browse(cr, uid, categoria_pool.search(cr, uid, [['code', '=', 'PROV']])[0]),
            'PROVENTO_SOBRE_PROVENTO': categoria_pool.browse(cr, uid, categoria_pool.search(cr, uid, [['code', '=', 'PROV_PROV']])[0]),
            'PROVENTO_NAO_TRIBUTADO': categoria_pool.browse(cr, uid, categoria_pool.search(cr, uid, [['code', '=', 'PROV_NAO_TRIBUTADO']])[0]),
        }

        #
        # Leva as tabelas padrão também
        #
        tabela_inss = OrderedDict()
        teto_inss = OrderedDict()
        tabela_inss_ids = self.pool.get('hr.tabela.inss').search(cr, 1, [], order='ano desc, teto desc')
        ultimo_ano = 0
        for tab_obj in self.pool.get('hr.tabela.inss').browse(cr, 1, tabela_inss_ids):
            #
            # Inclui o ano seguinte ao último ano cadastrado, para os casos de virada
            # de dezembro pra janeiro
            #
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                tabela_inss[ultimo_ano + 1] = []
                teto_inss[ultimo_ano + 1] = 0

            if tab_obj.ano not in tabela_inss:
                tabela_inss[tab_obj.ano] = []
                teto_inss[tab_obj.ano] = 0

            tabela_inss[tab_obj.ano].append([tab_obj.teto, tab_obj.aliquota])

            if tab_obj.teto > teto_inss[tab_obj.ano]:
                teto_inss[tab_obj.ano] = tab_obj.teto

            if tab_obj.ano == ultimo_ano:
                tabela_inss[ultimo_ano + 1].append([tab_obj.teto, tab_obj.aliquota])

                if tab_obj.teto > teto_inss[ultimo_ano + 1]:
                    teto_inss[ultimo_ano + 1] = tab_obj.teto

        localdict['TABELA_INSS'] = tabela_inss
        localdict['TETO_INSS'] = teto_inss

        tabela_ir = OrderedDict()
        tabela_ir_ids = self.pool.get('hr.tabela.ir').search(cr, 1, [], order='ano desc, mes desc, piso desc')
        ultimo_ano = 0
        ultimo_mes = ''
        for tab_obj in self.pool.get('hr.tabela.ir').browse(cr, 1, tabela_ir_ids):
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                ultimo_mes = tab_obj.mes
                tabela_ir[ultimo_ano + 1] = OrderedDict()
                tabela_ir[ultimo_ano + 1]['01'] = OrderedDict()

            if not tab_obj.ano in tabela_ir:
                tabela_ir[tab_obj.ano] = OrderedDict()

            if not tab_obj.mes in tabela_ir[tab_obj.ano]:
                tabela_ir[tab_obj.ano][tab_obj.mes] = OrderedDict()

            tabela_ir[tab_obj.ano][tab_obj.mes][tab_obj.piso] = [tab_obj.aliquota or 0, tab_obj.parcela_deduzir or 0]

            if tab_obj.ano == ultimo_ano and tab_obj.mes == ultimo_mes:
                tabela_ir[ultimo_ano + 1]['01'][tab_obj.piso] = [tab_obj.aliquota or 0, tab_obj.parcela_deduzir or 0]

        localdict['TABELA_IR'] = tabela_ir
        #print(tabela_ir)

        tabela_ir_dependente = OrderedDict()
        tabela_ir_dependente_ids = self.pool.get('hr.tabela.ir.dependente').search(cr, 1, [], order='ano desc, mes desc')
        ultimo_ano = 0
        ultimo_mes = ''
        for tab_obj in self.pool.get('hr.tabela.ir.dependente').browse(cr, 1, tabela_ir_dependente_ids):
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                ultimo_mes = tab_obj.mes
                tabela_ir_dependente[ultimo_ano + 1] = OrderedDict()

            if not tab_obj.ano in tabela_ir_dependente:
                tabela_ir_dependente[tab_obj.ano] = OrderedDict()

            tabela_ir_dependente[tab_obj.ano][tab_obj.mes] = tab_obj.deducao_dependente

            if tab_obj.ano == ultimo_ano and tab_obj.mes == ultimo_mes:
                tabela_ir_dependente[ultimo_ano + 1]['01'] = tab_obj.deducao_dependente

        localdict['TABELA_IR_DEPENDENTE'] = tabela_ir_dependente

        tabela_rat = OrderedDict()
        tabela_outras_entidades = OrderedDict()
        tabela_rat_ids = self.pool.get('hr.tabela.rat').search(cr, 1, [], order='raiz_cnpj, ano desc')
        ultimo_ano = 0
        for tab_obj in self.pool.get('hr.tabela.rat').browse(cr, 1, tabela_rat_ids):
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                tabela_rat[ultimo_ano + 1] = OrderedDict()
                tabela_outras_entidades[ultimo_ano + 1] = OrderedDict()

            if not tab_obj.ano in tabela_rat:
                tabela_rat[tab_obj.ano] = OrderedDict()
                tabela_outras_entidades[tab_obj.ano] = OrderedDict()

            tabela_rat[tab_obj.ano][tab_obj.raiz_cnpj] = tab_obj.aliquota_final
            tabela_outras_entidades[tab_obj.ano][tab_obj.raiz_cnpj] = tab_obj.aliquota_outras_entidades or 0

            if tab_obj.ano == ultimo_ano:
                tabela_rat[ultimo_ano + 1][tab_obj.raiz_cnpj] = tab_obj.aliquota_final
                tabela_outras_entidades[ultimo_ano + 1][tab_obj.raiz_cnpj] = tab_obj.aliquota_outras_entidades or 0

        localdict['TABELA_RAT'] = tabela_rat
        localdict['TABELA_OUTRAS_ENTIDADES'] = tabela_outras_entidades

        tabela_salario_familia = OrderedDict()
        tabela_salario_familia_ids = self.pool.get('hr.tabela.salario.familia').search(cr, 1, [], order='ano desc, teto')
        ultimo_ano = 0
        for tab_obj in self.pool.get('hr.tabela.salario.familia').browse(cr, 1, tabela_salario_familia_ids):
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                tabela_salario_familia[ultimo_ano + 1] = []

            if not tab_obj.ano in tabela_salario_familia:
                tabela_salario_familia[tab_obj.ano] = []

            tabela_salario_familia[tab_obj.ano].append([tab_obj.teto, tab_obj.valor])

            if tab_obj.ano == ultimo_ano:
                tabela_salario_familia[ultimo_ano + 1].append([tab_obj.teto, tab_obj.valor])

        localdict['TABELA_SALARIO_FAMILIA'] = tabela_salario_familia

        tabela_salario_minimo = OrderedDict()
        tabela_salario_minimo_ids = self.pool.get('hr.tabela.salario.minimo').search(cr, 1, [], order='ano desc')
        ultimo_ano = 0
        for tab_obj in self.pool.get('hr.tabela.salario.minimo').browse(cr, 1, tabela_salario_minimo_ids):
            if ultimo_ano == 0:
                ultimo_ano = tab_obj.ano
                tabela_salario_minimo[ultimo_ano + 1] = D(0)

            if not tab_obj.ano in tabela_salario_minimo:
                tabela_salario_minimo[tab_obj.ano] = D(0)

            tabela_salario_minimo[tab_obj.ano] = D(tab_obj.valor)

            if tab_obj.ano == ultimo_ano:
                tabela_salario_minimo[ultimo_ano + 1] = D(tab_obj.valor)

        localdict['TABELA_SALARIO_MINIMO'] = tabela_salario_minimo

        #
        # Busca as regras de todas as estruturas pais-filhas
        #
        estrutura_ids = list(set(self.pool.get('hr.payroll.structure')._get_parent_structure(cr, uid, [holerite_obj.struct_id.id], context=context)))
        estrutura_ids += [holerite_obj.struct_id.id]

        #
        # Busca as regras da estrutura
        #
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, estrutura_ids, context=context)

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract, 'empregado': employee, 'contrato': contract})

            #
            # Monta um dicionário com as regras digitadas, para evitar duplicidade
            #
            linhas_digitadas = {}
            for line_obj in holerite_obj.line_ids:
                linhas_digitadas[line_obj.code] = line_obj

            #
            # Agora, exclui as linhas digitadas, elas serão reincluídas depois
            #
            for line_obj in holerite_obj.line_ids:
                line_obj.unlink()

            #
            # Se houver holerite anterior, traz as linhas calculadas
            # no caso de rescisão, somente vai a base do inss e o valor
            #
            if holerite_anterior:
                ajuste_liquido_irpf = 0

                for linha_obj in holerite_anterior.line_ids:
                    if linha_obj.salary_rule_id.regra_holerite_anterior_id:
                        regra_obj = linha_obj.salary_rule_id.regra_holerite_anterior_id
                    else:
                        regra_obj = linha_obj.salary_rule_id

                    #
                    # Recalcula a proporção a toda hora, pois no caso de IRPF, quando
                    # incluir, vai ser 100%
                    #
                    proporcao = D(holerite_obj.dias_ferias) / D(holerite_anterior.dias_ferias or 1)
                    proporcao_abono = D(0)

                    if holerite_anterior.abono_pecuniario_ferias:
                        data_inicial_abono = parse_datetime(holerite_anterior.date_to).date()
                        data_inicial_abono += relativedelta(days=1)
                        data_final_abono = data_inicial_abono + relativedelta(days=9)

                        print('1 - data_inicial_abono, data_final_abono')
                        print(data_inicial_abono, data_final_abono)

                        if str(data_inicial_abono) < holerite_obj.date_from:
                            #data_inicial_abono = parse_datetime(str(data_inicial_abono)).date()
                            data_inicial_abono = parse_datetime(holerite_obj.date_from).date()

                        print('2 - data_inicial_abono, data_final_abono')
                        print(data_inicial_abono, data_final_abono)

                        if str(data_inicial_abono) <= holerite_obj.date_to:
                            if str(data_final_abono) > holerite_obj.date_to:
                                data_final_abono = parse_datetime(holerite_obj.date_to).date()

                            dias_abono = data_final_abono - data_inicial_abono

                            if dias_abono.days:
                                dias_abono = dias_abono.days + 1
                                proporcao_abono = D(dias_abono) / D(10)

                            print('dias_abono', dias_abono, proporcao_abono)
                    #
                    # IRPF é incluído no holerite de pagamento, que ocorre 2 dias antes do início de gozo
                    #
                    if holerite_anterior.tipo == 'F' and ('IRPF' in regra_obj.code or 'DEPENDENTE' in regra_obj.code):
                        #
                        # Retornado dia 13/08/2014
                        #
                        data_pagamento = parse_datetime(holerite_anterior.date_from).date() + relativedelta(days=-2)
                        data_pagamento = str(data_pagamento)

                        if data_pagamento < holerite_obj.date_from or data_pagamento > holerite_obj.date_to:
                           if linha_obj.code == 'IRPF':
                               ajuste_liquido_irpf = linha_obj.total * proporcao * -1
                               continue

                        ## else:
                        #proporcao = D(1)
                        #if linha_obj.code == 'IRPF':
                            #ajuste_liquido_irpf = D(linha_obj.total) * D(D(1) - proporcao)
                            #ajuste_liquido_irpf = ajuste_liquido_irpf.quantize(D('0.01'))

                    proporcao_inversa = D(1) - proporcao
                    proporcao_inversa_abono = D(1) - proporcao_abono

                    #
                    # Alterado dia 22/05/2014 para considerar também as rescisões
                    #
                    #if holerite_obj.tipo != 'R' or regra_obj.code in ['BASE_INSS', 'INSS']:
                    if True:
                        codigo_regra = linha_obj.code + '_anterior'

                        if linha_obj.code == 'INSS':
                            linha_obj.name = u'INSS de férias gozadas'

                        if codigo_regra in linhas_digitadas:
                            result_dict[codigo_regra] = {
                                'holerite_anterior_line_id': linha_obj.id,
                                'salary_rule_id': linhas_digitadas[codigo_regra].salary_rule_id.id,
                                'contract_id': linhas_digitadas[codigo_regra].contract_id.id,
                                'name': linhas_digitadas[codigo_regra].name,
                                'code': codigo_regra,
                                'category_id': linhas_digitadas[codigo_regra].category_id.id,
                                'sequence': linhas_digitadas[codigo_regra].sequence,
                                'appears_on_payslip': linhas_digitadas[codigo_regra].appears_on_payslip,
                                'condition_select': linhas_digitadas[codigo_regra].condition_select,
                                'condition_python': linhas_digitadas[codigo_regra].condition_python,
                                'condition_range': linhas_digitadas[codigo_regra].condition_range,
                                'condition_range_min': linhas_digitadas[codigo_regra].condition_range_min,
                                'condition_range_max': linhas_digitadas[codigo_regra].condition_range_max,
                                'amount_select': linhas_digitadas[codigo_regra].amount_select,
                                'amount_fix': linhas_digitadas[codigo_regra].amount_fix,
                                'amount_python_compute': linhas_digitadas[codigo_regra].amount_python_compute,
                                'amount_percentage': linhas_digitadas[codigo_regra].amount_percentage,
                                'amount_percentage_base': linhas_digitadas[codigo_regra].amount_percentage_base,
                                'register_id': linhas_digitadas[codigo_regra].register_id.id,
                                'amount': D(linhas_digitadas[codigo_regra].amount).quantize(D('0.01')),
                                'employee_id': linhas_digitadas[codigo_regra].employee_id.id,
                                'quantity': D(linhas_digitadas[codigo_regra].quantity),
                                'rate': D(linhas_digitadas[codigo_regra].rate),
                                'total': D(linhas_digitadas[codigo_regra].total),
                                'digitado': True,
                                'sinal': linhas_digitadas[codigo_regra].sinal,
                            }

                            localdict[codigo_regra] = D(linhas_digitadas[codigo_regra].total)
                            localdict[codigo_regra + '_taxa'] = D(linhas_digitadas[codigo_regra].rate)
                            #localdict = _sum_salary_rule_category(localdict, regra_obj.category_id, result_dict[codigo_regra]['total'])

                        else:
                            #
                            # Calcula aqui os novos valores de amount e total
                            # garantindo que, entre os meses em que haja a distribuição,
                            # não haja diferença de centavos
                            #
                            amount_original = D(linha_obj.amount).quantize(D('0.01'))
                            total_original = D(linha_obj.total).quantize(D('0.01'))

                            if 'ABONO' in linha_obj.code:
                                if proporcao_abono > proporcao_inversa_abono:
                                    amount_dif = amount_original * proporcao_inversa_abono
                                    amount_dif = amount_dif.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    total_dif = total_original * proporcao_inversa_abono
                                    total_dif = total_dif.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    amount = amount_original - amount_dif
                                    total = total_original - total_dif

                                else:
                                    amount = amount_original * proporcao_abono
                                    amount = amount.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    total = total_original * proporcao_abono
                                    total = total.quantize(D('0.01')) #, rounding=ROUND_DOWN)

                            else:
                                if proporcao > proporcao_inversa:
                                    amount_dif = amount_original * proporcao_inversa
                                    amount_dif = amount_dif.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    total_dif = total_original * proporcao_inversa
                                    total_dif = total_dif.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    amount = amount_original - amount_dif
                                    total = total_original - total_dif

                                else:
                                    amount = amount_original * proporcao
                                    amount = amount.quantize(D('0.01')) #, rounding=ROUND_DOWN)
                                    total = total_original * proporcao
                                    total = total.quantize(D('0.01')) #, rounding=ROUND_DOWN)

                            result_dict[codigo_regra] = {
                                'holerite_anterior_line_id': linha_obj.id,
                                'salary_rule_id': regra_obj.id,
                                'contract_id': linha_obj.contract_id.id,
                                'name': linha_obj.name,
                                'code': codigo_regra,
                                'category_id': regra_obj.category_id.id,
                                'sequence': regra_obj.sequence,
                                'appears_on_payslip': regra_obj.appears_on_payslip,
                                'condition_select': linha_obj.condition_select,
                                'condition_python': linha_obj.condition_python,
                                'condition_range': linha_obj.condition_range,
                                'condition_range_min': linha_obj.condition_range_min,
                                'condition_range_max': linha_obj.condition_range_max,
                                'amount_select': linha_obj.amount_select,
                                'amount_fix': linha_obj.amount_fix,
                                'amount_python_compute': linha_obj.amount_python_compute,
                                'amount_percentage': linha_obj.amount_percentage,
                                'amount_percentage_base': linha_obj.amount_percentage_base,
                                'register_id': linha_obj.register_id.id,
                                'amount': amount,
                                'employee_id': linha_obj.employee_id.id,
                                'quantity': D(linha_obj.quantity),
                                'rate': D(linha_obj.rate),
                                'total': total,
                                'digitado': False,
                                'sinal': linha_obj.sinal,
                            }

                            #if regra_obj.code in ['BASE_INSS', 'INSS']:
                                #result_dict[codigo_regra].update({
                                    #'amount': D(D(linha_obj.amount) * D(proporcao)).quantize(D('0.01'), rounding=arredondamento),
                                    #'total': D(D(linha_obj.total) * D(proporcao)).quantize(D('0.01'), rounding=arredondamento),
                                #})

                            #
                            # Para os líquidos, soma os proporcionais de proventos e descontos
                            #
                            if 'LIQ_' in regra_obj.code:
                                prov_amount = D(0)
                                prov_total = D(0)
                                desc_amount = D(0)
                                desc_total = D(0)
                                for codreg in result_dict:
                                    if '_anterior' in codreg:
                                        if result_dict[codreg]['sinal'] == '+':
                                            prov_amount += result_dict[codreg]['amount']
                                            prov_total += result_dict[codreg]['total']
                                        elif result_dict[codreg]['sinal'] == '-':
                                            desc_amount += result_dict[codreg]['amount']
                                            desc_total += result_dict[codreg]['total']

                                result_dict[codigo_regra]['amount'] = prov_total - desc_total
                                result_dict[codigo_regra]['total'] = prov_total - desc_total
                                #result_dict[codigo_regra]['amount'] -= ajuste_liquido_irpf
                                #result_dict[codigo_regra]['total'] -= ajuste_liquido_irpf

                            localdict[codigo_regra] = result_dict[codigo_regra]['total']
                            localdict[codigo_regra + '_taxa'] = result_dict[codigo_regra]['rate']

                            #localdict = _sum_salary_rule_category(localdict, regra_obj.category_id, result_dict[codigo_regra]['total'])

            #
            # Nos holerites normais, traz também as regras específicas do empregado
            #
            regras = copy(rule_ids)
            regra_funcionario_com_valor = {}
            rubricas_especiais = {}
            if holerite_obj.tipo in ['N', 'R', 'A', 'M', 'C'] and contract.regra_ids:
                for regra in contract.regra_ids:
                    ignora_rubrica_funcionario = holerite_obj.struct_id.ignora_rubrica_funcionario
                    ignora_rubrica_funcionario_quantidade = holerite_obj.struct_id.ignora_rubrica_funcionario_quantidade
                    if regra.data_final and regra.data_final < holerite_obj.date_from:
                        continue
                    if regra.data_inicial and regra.data_inicial > holerite_obj.date_to:
                        continue

                    #
                    # Leva as rubricas especiais para testar dentro das outras
                    # rubricas
                    #
                    rubricas_especiais[regra.rule_id.code + str(regra.rule_id.id).zfill(6)] = regra

                    #
                    # Considera se a estrutura ignora alguns casos
                    #
                    if (regra.valor != 0 or regra.quantidade != 0) and (not ignora_rubrica_funcionario_quantidade):
                        if regra.rule_id.category_id.sinal != '-' or holerite_obj.tipo in ['N', 'R']:
                            regras += [(regra.rule_id.id, regra.rule_id.sequence)]
                            regra_funcionario_com_valor[regra.rule_id.code] = regra

                    elif not ignora_rubrica_funcionario:
                        if regra.rule_id.category_id.sinal != '-' or holerite_obj.tipo in ['N', 'R']:
                            regras += [(regra.rule_id.id, regra.rule_id.sequence)]

            elif holerite_obj.tipo in ['F', 'R', 'D'] and contract.regra_ids:
                #print('vai carregar as regras especificas dos funcionarios', contract.regra_ids)
                for regra in contract.regra_ids:
                    #
                    # Para rescisões, considerar o período de pagamento somente
                    #
                    if holerite_obj.tipo == 'R':
                        #
                        # Começou depois do fim do período de cálculo?
                        #
                        if regra.data_inicial and regra.data_inicial > holerite_obj.date_to:
                            continue

                        #print(regra.rule_id.code, 'eh media', 'comecou antes do fim')
                        #print(regra.rule_id.code, regra.data_final, holerite_obj.date_from)
                        #
                        # A data final é anterior ao início do período de cálculo?
                        #
                        if regra.data_final and regra.data_final < holerite_obj.date_from:
                            continue

                        #print(regra.rule_id.code, 'eh media', 'terminou depois do comeco')
                    else:
                        #
                        # Começou depois do fim do período aquisitivo?
                        #
                        if regra.data_inicial and regra.data_inicial > holerite_obj.data_fim_periodo_aquisitivo:
                            continue

                        #print(regra.rule_id.code, 'eh media', 'comecou antes do fim')
                        #print(regra.rule_id.code, regra.data_final, holerite_obj.data_inicio_periodo_aquisitivo)
                        #
                        # A data final é anterior ao início do período aquisitivo?
                        #
                        if regra.data_final and regra.data_final < holerite_obj.data_inicio_periodo_aquisitivo:
                            continue

                        #print(regra.rule_id.code, 'eh media', 'terminou depois do comeco')

                    #
                    # Leva as rubricas especiais para testar dentro das outras
                    # rubricas
                    #
                    rubricas_especiais[regra.rule_id.code + str(regra.rule_id.id).zfill(6)] = regra

                    #
                    # A rubrica não é de média?
                    #
                    if not regra.rule_id.tipo_media:
                        #print('nao eh media', regra.rule_id.code)
                        continue

                    regras += [(regra.rule_id.id, regra.rule_id.sequence)]
                    #regras += [(regra.rule_id.id, regra.rule_id.sequence)]
                #print(regras)

            rubrica_especial_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, rubricas_especiais)
            localdict['rubrica_especial'] = rubrica_especial_obj

            sorted_rule_ids = [id for id, sequence in sorted(regras, key=lambda x:x[1])]

            jah_calculou = []

            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                #if 'PENSAO_ALIMENTICIA' in rule.code:
                    #print(rule.code, rule.code in linhas_digitadas, rule.code in regra_funcionario_com_valor)

                #
                # As 8 linhas abaixo reiniciam os valores retornados
                # a cada cálculo de regra
                #
                localdict['result'] = D(0)
                localdict['result_qty'] = D('1.00')
                localdict['result_rate'] = D('100.00')
                localdict['aparece_no_holerite'] = rule.appears_on_payslip
                localdict['forca_valor'] = None
                localdict['forca_quantidade'] = None
                localdict['forca_porcentagem'] = None
                localdict['forca_total'] = None
                localdict['categoria_id'] = None
                localdict['simulacao_id'] = None
                localdict['CALCULOS_ANTERIORES'] = result_dict

                if rule.code in linhas_digitadas:
                    linha = linhas_digitadas[rule.code]
                    valor_anterior = rule.code in localdict and localdict[rule.code] or 0.0

                    localdict[rule.code] = D(linha.total)
                    localdict[rule.code + '_taxa' ] = D(linha.rate)
                    localdict[rule.code + '_base'] = linha.amount
                    localdict[rule.code + '_quantidade'] = linha.quantity

                    rules[rule.code] = rule
                    # sum the amount for its salary category
                    #localdict = _sum_salary_rule_category(localdict, rule.category_id, linha.total - valor_anterior)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': D(linha.amount).quantize(D('0.01')),
                        'employee_id': contract.employee_id.id,
                        'quantity': D(linha.quantity),
                        'rate': D(linha.rate),
                        'total': D(linha.total),
                        'sinal': linha.category_id.sinal,
                        'digitado': True,
                        'simulacao_id': linha.simulacao_id.id if linha.simulacao_id else False,
                    }

                elif rule.code in regra_funcionario_com_valor:
                    regra_valor = regra_funcionario_com_valor[rule.code]
                    amount = D(regra_valor.valor)
                    qty = D(regra_valor.quantidade)
                    rate = D(regra_valor.porcentagem)

                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = D(str(amount)) * D(str(qty)) * D(str(rate)) / D('100.00')

                    if rule.code.strip() in ['INSS', 'INSS_13', 'FGTS']:
                        tot_rule = tot_rule.quantize(D('0.01'), rounding=ROUND_DOWN)
                        #tot_rule = float(str(tot_rule))
                    else:
                        tot_rule = tot_rule.quantize(D('0.01'))

                    #tot_rule = float(str(tot_rule))
                    localdict[rule.code] = tot_rule
                    localdict[rule.code + 'taxa'] = rate
                    localdict[rule.code + '_base'] = amount
                    localdict[rule.code + '_quantidade'] = qty
                    rules[rule.code] = rule
                    # sum the amount for its salary category
                    #localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': D(amount).quantize(D('0.01')),
                        'employee_id': contract.employee_id.id,
                        'quantity': D(qty),
                        'rate': D(rate),
                        'total': D(tot_rule),
                        'sinal': rule.category_id.sinal,
                        'digitado': False,
                    }

                else:
                    if not (obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist):
                        # blacklist this rule and its children
                        blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]
                        continue

                    else:
                        ##if rule.code == 'PERICULOSIDADE':
                            ##print('periculosidade')
                            ##print(localdict['categoria'].BASE, localdict['categoria'].PROV)
                        # compute the amount of the rule
                        amount, qty, rate, aparece_no_holerite, forca_valor, forca_quantidade, forca_porcentagem, forca_total, categoria_id, simulacao_id = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                        amount = D(amount)
                        qty = D(qty)
                        rate = D(rate)
                        # check if there is already a rule computed with that code
                        previous_amount = rule.code in localdict and localdict[rule.code] or D(0)
                        previous_amount = D(previous_amount)
                        # set/overwrite the amount computed for this rule in the localdict
                        tot_rule = D(str(amount)) * D(str(qty)) * D(str(rate)) / D('100.00')

                        if categoria_id is None:
                            categoria_id = rule.category_id

                        if rule.code.strip() in ['INSS', 'INSS_13']:
                            tot_rule = tot_rule.quantize(D('0.01'), rounding=ROUND_DOWN)
                            tot_rule = D(tot_rule)
                        else:
                            tot_rule = tot_rule.quantize(D('0.01'))

                        if forca_valor is not None:
                            amount = D(forca_valor)

                        if forca_quantidade is not None:
                            qty = D(forca_quantidade)

                        if forca_porcentagem is not None:
                            rate = D(forca_porcentagem)

                        if forca_total is not None:
                            tot_rule = D(forca_total)

                        tot_rule = D(tot_rule)
                        localdict[rule.code] = tot_rule
                        localdict[rule.code + '_taxa'] = rate
                        localdict[rule.code + '_base'] = amount
                        localdict[rule.code + '_quantidade'] = qty
                        rules[rule.code] = rule

                        ##if rule.code == 'PERICULOSIDADE':
                            ##print('periculosidade')
                            ##print(tot_rule)
                        #
                        # Pega todos os float do localdict e converte para Decimal
                        #
                        localdict['Decimal'] = D
                        localdict['D'] = D

                        for item, valor in localdict.iteritems():
                            if isinstance(valor, float):
                                localdict[item] = D(valor)

                        #
                        # Acumula o total da categoria...
                        #
                        #localdict = _sum_salary_rule_category(localdict, categoria_id, tot_rule - previous_amount)

                        # create/overwrite the rule in the temporary results
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': categoria_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': aparece_no_holerite,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': D(amount).quantize(D('0.01')),
                            'employee_id': contract.employee_id.id,
                            'quantity': D(qty),
                            'rate': D(rate),
                            'total': D(tot_rule),
                            'sinal': categoria_id.sinal,
                            'digitado': False,
                            'simulacao_id': simulacao_id,
                        }

                        diferenca_valor = D(0)
                        diferenca_total = D(0)
                        if 'SALFAM' + '-' + str(contract.id) in result_dict:
                            diferenca_valor = result_dict['SALFAM' + '-' + str(contract.id)]['total']
                            diferenca_total = result_dict['SALFAM' + '-' + str(contract.id)]['total']

                        #
                        # O valor da rubrica deu negativo, vamos lançar o ajuste
                        # para quando recalcular dê o valor correto
                        #
                        if (tot_rule < diferenca_total or tot_rule < 0) and rule.regra_saldo_devedor_id:
                            #
                            # Deixamos no caso somente o salário família, se houver
                            #
                            result_dict[key]['total'] = D(diferenca_valor)
                            result_dict[key]['amount'] = D(diferenca_total)

                            #
                            # E, agora, lançamos a regra de ajuste
                            # copiando a regra atual, e só alterando o valor
                            #
                            regra_ajuste = rule.regra_saldo_devedor_id
                            dados_regra_ajuste = copy(result_dict[key])
                            dados_regra_ajuste.update({
                                'salary_rule_id': regra_ajuste.id,
                                'name': regra_ajuste.name,
                                'code': regra_ajuste.code,
                                'category_id': regra_ajuste.category_id.id,
                                'sequence': regra_ajuste.sequence,
                                'condition_select': regra_ajuste.condition_select,
                                'condition_python': regra_ajuste.condition_python,
                                'condition_range': regra_ajuste.condition_range,
                                'condition_range_min': regra_ajuste.condition_range_min,
                                'condition_range_max': regra_ajuste.condition_range_max,
                                'amount_select': regra_ajuste.amount_select,
                                'amount_fix': regra_ajuste.amount_fix,
                                'amount_python_compute': regra_ajuste.amount_python_compute,
                                'amount_percentage': regra_ajuste.amount_percentage,
                                'amount_percentage_base': regra_ajuste.amount_percentage_base,
                                'sinal': regra_ajuste.category_id.sinal,
                                'total': D((tot_rule * -1) + diferenca_total).quantize(D('0.01')),
                                'amount': D((amount * -1) + diferenca_valor).quantize(D('0.01')),
                            })
                            result_dict[regra_ajuste.code] = dados_regra_ajuste

                if key in result_dict:
                    result_dict[key]['sinal'] = rule.category_id.sinal
                    result_dict[key]['category_id'] = rule.category_id.id

                    #print(key)

                    valores = result_dict[key]
                    #
                    # Acrescenta na descrição "média" quando for média
                    #
                    if valores['code'] in medias or valores['code'].replace('DSR_', '') in medias:
                        if valores['code'] in medias:
                            media = medias[valores['code']]
                        elif valores['code'].replace('DSR_', '') in medias:
                            media = medias[valores['code'].replace('DSR_', '')]

                        if valores['code'] == 'LICENCA_MATERNIDADE':
                            valores['name'] = valores['name'] + u' 13º'

                        else:
                            #print(key, media.tipo_media)
                            if media.tipo_media != 'calculada':
                                valores['name'] = u'Média ' + valores['name']

                            if holerite_obj.tipo == 'F' and holerite_obj.abono_pecuniario_ferias:
                                valores_abono = copy(valores)

                                if media.tipo_media == 'quantidade':
                                    valores['quantity'] *= holerite_obj.dias_ferias / D(30)
                                #elif media.tipo_media == 'valor':
                                else:
                                    valores['amount'] *= holerite_obj.dias_ferias / D(30)

                                valores['total'] = valores['amount'] * valores['quantity'] * valores['rate'] / D(100)

                    elif rule.tipo_media == 'calculada':
                        if holerite_obj.tipo == 'F' and holerite_obj.abono_pecuniario_ferias:
                            valores_abono = copy(valores)

                            if rule.tipo_media == 'quantidade':
                                valores['quantity'] *= holerite_obj.dias_ferias / D(30)
                            #elif media.tipo_media == 'valor':
                            else:
                                valores['amount'] *= holerite_obj.dias_ferias / D(30)

                            valores['total'] = valores['amount'] * valores['quantity'] * valores['rate'] / D(100)

                    localdict = _sum_salary_rule_category(localdict, rule.category_id, valores['total'])

                    #
                    # Trata agora as rubricas que são média, da parte do abono nas férias
                    #
                    if (valores['code'] in medias or valores['code'].replace('DSR_', '') in medias or rule.tipo_media == 'calculada') and \
                        holerite_obj.tipo == 'F' and holerite_obj.abono_pecuniario_ferias:
                        #media.tipo_media != 'calculada' and \

                        if rule.tipo_media == 'calculada' or media.tipo_media == 'valor':
                            #
                            # E refaz a proporção do abono
                            #
                            valores_abono['amount'] *= (30 - holerite_obj.dias_ferias) / D(30)

                        else:
                            #
                            # E refaz a proporção do abono
                            #
                            valores_abono['quantity'] *= (30 - holerite_obj.dias_ferias) / D(30)

                        valores_abono['total'] = valores_abono['amount'] * valores_abono['quantity'] * valores_abono['rate'] / D(100)
                        valores_abono['name'] += u' abono'
                        valores_abono['code'] += '_ABONO'
                        valores_abono['sequence'] -= D('0.01')
                        result_dict[valores_abono['code'] + '-' + str(contract.id)] = valores_abono

                        if valores['category_id'] in [localdict['PROVENTO_TRIBUTADO'].id, localdict['PROVENTO_SOBRE_PROVENTO'].id]:
                            valores_abono['category_id'] = localdict['PROVENTO_NAO_TRIBUTADO'].id
                            localdict = _sum_salary_rule_category(localdict, localdict['PROVENTO_NAO_TRIBUTADO'], valores_abono['total'])

                        localdict[rule.code + '_taxa'] = valores['rate']
                        localdict[rule.code + '_base'] = valores['amount']
                        localdict[rule.code + '_quantidade'] = valores['quantity']
                        localdict[rule.code + '_ABONO_taxa'] = valores_abono['rate']
                        localdict[rule.code + '_ABONO_base'] = valores_abono['amount']
                        localdict[rule.code + '_ABONO_quantidade'] = valores_abono['quantity']

                #
                # Reacumula as categorias
                #
                categories_dict = {}
                categories_obj = BrowsableObject(self.pool, cr, uid, holerite_obj.contract_id.id, categories_dict)
                localdict['categories'] = categories_obj
                localdict['categoria'] = categories_obj

                for key in result_dict:
                    if '_anterior' in key:
                        continue

                    #
                    # As rubricas de abono foram somadas nos proventos não tributados mais acima
                    #
                    if key[-6:] == '_ABONO' in key:
                        continue

                    linha = result_dict[key]
                    localdict = _sum_salary_rule_category(localdict, linha['category_id'], linha['total'])

        result = []
        for codigo, valores in result_dict.items():
            result.append(valores)

        #result = [value for code, value in result_dict.items()]

        #
        # Ajusta o Saldo Devedor para o próximo mês
        #
        if holerite_obj.tipo == 'N':
            regras_pool = self.pool.get('hr.salary.rule')
            contrato_regras_pool = self.pool.get('hr.contract_regra')

            data_inicial = parse_datetime(holerite_obj.date_to).date() + relativedelta(days=+1)
            data_inicial, data_final = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
            desconto_saldo_devedor_id = regras_pool.search(cr, uid, [('code', '=', 'DESC_SALDO_DEV')])[0]

            rubrica_desc_saldo_dev_ids = contrato_regras_pool.search(cr, 1, [('data_inicial', '=', str(data_inicial)), ('data_final', '=', str(data_final)), ('contract_id', '=', holerite_obj.contract_id.id), ('rule_id', '=', desconto_saldo_devedor_id)])
            contrato_regras_pool.unlink(cr, 1, rubrica_desc_saldo_dev_ids)

            if 'SALDO_DEVEDOR' in result_dict and result_dict['SALDO_DEVEDOR']['total'] > 0:
                desconto_saldo_devedor_obj = regras_pool.browse(cr, uid, desconto_saldo_devedor_id)
                dados = {
                    'contract_id': holerite_obj.contract_id.id,
                    'rule_id': desconto_saldo_devedor_obj.id,
                    'data_inicial': str(data_inicial),
                    'data_final': str(data_final),
                    'quantidade': 1,
                    'porcentagem': 100,
                    'valor': result_dict['SALDO_DEVEDOR']['total'],
                }
                contrato_regras_pool.create(cr, 1, dados)


        return result

    def ajusta_inss(self, cr, uid, ids, context={}):
        def dic_regra(holerite_obj, regra_obj, local_dict):
            item_pool = self.pool.get('hr.payslip.line')
            regra_pool = self.pool.get('hr.salary.rule')
            local_dict['holerite'] = holerite_obj
            local_dict['contrato'] = holerite_obj.contract_id
            local_dict['empregado'] = holerite_obj.employee_id

            valor, quantidade, porcentagem, aparece_no_holerite, forca_valor, forca_quantidade, forca_porcentagem, categoria_id, simulacao_id = regra_pool.compute_rule(cr, uid, regra_obj.id, localdict=local_dict)

            dados = {
                'slip_id': holerite_obj.id,
                'contract_id': holerite_obj.contract_id.id,
                'employee_id': holerite_obj.employee_id.id,
                'company_id':  holerite_obj.contract_id.company_id.id,
                'salary_rule_id': regra_obj.id,
                'name': regra_obj.name,
                'code': regra_obj.code,
                'category_id': regra_obj.category_id.id,
                'sequence': regra_obj.sequence,
                'appears_on_payslip': True,
                'condition_select': regra_obj.condition_select,
                'condition_python': regra_obj.condition_python,
                'condition_range': regra_obj.condition_range,
                'condition_range_min': regra_obj.condition_range_min,
                'condition_range_max': regra_obj.condition_range_max,
                'amount_select': regra_obj.amount_select,
                'amount_fix': regra_obj.amount_fix,
                'amount_python_compute': regra_obj.amount_python_compute,
                'amount_percentage': regra_obj.amount_percentage,
                'amount_percentage_base': regra_obj.amount_percentage_base,
                'register_id': regra_obj.register_id.id,
                'amount': D(valor).quantize(D('0.01')),
                'employee_id': holerite_obj.employee_id.id,
                'quantity': D(quantidade),
                'rate': D(porcentagem),
                'total': D(D(quantidade) * D(valor) * (D(porcentagem) / D('100.00'))).quantize(D('0.01')),
                'digitado': False,
                'simulacao_id': simulacao_id
            }

            item_ids = item_pool.search(cr, uid, [('slip_id', '=', holerite_obj.id), ('salary_rule_id', '=', regra_obj.id)])
            if len(item_ids) > 0:
                item_pool.unlink(cr, uid, item_ids)

            item_pool.create(cr, uid, dados)
            #print(local_dict)
            local_dict[regra_obj.code] = dados['total']
            local_dict[regra_obj.code + '_taxa'] = dados['rate']
            return local_dict

        regras_pool = self.pool.get('hr.salary.rule')

        regras_inss_ids = regras_pool.search(cr, uid, ['|', ('code', 'in', ['INSS_EMPRESA', 'INSS_OUTRAS_ENTIDADES', 'INSS_RAT', 'INSS_FAP_AJUSTADO', 'INSS_EMPRESA_TOTAL', 'INSS_DEDUCAO_PREVIDENCIARIA', 'DEDUCAO_DEPENDENTES', 'BASE_FGTS']), ('id', '=', 86)])

        regra_inss = {}
        for regra_obj in regras_pool.browse(cr, uid, regras_inss_ids):
            regra_inss[regra_obj.code] = regra_obj

        holerite_ids = self.search(cr, uid, [('struct_id', 'in', [18, 26, 34, 47, 53, 21, 37, 39, 40, 41, 43, 44, 27, 45, 56, 49])])
        # holerite_ids = [1792]

        for holerite_obj in self.browse(cr, uid, holerite_ids):
            base_inss = D(0)
            local_dict = {}

            for linha_obj in holerite_obj.line_ids:
                local_dict[linha_obj.code] = D(linha_obj.total)

            #
            # Insere as linhas de apuração
            #
            local_dict = dic_regra(holerite_obj, regra_inss['INSS_DEDUCAO_PREVIDENCIARIA'], local_dict)

            #
            # Prolabore e autonomo não tem FGTS
            #
            if holerite_obj.struct_id.id not in [56, 49]:
                local_dict = dic_regra(holerite_obj, regra_inss['BASE_FGTS'], local_dict)

            local_dict = dic_regra(holerite_obj, regra_inss['DEDUCAO_DEPENDENTES'], local_dict)

            #
            # Retorno de férias não tem INSS
            #
            if holerite_obj.struct_id.id != 27:
                local_dict = dic_regra(holerite_obj, regra_inss['INSS_EMPRESA'], local_dict)

                if holerite_obj.struct_id.id not in [56, 49]:
                    local_dict = dic_regra(holerite_obj, regra_inss['INSS_OUTRAS_ENTIDADES'], local_dict)
                    local_dict = dic_regra(holerite_obj, regra_inss['INSS_RAT'], local_dict)
                    local_dict = dic_regra(holerite_obj, regra_inss['INSS_FAP_AJUSTADO'], local_dict)

                local_dict = dic_regra(holerite_obj, regra_inss['INSS_EMPRESA_TOTAL'], local_dict)


                local_dict = dic_regra(holerite_obj, regra_inss['BASE_IRPF'], local_dict)
            #print(holerite_obj.employee_id.nome)

        return True

    def imprime_recibo_ferias(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Recibo de Férias', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_ferias.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', 'recibo_ferias.pdf')])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'recibo_ferias.pdf',
            'datas_fname': 'recibo_ferias.pdf',
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def imprime_aviso_ferias(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids
        rel = Report('Aviso de Férias', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'aviso_ferias.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', 'aviso_ferias.pdf')])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'aviso_ferias.pdf',
            'datas_fname': 'aviso_ferias.pdf',
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def imprime_recibo_pagamento(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Recibo de Pagamento', cr, uid)

        holerite_obj = self.browse(cr, uid, id)
        if holerite_obj.contract_id.categoria_trabalhador in ["701", "702", "703"]:
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_rpa.jrxml')
            recibo = 'recibo_pagamento_rpa.pdf'

        else:
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_duas_vias.jrxml')
            recibo = 'recibo_pagamento.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['EXIBE_FERIAS'] = context.get('exibe_ferias', 'N')

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def imprime_recibo_pagamento_decimo(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        holerite_obj = self.browse(cr, uid, id)
        rel = Report('Recibo de Pagamento Décimo Terceiro', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_duas_vias.jrxml')
        recibo = 'recibo_pagamento_decimo.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def imprime_analise_rescisao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Analise de Rescisao', cr, uid)

        holerite_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_analise_rescisao.jrxml')
        recibo = 'analise_rescisao.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['EXIBE_FERIAS'] = context.get('exibe_ferias', 'N')

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def rubrica_outro_periodo(self, cr, uid, ids, rubrica='', meses=-1, tipo='N', context={}, mes_todo=False, simulacao=False, mesmo_funcionario=False, do_afastamento=False):
        res = {}
        payslip_line_pool = self.pool.get('hr.payslip.line')

        for holerite_obj in self.browse(cr, uid, ids):
            if holerite_obj.tipo == 'R':
                if meses == 0 and (not do_afastamento):
                    data_inicial = parse_datetime(holerite_obj.date_from).date()
                    data_final = parse_datetime(holerite_obj.date_to).date()

                else:
                    data_final = parse_datetime(holerite_obj.data_afastamento).date()
                    data_inicial = parse_datetime(holerite_obj.data_afastamento[:8] + '01').date()

            else:
                data_inicial = parse_datetime(holerite_obj.date_from).date()
                data_final = parse_datetime(holerite_obj.date_to).date()

            if meses != 0:
                data_inicial += relativedelta(months=meses)
                data_final += relativedelta(months=meses)

            #data_final = parse_datetime(holerite_obj.date_from).date() + relativedelta(days=-1)

            if mes_todo:
                data_inicial = primeiro_dia_mes(data_inicial)
                data_final = ultimo_dia_mes(data_final)

            if isinstance(tipo, (str, unicode)):
                tipo = [tipo]

            print('data anteriores', data_inicial, data_final, tipo, rubrica)
            #
            # Busca os holerites do tipo correspondente, no período desejado
            #
            # No caso de 13º, olhamos a competência do cálculo, e não o período
            # calculado
            #

            if holerite_obj.tipo == 'D':
                if mesmo_funcionario:
                    busca = [
                        #('company_id', '=', holerite_obj.company_id.id),
                        ('employee_id', '=', holerite_obj.employee_id.id),
                        ('id', '<', holerite_obj.id),
                        #('contract_id', '=', holerite_obj.contract_id.id),
                        ('tipo', 'in', tipo),
                        ('simulacao', '=', simulacao),
                        ('ano', '=', data_inicial.year),
                        ('mes', '=', str(data_inicial.month).zfill(2)),
                    ]
                else:
                    busca = [
                        #('company_id', '=', holerite_obj.company_id.id),
                        #('employee_id', '=', holerite_obj.employee_id.id),
                        ('contract_id', '=', holerite_obj.contract_id.id),
                        ('tipo', 'in', tipo),
                        ('simulacao', '=', simulacao),
                        ('ano', '=', data_inicial.year),
                        ('mes', '=', str(data_inicial.month).zfill(2)),
                    ]

            else:
                if mesmo_funcionario:
                    busca = [
                        #('company_id', '=', holerite_obj.company_id.id),
                        ('employee_id', '=', holerite_obj.employee_id.id),
                        ('id', '<', holerite_obj.id),
                        #('contract_id', '=', holerite_obj.contract_id.id),
                        ('tipo', 'in', tipo),
                        ('date_from', '>=', str(data_inicial)),
                        ('date_to', '<=', str(data_final)),
                        ('simulacao', '=', simulacao),
                    ]
                else:
                    busca = [
                        #('company_id', '=', holerite_obj.company_id.id),
                        #('employee_id', '=', holerite_obj.employee_id.id),
                        ('contract_id', '=', holerite_obj.contract_id.id),
                        ('tipo', 'in', tipo),
                        ('date_from', '>=', str(data_inicial)),
                        ('date_to', '<=', str(data_final)),
                        ('simulacao', '=', simulacao),
                    ]


            #if not meses == 0 and not holerite_obj.complementar:
                #busca.append(('id', '=', holerite_obj.id))
            #else:
                #busca.append(('id', '!=', holerite_obj.id))

            holerite_ids = self.search(cr, uid, busca)
            print('holerite_ids', holerite_ids, busca)

            if rubrica in ['proventos', 'deducoes']:
                if len(holerite_ids):
                    res[holerite_obj.id] = self.browse(cr, uid, holerite_ids[0])
                else:
                    res[holerite_obj.id] = None

            else:
                busca_rubricas = [
                    ('code', '=', rubrica),
                    ('slip_id', 'in', holerite_ids)
                ]

                rubrica_ids = payslip_line_pool.search(cr, uid, busca_rubricas)

                print('rubrica anteriores', rubrica_ids, busca_rubricas)

                if len(rubrica_ids) > 0:
                    if mesmo_funcionario:
                        res[holerite_obj.id] = payslip_line_pool.browse(cr, uid, rubrica_ids)

                    else:
                        res[holerite_obj.id] = payslip_line_pool.browse(cr, uid, rubrica_ids[0])
                else:
                    res[holerite_obj.id] = None

        if len(ids) == 1:
            res = res.values()[0]

        print(res)

        return res

    def imprime_recisao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        rescisao_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_rescisao_contrato_trabalho.jrxml')
        recibo = 'termo_rescisao.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        #Imprime termo de Homologação

        relh = Report('Termo de Homologação de Rescisão', cr, uid)
        relh.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_homologacao_de_rescisao_de_contrato_de_trabalho.jrxml')
        reciboh = 'termo_homologacao_rescisao.pdf'

        relh.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        relh.parametros['USER_ID'] = int(uid)

        pdf, formato = relh.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', reciboh)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': reciboh,
            'datas_fname': reciboh,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        #Imprime termo de Quitação

        relq = Report('Termo de Homologação de Rescisão', cr, uid)
        relq.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_de_quitacao_de_rescisao_de_contrato_de_trabalho.jrxml')
        reciboq = 'termo_quitacao_rescisao.pdf'

        relq.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        relq.parametros['USER_ID'] = int(uid)

        pdf, formato = relq.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', reciboq)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': reciboq,
            'datas_fname': reciboq,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def imprime_seguro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        seguro_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'seguro_desemprego_verde.jrxml')
        recibo = 'seguro_desemprego.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def gera_ficha_registro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.contract_id.id

        rel = Report('Ficha Registro Funcionário', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_ficha_registro_empregado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(contract_id) + ')'
        recibo = 'hr_ficha_registro_empregado.pdf',

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'hr_ficha_registro_empregado.pdf',
            'datas_fname': 'hr_ficha_registro_empregado.pdf',
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def gera_relatorio_media(self, cr, uid, ids, context={}):
        if not ids:
            return

        for holerite_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(holerite_obj.data_inicio_periodo_aquisitivo)
            data_final = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo)

            linhas = []
            if not holerite_obj.media_ids:
                #raise osv.except_osv(u'Erro!', u'Não existe Medias calculadas!')
                self.gera_relatorio_media_2(cr, uid, ids, context=context)
                return True

            for media_obj in holerite_obj.media_ids:
                linha = DicionarioBrasil()


                sql = """select
                        coalesce(hl.total, 0 ) as total
                        from hr_payslip_media hm
                        left join hr_payslip_line hl on hl.slip_id = hm.slip_id and hl.salary_rule_id = hm.rule_id

                        where hm.id = {media_id}

                """

                sql = sql.format(media_id=media_obj.id)
                #print(sql)
                cr.execute(sql)
                dados = cr.fetchall()
                for total in dados:
                    total = total[0]

                linha['rubrica'] = media_obj.nome
                linha['tipo_media'] = media_obj.tipo_media
                linha['digitado'] = media_obj.digitado
                linha['mes_01'] = media_obj.mes_01
                linha['mes_02'] = media_obj.mes_02
                linha['mes_03'] = media_obj.mes_03
                linha['mes_04'] = media_obj.mes_04
                linha['mes_05'] = media_obj.mes_05
                linha['mes_06'] = media_obj.mes_06
                linha['mes_07'] = media_obj.mes_07
                linha['mes_08'] = media_obj.mes_08
                linha['mes_09'] = media_obj.mes_09
                linha['mes_10'] = media_obj.mes_10
                linha['mes_11'] = media_obj.mes_11
                linha['mes_12'] = media_obj.mes_12
                linha['total'] = media_obj.total_texto or formata_valor(media_obj.total or 0)
                linha['meses'] = D(media_obj.meses or 0)
                linha['proporcao'] = D(media_obj.proporcao or 0)
                linha['media'] = media_obj.media_texto or formata_valor(media_obj.media or 0)
                linha['total_calculado'] = D(total or 0)


                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Médias de '
            rel.title += holerite_obj.contract_id.employee_id.nome
            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Período de '
            filtro.text += formata_data(data_inicial)
            filtro.text += ' a '
            filtro.text += formata_data(data_final)

            relatorio =  u'medias_' + holerite_obj.contract_id.employee_id.nome + u'.pdf'

            rel.colunas = [
                ['rubrica', 'C', 30, u'Rubrica', False, None],
                ['tipo_media', 'C', 5, u'Tipo', False, None],
                ['digitado', 'B', 4, u'Digitado', False, None],
                ['mes_01', 'C', 14, u'1º mês', False, 'D'],
                ['mes_02', 'C', 14, u'2º mês', False, 'D'],
                ['mes_03', 'C', 14, u'3º mês', False, 'D'],
                ['mes_04', 'C', 14, u'4º mês', False, 'D'],
                ['mes_05', 'C', 14, u'5º mês', False, 'D'],
                ['mes_06', 'C', 14, u'6º mês', False, 'D'],
                ['mes_07', 'C', 14, u'7º mês', False, 'D'],
                ['mes_08', 'C', 14, u'8º mês', False, 'D'],
                ['mes_09', 'C', 14, u'9º mês', False, 'D'],
                ['mes_10', 'C', 14, u'10º mês', False, 'D'],
                ['mes_11', 'C', 14, u'11º mês', False, 'D'],
                ['mes_12', 'C', 14, u'12º mês', False, 'D'],
                ['total', 'C', 14, u'Total', False, 'D'],
                ['meses', 'F', 5, u'Meses', False, None],
                ['proporcao', 'F', 5, u'Proporção', False, None],
                ['media', 'C', 14, u'Média', False, 'D'],
                ['total_calculado', 'F', 15, u'Total Media', False, None],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['servico', u'Serviço', False],
                #['tipo', u'Tipo', False],
            #]
            #rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)
            #csv = gera_relatorio_csv(rel, linhas)

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', holerite_obj.id), ('name', '=', relatorio)])

            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': relatorio,
                'datas_fname': relatorio,
                'res_model': 'hr.payslip',
                'res_id': holerite_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

            return True


    def gera_relatorio_media_2(self, cr, uid, ids, context={}):
        if not ids:
            return

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        slips = []
        if rel_obj.tipo == 'R' or not rel_obj.media_ids:
            if rel_obj.line_ids:
                for slip_id in rel_obj.line_ids:
                    if slip_id.simulacao_id:
                        slips.append(slip_id.simulacao_id.id)

        else:
            if rel_obj.media_ids:
                slips.append(rel_obj.id)
            else:
                raise osv.except_osv(u'Erro!', u'Não existe Medias calculadas!')

        #print(slips)

        rel = Report('Ficha Registro Funcionário', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_media_rubrica.jrxml')
        rel.parametros['SLIPS_IDS'] = str(tuple(slips)).replace("u'", "'").replace(',)', ')')
        recibo = 'hr_relatorio_media_rubrica.pdf',

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])

        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'hr_relatorio_media_rubrica.pdf',
            'datas_fname': 'hr_relatorio_media_rubrica.pdf',
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def fecha_holerite(self, cr, uid, ids, context={}):
        for holerite_obj in self.pool.get('hr.payslip').browse(cr, uid, ids):
            cr.execute("update hr_payslip set paid = True, state = 'done' where id = " + str(holerite_obj.id) + ";")

            if holerite_obj.tipo == 'R' and (not holerite_obj.simulacao):
                self.pool.get('hr.contract').write(cr, uid, [holerite_obj.contract_id.id], {'date_end': holerite_obj.data_afastamento})

        return True

    def abre_holerite(self, cr, uid, ids, context={}):
        holerite_pool = self.pool.get('hr.payslip')

        if uid != 1:
            for holerite_obj in holerite_pool.browse(cr, uid, ids):
                if 'remessa_id' in holerite_pool._columns and holerite_obj.remessa_id:
                    raise osv.except_osv(u'Erro!', u'Você não pode reabrir um cálculo que já havia sido conferido e fechado, e enviado para o banco para pagamento!')

            raise osv.except_osv(u'Erro!', u'Você não tem permissão de reabrir um cálculo que já havia sido conferido e fechado!')

        for id in ids:
            cr.execute("update hr_payslip set state = 'draft' where id = " + str(id) + ";")

        return True

    def unlink(self, cr, uid, ids, context={}):

        for holerite_obj in self.pool.get('hr.payslip').browse(cr, uid, ids):
            if holerite_obj and holerite_obj.state and holerite_obj.state == 'done':
                raise osv.except_osv(u'Erro!', u'Não é permitida a exclusão de cálculo fechado!')

            #
            # Trata a exclusão/desvinculação das variáveis do holerite
            #
            for input_obj in holerite_obj.input_line_ids:
                if holerite_obj.tipo in ('N', 'R'):
                    input_obj.write({'payslip_id': False})
                else:
                    input_obj.unlink()

        res = super(hr_payslip, self).unlink(cr, uid, ids, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if not dados:
            return True

        if not isinstance(ids, (list, tuple)):
            lista_ids = [ids]
        else:
            lista_ids = ids

        if len(dados) > 1:
            #
            # Permite regerar o seguro desemprego
            #
            if len(dados) == 3 \
                and 'nome_arquivo_seguro' in dados \
                and 'arquivo_seguro' in dados \
                and 'arquivo_texto_seguro' in dados:
                pass

            else:
                for so in self.pool.get('hr.payslip').browse(cr, uid, lista_ids):
                    if so.state == 'done':
                        raise osv.except_osv(u'Erro!', u'Não é permitida a alteração de cálculo fechado!')

        res = super(hr_payslip, self).write(cr, uid, ids, dados, context=context)

        return res

    def create(self, cr, uid, dados, context={}):
        if dados['tipo'] == 'R':
            sql = """
                select coalesce(count(*), 0)
                from hr_payslip h
                where
                    h.tipo not in ('F', 'D', 'A')
                    and (h.simulacao is null
                    or h.simulacao = false)
                    and h.contract_id = {contract_id}
                    and (
                        (
                            h.tipo != 'R'
                            and to_char(h.date_from, 'YYYY-MM') = to_char(cast('{data_afastamento}' as date), 'YYYY-MM')
                        )
                        or
                        (
                            h.tipo = 'R'
                            and to_char(h.data_afastamento, 'YYYY-MM') = to_char(cast('{data_afastamento}' as date), 'YYYY-MM')
                        )
                    );
            """
        else:
            sql = """
                select coalesce(count(*), 0)
                from hr_payslip h
                     join hr_contract c on c.id = h.contract_id
                where
                    h.tipo not in ('F', 'D', 'A')
                    and (h.simulacao is null
                    or h.simulacao = false)
                    and h.contract_id = {contract_id}
                    -- RPA pode vários recibos no mês
                    and c.categoria_trabalhador not in ('701','702','703')
                    and (
                        (
                            h.tipo != 'R'
                            and to_char(h.date_from, 'YYYY-MM') = to_char(cast('{date_from}' as date), 'YYYY-MM')
                        )
                        or
                        (
                            h.tipo = 'R'
                            and to_char(h.data_afastamento, 'YYYY-MM') = to_char(cast('{date_from}' as date), 'YYYY-MM')
                        )
                    );
            """
        sql = sql.format(**dados)

        print(sql)
        print(dados)

        if '__copy_data_seen' not in context and ('simulacao' not in dados or dados['simulacao'] == False):
            cr.execute(sql)

            ja_existe = cr.fetchall()[0][0]
            estrutura = self.pool.get('hr.payroll.structure').browse(cr, uid, dados['struct_id'])

            if ja_existe:
                mes = parse_datetime(dados['date_from']).date().month
                nome_func = self.pool.get('hr.employee').read(cr, uid, dados['employee_id'], ['name'])

                if mes not in [1, 2]:
                    if ja_existe != 0 and ('COMPLEMENTAR' not in estrutura.name.upper() and u'13º' not in estrutura.name.upper()):
                        raise osv.except_osv(u'Inválido !', u'Cálculo em duplicidade para o funcionário {nome}!'.format(nome=nome_func))
                elif ja_existe > 1:
                    raise osv.except_osv(u'Inválido !', u'Cálculo triplicado para o funcionário {nome}!'.format(nome=nome_func))

        return super(hr_payslip, self).create(cr, uid, dados, context=context)

    def abono_pecuniario_ferias_change(self, cr, uid, ids, abono_pecuniario_ferias, date_from, date_to):
        if not ids:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        if abono_pecuniario_ferias:
            date_to = parse_datetime(date_from).date() + relativedelta(days=+19)
        else:
            date_to = parse_datetime(date_from).date() + relativedelta(days=+29)

        valores['date_to'] = str(date_to)

        return res

    def cria_apaga_variavel(self, cr, uid, ids, valor=0, codigo='DIFERENCA_INSS', context={}):
        rule_ids = self.pool.get('hr.salary.rule').search(cr, uid, [('code', '=', codigo)])

        if not rule_ids:
            return

        rule_id = rule_ids[0]

        for holerite_obj in self.browse(cr, uid, ids):
            achou_obj = None

            for var_obj in holerite_obj.input_line_ids:
                if var_obj.code == codigo:
                    achou_obj = var_obj
                    break

            if valor == 0:
                if achou_obj is not None:
                    achou_obj.unlink()

            else:
                if achou_obj is not None:
                    achou_obj.write({'amount': valor})
                else:
                    dados = {
                        'payslip_id': holerite_obj.id,
                        'contract_id': holerite_obj.contract_id.id,
                        'employee_id': holerite_obj.employee_id.id,
                        'rule_id': rule_id,
                        'amount': valor,
                        'data_inicial': holerite_obj.date_from,
                        'data_final': holerite_obj.date_to,
                    }
                    self.pool.get('hr.payslip.input').create(cr, uid, dados)
