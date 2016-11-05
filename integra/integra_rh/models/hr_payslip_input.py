#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
#from hr_jornada import float_time, time_float
from pybrasil.data import hora_decimal_to_horas_minutos_segundos, horario_decimal_to_hora_decimal
from hr_jornada import float_time, time_float

from osv import fields, osv


class hr_payslip_input(osv.Model):
    '''
    Payslip Input
    '''
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    def _valor(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            res[obj.id] = obj.amount

            if obj.data_inicial >= '2015-01-01' and obj.rule_id.manual_horas:
                #res[obj.id] = time_float(obj.amount)
                res[obj.id] = horario_decimal_to_hora_decimal(obj.amount or 0)

        return res

    _columns = {
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica', select=True, ondelete='restrict'),
        #
        # O código e a sequência precisam ser armazenados no banco de dados, sempre
        #
        'exige_valor': fields.related('rule_id', 'exige_valor', type='boolean', string=u'Exige valor?', store=True, select=True),
        'tipo_media': fields.related('rule_id', 'tipo_media', type='char', string=u'Tipo média', store=False, select=True),
        'sequence': fields.related('rule_id', 'sequence', type='integer', string=u'Sequência', store=True, select=True),
        'code': fields.related('rule_id', 'code', type='char', string=u'Código', store=True, select=True),
        'name': fields.related('rule_id', 'name', type='char', string=u'Descrição'),

        'employee_id': fields.many2one('hr.employee', u'Funcionário', select=True, ondelete='restrict'),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string='Empresa', store=True, select=True),

        'payslip_id': fields.many2one('hr.payslip', u'Holerite', ondelete='restrict', select=True),
        'contract_id': fields.many2one('hr.contract', string='Contrato', ondelete='restrict'),
        #'contract_id': fields.many2one('hr.contract', u'Contrato', select=True),


        #'name': fields.char('Description', size=256, required=True),
        #'sequence': fields.integer('Sequence', required=True, select=True),
        #'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
        'horas': fields.float(u'Horas'),
        'amount': fields.float(u'Valor'),
        'valor': fields.function(_valor, type='float', method=True, string=u'Valor', store=False),

        'data_inicial': fields.date(u'Data inicial', select=True),
        'data_final': fields.date(u'Data final', select=True),
    }

    _defaults = {
        #'sequence': 10,
        'amount': 0.0,
    }

    def onchange_contract_id(self, cr, uid, ids, contract_id):
        res = {}
        valores = {}
        res['value'] = valores

        if not contract_id:
            return res

        contract_pool = self.pool.get('hr.contract')
        contract_obj = contract_pool.browse(cr, uid, contract_id)
        valores['employee_id'] = contract_obj.employee_id.id
        valores['company_id'] = contract_obj.company_id.id

        return res
    
    def create(self, cr, uid, dados, context={}):
        if not context.get('calcula_medias', False):
            if 'data_inicial' in dados and 'data_final' in dados and 'rule_id' in dados and 'contract_id' in dados:
                sql = """
                    select
                        v.id,
                        r.id,
                        r.code
                    from 
                        hr_payslip_input v
                        join hr_salary_rule r on r.id = v.rule_id
                    where
                        v.payslip_id is null
                        and v.rule_id = {rule_id}
                        and v.contract_id = {contract_id}
                        and v.data_inicial = '{data_inicial}'
                        and v.data_final = '{data_final}';
                """
                
                sql = sql.format(**dados)
                #print(sql)
                cr.execute(sql)
                ja_existe = cr.fetchall()
                
                if ja_existe:
                    rule_id = ja_existe[0][1]
                    rule_code = ja_existe[0][2]
                    raise osv.except_osv(u'Inválido !', u'Variável {rule_code} em duplicidade para o funcionário {funcionario} no período!'.format(rule_code=rule_code,funcionario= dados['contract_id']))
                
        return super(hr_payslip_input, self).create(cr, uid, dados, context=context)

    def onchange_horas(self, cr, uid, ids, horas, amount, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not horas and not amount:
            return res
        
        if horas:
            print('horas')
            print(horas)
            amount = horas
            print(amount)
            valores['amount'] = amount
            
        else:
            print('amount')
            print(amount)
            horas = amount
            print(horas)
            valores['horas'] = horas

        return res
    

hr_payslip_input()


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

MESES_DIC = dict(MESES)


def mes_atual():
    hoje = parse_datetime(fields.date.today())
    return hoje.year, hoje.month


def mes_seguinte():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=+1)
    return mes_passado.year, mes_passado.month


def mes_passado():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=-1)
    return mes_passado.year, mes_passado.month


def primeiro_ultimo_dia_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = primeiro_dia + relativedelta(months=+1, days=-1)
    return str(primeiro_dia)[:10], str(ultimo_dia)[:10]
