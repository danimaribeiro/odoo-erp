#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
import os
from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

MESES_DIC = dict(MESES)

TIPOS = (
    ('T', 'Todos'),
    ('N', 'Holerite normal'),
    ('R', 'Rescisões'),
    ('D', '13º salário'),
)

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


class hr_rubrica_mes(osv.osv_memory):
    _name = 'hr.rubrica.mes'
    _description = u'Rubricas do holerite'
    _order = 'company_id'
    _rec_name = 'company_id'


    def _get_input_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        if not ids:
            return {}

        for ru_obj in self.browse(cr, uid, ids):
            sql = u"""
            select
                hp.id
                from hr_payslip_line hp
                join hr_payslip h on h.id = hp.slip_id
                join hr_salary_rule r on r.id = hp.salary_rule_id
                join hr_contract ct on ct.id = h.contract_id
                join res_company c on c.id = ct.company_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id

            where
                (
                    hp.salary_rule_id = {rule_id} or
                    r.code like '{similar}'
                ) and
                (c.id = {company_id}
                or c.parent_id = {company_id}
                or cc.parent_id = {company_id}
                )
                and h.simulacao = False
                """

            dados = {

                'tipo': ru_obj.data_inicial,
                'data_inicial': ru_obj.data_inicial,
                'data_final': ru_obj.data_final,
                'company_id': ru_obj.company_id.id,
                'rule_id': ru_obj.rule_id.id,
                'similar': '%' if not ru_obj.rubricas_similares else ru_obj.rule_id.code,
            }
            
            
            if ru_obj.tipo == 'N':
                sql += u'''
                and                
                    h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                '''

            if ru_obj.tipo == 'D':
                sql += u'''
                and                
                    h.tipo = 'D' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                '''
                
            if ru_obj.tipo == 'R':
                sql += u'''
                and
                    h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}'
                '''   
                      
            if ru_obj.tipo == 'T':
                sql += u'''
                and
                    h.tipo in ('N','R','F','D') and 
                    (
                        h.date_from between '{data_inicial}' and '{data_final}'
                        or h.data_afastamento between '{data_inicial}' and '{data_final}'
                    )
                '''       

            if ru_obj.partner_id:
                sql += u'''
                and ct.sindicato_id = {sindicato_id}
                '''
                dados['sindicato_id'] = ru_obj.partner_id.id

            if ru_obj.employee_id:
                sql += u'''
                and h.employee_id = {employee_id}
                '''
                dados['employee_id'] = ru_obj.employee_id.id

            print(sql.format(**dados))
            cr.execute(sql.format(**dados))

            busca = []
            for ret in cr.fetchall():
                busca.append(ret[0])

            res = {}
            if ids:
                for id in ids:
                    res[id] = busca
            else:
                res = busca

            return res


    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'tipo': fields.selection(TIPOS, u'Tipo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Sindicato'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'rubricas_similares': fields.boolean(u'Rubricas similares?'),
        'input_ids': fields.function(_get_input_ids, method=True, type='one2many', string=u'Entradas variáveis', relation='hr.payslip.line'),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'tipo': 'T',
        'rubricas_similares': True,
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.payslip', context=c),
    }

    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        return retorno

    def busca_entradas(self, cr, uid, ids, context={}):
        valores = {}
        retorno = {'value': valores}

        if 'ano' not in context or 'mes' not in context:
            return retorno

        ano = context['ano']
        mes = context['mes']

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        valores['input_ids'] = self._get_input_ids(cr, uid, ids, 'input_ids', context=context)

        return retorno
    
    def gera_relatorio_rubrica_mes(self, cr, uid, ids,input_ids, context={}):
        if not ids and not input_ids:
            return False

        id = ids[0]
        rubrica_obj = self.browse(cr, uid, id)
        company_id = rubrica_obj.company_id.id
        data_inicial = parse_datetime(rubrica_obj.data_inicial).date()
        data_final = parse_datetime(rubrica_obj.data_final).date()
        
        linha = []
        for linha_obj in rubrica_obj.input_ids:
            linha.append(linha_obj.id) 

        rel = Report('Resumo de Resultado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_rubrica_mes.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]      
        rel.parametros['RUBRICA'] =  str(linha).replace('[', '(').replace(']', ')')
             

        pdf, formato = rel.execute()
        
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.rubrica.mes'), ('res_id', '=', id), ('name', '=', 'rubrica_mes.pdf')])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'rubrica_mes.pdf',
            'datas_fname': 'rubrica_mes.pdf',
            'res_model': 'hr.rubrica.mes',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True


hr_rubrica_mes()
