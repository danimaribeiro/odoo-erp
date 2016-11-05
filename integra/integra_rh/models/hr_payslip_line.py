# -*- coding:utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from pybrasil.valor.decimal import Decimal as D, ROUND_DOWN
from copy import copy
from integra_rh.constantes_rh import TIPO_AFASTAMENTO
from hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from osv import fields, osv
from finan.wizard.finan_relatorio import Report
from collections import OrderedDict
import os
import base64

from hr_salary_rule import *
from pybrasil.data import parse_datetime, idade, agora, hoje as hoje_brasil, dia_util_pagamento, primeiro_dia_mes, ultimo_dia_mes

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


TIPO_MEDIA = [
    ('valor', u'Valor'),
    ('quantidade', u'Quantidade'),
    ('calculada', u'Calculada normalmente'),
    ('afastamento', u'Dias de afastamento'),
]

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


class hr_payslip_line(osv.osv):
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, ano desc, mes desc, sequence, name, id'

    def _calculate_total(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.digitado:
                valor = line.total

            else:
                valor = D(str(line.quantity)) * D(str(line.amount)) * D(str(line.rate)) / D('100.00')
                if line.code in ['INSS', 'INSS_13', 'FGTS']:
                    valor = valor.quantize(D('0.01'), rounding=ROUND_DOWN)
                else:
                    valor = valor.quantize(D('0.01'))

            res[line.id] = float(str(valor))

        return res

    def _provento_desconto(self, cr, uid, ids, nome_campo, args, context={}):
        res = {}

        for linha_obj in self.browse(cr, uid, ids, context=context):
            res[linha_obj.id] = D('0')
            if nome_campo == 'provento' and linha_obj.sinal == '+':
                res[linha_obj.id] = D(str(linha_obj.total)).quantize(D('0.01'))
            elif nome_campo == 'deducao' and linha_obj.sinal == '-':
                res[linha_obj.id] = D(str(linha_obj.total)).quantize(D('0.01'))
            elif nome_campo == 'base' and linha_obj.sinal == '0':
                res[linha_obj.id] = D(str(linha_obj.total)).quantize(D('0.01'))

        return res

    _columns = {
        'slip_id': fields.many2one('hr.payslip', 'Pay Slip', required=False, ondelete='cascade', select=True),
        'salary_rule_id': fields.many2one('hr.salary.rule', 'Rule', required=True, select=True),
        'sequence': fields.float(u'Sequência', select=True),
        #'employee_id': fields.many2one('hr.employee', 'Employee', required=True, select=True),
        #'contract_id': fields.many2one('hr.contract', 'Contract', required=True, select=True),
        'employee_id': fields.related('slip_id', 'employee_id', string=u'Funcionário', type='many2one', relation='hr.employee', store=True),
        'contract_id': fields.related('slip_id', 'contract_id', string=u'Contrato', type='many2one', relation='hr.contract', store=True),
        'company_id': fields.related('slip_id', 'company_id', string=u'Empresa', type='many2one', relation='res.company', store=True),
        'rate': fields.float('Rate (%)', digits=(18, 6)),
        'amount': fields.float('Amount', digits=(21, 10)),

        'quantity': fields.float(u'Quantidade', digits=(18, 2)),
        'horas': fields.float(u'Horas'),

        'total_calculado': fields.function(_calculate_total, method=True, type='float', string=u'Total calculado', digits=(18, 2), store=True),
        'total': fields.float(u'Total', digits=(18, 2)),
        'holerite_anterior_line_id': fields.many2one('hr.payslip.line', u'Holerite anterior', ondelete='restrict'),
        'digitado': fields.boolean(u'Digitado?'),
        'digitado_media': fields.boolean(u'Digitado média?'),
        'tipo_media': fields.related('salary_rule_id', 'tipo_media', type='selection', selection=TIPO_MEDIA, string=u'Média para férias/13º'),

        # 'sinal': fields.char(u'Sinal', size=1),
        'rubrica_rescisao_id': fields.related('salary_rule_id', 'rubrica_rescisao_id', type='many2one', relation='hr.rubrica.rescisao', string=u'Rubrica para Rescisão'),
        'sinal': fields.related('category_id', 'sinal', string=u'Sinal', store=False),
        'condition_select': fields.selection([('none', 'Always True'), ('range', 'Range'), ('python', 'Python Expression'), ('manual', u'Manual')], "Condition Based on", required=True),
        # 'condition_range':fields.char('Range Based on',size=1024, readonly=False, help='This will be used to compute the % fields values; in general it is on basic, but you can also use categories code fields in lowercase as a variable names (hra, ma, lta, etc.) and the variable basic.'),
        # 'condition_python':fields.text('Python Condition', required=True, readonly=False, help='Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.'),#old name = conditions
        # 'condition_range_min': fields.float('Minimum Range', required=False, help="The minimum amount, applied for this rule."),
        # 'condition_range_max': fields.float('Maximum Range', required=False, help="The maximum amount, applied for this rule."),
        'amount_select':fields.selection([
            ('percentage', 'Percentage (%)'),
            ('fix', 'Fixed Amount'),
            ('code', 'Python Code'),
            ('manual', u'Manual'),
        ], 'Amount Type', select=True, required=True, help="The computation method for the rule amount."),
        # 'amount_fix': fields.float('Fixed Amount', digits_compute=dp.get_precision('Payroll'),),
        # 'amount_percentage': fields.float('Percentage (%)', digits_compute=dp.get_precision('Payroll Rate'), help='For example, enter 50.0 to apply a percentage of 50%'),
        # 'amount_python_compute':fields.text('Python Code'),
        # 'amount_percentage_base':fields.char('Percentage based on',size=1024, required=False, readonly=False, help='result will be affected to a variable'),
        'provento': fields.function(_provento_desconto, type='float', string=u'Provento', digits=(18, 2), store=False),
        'deducao': fields.function(_provento_desconto, type='float', string=u'Dedução', digits=(18, 2), store=False),
        'base': fields.function(_provento_desconto, type='float', string=u'Base', digits=(18, 2), store=False),
        'simulacao_id': fields.many2one('hr.payslip', u'Simulação'),
        'ano': fields.related('slip_id', 'ano', type='integer', string=u'Ano', store=True, select=True),
        'mes': fields.related('slip_id', 'mes', type='char', selection=MESES, string=u'Mês', store=True, select=True),
        #'code': fields.related('salary_rule_id', 'code', type='char', string=u'Código', store=True, select=True),
        #'name': fields.related('salary_rule_id', 'name', type='char', string=u'Descrição'),
        #'name':fields.char('Name', size=256),
        #'code':fields.char('Code', size=64),
        #'category_id':fields.many2one('hr.salary.rule.category', 'Category'),

        'valor_novo': fields.float(u'Valor novo'),
        'total_novo': fields.float(u'Total novo'),
        'diferenca': fields.float(u'Diferença'),
    }

    _defaults = {
        'quantity': 1.0,
        'rate': 100.0,
        'digitado': False,
        # 'sinal': '+',
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]).zfill(2),
    }


    def onchange_contract_id(self, cr, uid, ids, contract_id):
        res = {}
        valores = {}
        res['value'] = valores

        if not contract_id:
            return res

        contract_pool = self.pool.get('hr.contract')
        contract_obj = contract_pool.browse(cr, uid, contract_id)
        valores['company_id'] = contract_obj.company_id.id

        return res

    def create(self, cr, uid, dados, context={}):
        #
        # Impede a alteração dos campos related na tabela original
        #
        if 'ano' in dados:
            del dados['ano']

        if 'mes' in dados:
            del dados['mes']

        return super(hr_payslip_line, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Impede a alteração dos campos related na tabela original
        #
        if 'ano' in dados:
            del dados['ano']

        if 'mes' in dados:
            del dados['mes']

        return super(hr_payslip_line, self).write(cr, uid, ids, dados, context=context)

    #def unlink(self, cr, uid, ids, context={}):
        #pass

    def onchange_salary_rule_id(self, cr, uid, ids, salary_rule_id, context={}):
        if not salary_rule_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        rule_obj = self.pool.get('hr.salary.rule').browse(cr, uid, salary_rule_id)

        valores['tipo_media'] = rule_obj.tipo_media

        return res

    def onchange_horas(self, cr, uid, ids, horas, quantity, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not horas and not quantity:
            return res

        if horas:
            #print('horas')
            #print(horas)
            quantity = horas
            #print(quantity)
            valores['quantity'] = quantity

        else:
            #print('quantity')
            #print(quantity)
            horas = quantity
            #print(horas)
            valores['horas'] = horas

        return res


hr_payslip_line()
