# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora, hoje
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes
from relatorio import *
from finan.wizard.finan_relatorio import Report
import csv
from pybrasil.base import DicionarioBrasil
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes , idade_anos
from pybrasil.valor.decimal import Decimal as D
from integra_rh_caged.models.caged import limpa_caged
from dateutil.relativedelta import relativedelta
from integra_rh.models.hr_falta import TIPO_FALTA


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

SQL_PROVISAO_FERIAS_RELATORIO = open(DIR_ATUAL + '/hr_provisao_ferias_relatorio.sql').read().decode('utf-8')
SQL_PROVISAO_DECIMO_RELATORIO = open(DIR_ATUAL + '/hr_provisao_decimo_relatorio.sql').read().decode('utf-8')


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
    # ('13', 'décimo terceiro'),
)

MESES_DIC = dict(MESES)

TIPOS = (
    ('T', 'Todos'),
    ('N', 'Somente holerites'),
    ('R', 'Somente rescisões'),
    ('D', 'Somente 13º'),
    ('F', 'Somente Férias'),
)
SEXO = (
    ('M', 'Masculino'),
    ('F', 'Feminino'),
    ('', 'Ambos'),
)
#arquivo
TIPO_ATIVO_DEMITIDO = [
    ('1','Ativos'),
    ('2','Demitidos'),
]

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
    ('rtf', u'WORD'),
)
FORMATO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)


class hr_relatorio(osv.osv_memory):
    _name = 'hr.relatorio'
    _description = u'Relatórios do RH'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data do Arquivo'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'tipo': fields.selection(TIPOS, u'Tipo'),
        'sexo': fields.selection(SEXO, u'Sexo'),
        'tipo_pagamento': fields.selection((('T', 'Todos'),('N', 'Normal'), ('F', u'Férias'), ('R', u'Rescisão'), ('D', u'Décimo terceiro')), string=u'Tipo'),
        'todos': fields.boolean(u'Buscar todos'),
        'todos': fields.boolean(u'Buscar todos'),
        'tipo_funcionario': fields.selection(TIPO_ATIVO_DEMITIDO, u'Tipo'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'formato_rel': fields.selection(FORMATO, u'Formato'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'inclui_valores': fields.boolean(u'Inclui cálculos?'),
        'complementar': fields.boolean(u'Complementar?'),
        'struct_id': fields.many2one('hr.payroll.structure', u'Estrututra de Salário'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'detalhe_holerite': fields.boolean(u'Inclui detalhe dos holerites?'),
        'job_id': fields.many2one('hr.job', u'Cargo/função'),
        'somente_cnpj': fields.boolean(u'Somente este CNPJ?'),
        'is_sintetico': fields.boolean(u'Sintético?'),
        'imprime_recibo': fields.boolean(u'Imprime recibo?'),
        'curso_id': fields.many2one('hr.curso.treinamento', u'Curso'),
        'exame_id': fields.many2one('hr.exame', u'Exame'),
        'tipo_falta': fields.selection(TIPO_FALTA, string=u'Tipo', select=True),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'data': fields.date.today,
        'ano': lambda *args, **kwargs: mes_passado().year,
        'mes': lambda *args, **kwargs: str(mes_passado().month),
        'tipo': 'T',
        'formato': 'pdf',
        'formato_rel': 'pdf',
        'inclui_valores': False,
        'complementar': False,
        'detalhe_holerite': False,
    }

    def gera_listagem_ferias(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Férias Geral'
            rel.monta_contagem = False
            rel.colunas = [
                # ['employee_id.nome'       ,   'C', 60, u'Funcionário', False],
                ['contract_id.date_start' , 'D', 10, u'Admissão', False],
                ['data_inicial_periodo_aquisitivo', 'D', 10, u'Aquis. de' , False],
                ['data_final_periodo_aquisitivo'  , 'D', 10, u'Aquis. até', False],
                ['data_inicial_periodo_concessivo', 'D', 10, u'Conce. de' , False],
                ['data_final_periodo_concessivo'  , 'D', 10, u'Conce. até', False],
                ['data_inicial_periodo_gozo'      , 'D', 10, u'Gozo de' , False],
                ['data_final_periodo_gozo'        , 'D', 10, u'Gozo até', False],
                ['data_aviso'                     , 'D', 10, u'Aviso', False],
                ['data_limite_gozo'               , 'D', 10, u'Lim. gozo', False],
                ['data_limite_aviso'              , 'D', 10, u'Lim. aviso', False],
                ['data_limite_pagamento'          , 'D', 10, u'Lim.pagam.', False],
                ['faltas', 'I', 4, u'Faltas', False],
                ['afastamentos', 'I', 4, u'Afastamentos', False],
                ['dias', 'I', 4, u'Dias', False],
                ['saldo_dias', 'F', 7, u'Saldo', False],
                ['avos', 'I', 4, u'Avos', False],
                ['proporcional', 'B', 4, u'Proporcional', False],
                ['vencida', 'B', 4, u'Vencida', False],
                ['pagamento_dobro', 'B', 4, u'Dobro', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                #['company_id.parent_id.name', u'Grupo', True],
                #['company_id.name', u'Unidade', False],
                ['employee_id.nome', u'Funcionário', False],
            ]
            rel.monta_grupos(rel.grupos)

            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            cr.execute("""  select cf.id
                            from hr_contract_ferias cf
                            join hr_employee e on e.id = cf.employee_id
                            join res_company c on c.id = cf.company_id
                            join res_partner rp on rp.id = c.partner_id
                            left join res_company cc on cc.id = c.parent_id
                            left join res_company ccc on ccc.id = cc.parent_id

                            where cf.data_inicial_periodo_concessivo between '""" + date_inicial + """' and '""" + date_final + """'
                            and
                            (
                            c.id = """ + str(rel_obj.company_id.id) + """
                            or c.parent_id = """ + str(rel_obj.company_id.id) + """
                            or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                            )

                            --order by cc.name, c.name, e.nome,
                            order by e.nome,
                            cf.data_inicial_periodo_aquisitivo, cf.data_final_periodo_aquisitivo;""")

            ferias_ids = []
            for ret in cr.fetchall():
                ferias_ids.append(ret[0])

            ferias_objs = self.pool.get('hr.contract_ferias').browse(cr, uid, ferias_ids)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(date_inicial) + u' a ' + formata_data(date_final)


            pdf = gera_relatorio(rel, ferias_objs)

            dados = {
                'nome': 'listagem_ferias.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_ferias_vencidas(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_final = str(data_final)[:10]

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Férias Vencidas e Proporcionais'
            rel.monta_contagem = False
            rel.colunas = [
                ['employee_id.nome'       , 'C', 60, u'Funcionário', False],
                ['contract_id.date_start' , 'D', 10, u'Admissão', False],
                ['data_inicial_periodo_aquisitivo', 'D', 10, u'Aquis. de' , False],
                ['data_final_periodo_aquisitivo'  , 'D', 10, u'Aquis. até', False],
                ['data_limite_aviso'  , 'D', 10, u'Aviso', False],
                ['proporcional', 'B', 4, u'Proporcional', False],
                ['vencida', 'B', 4, u'Vencida', False],
                ['avos'  , 'I', 5, u'Avos', False],
                ['meses_vencida', 'I', 4, u'Meses', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['contract_id.company_id.parent_id.name', u'Grupo', True],
                ['contract_id.company_id.name', u'Unidade', True],
                # ['employee_id.nome', u'Funcionário', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql = '''
            select
                cf.id

            from
                hr_contract_ferias cf
                join hr_employee e on e.id = cf.employee_id
                join hr_contract as co on co.id = cf.contract_id
                join res_company c on c.id = co.company_id
                left join res_company cc on cc.id = c.parent_id

            where
                (cf.vencida = True or cf.proporcional = True)
                and (cf.perdido_afastamento is null or cf.perdido_afastamento = False)
                and co.date_end is null
                and cf.data_limite_aviso <= '{data_final}'
                and co.categoria_trabalhador not in ('102','722','901','701','702','703')
                and
                    (
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                    )
            '''

            if not rel_obj.is_sintetico:
                sql += '''
            order by
                cc.name,
                c.name,
                e.nome,
                cf.data_inicial_periodo_aquisitivo,
                cf.data_final_periodo_aquisitivo;
                '''
            else:
                sql += '''
            order by
                cc.name,
                c.name,
                cf.data_limite_aviso,
                e.nome,
                cf.data_inicial_periodo_aquisitivo,
                cf.data_final_periodo_aquisitivo;
                '''

            sql = sql.format(data_final=rel_obj.data_final, company_id=rel_obj.company_id.id)
            print(sql)
            cr.execute(sql)

            ferias_ids = []
            dados =  cr.fetchall()

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for ferias_id, in dados:
                ferias_ids.append(ferias_id)

            ferias_objs = self.pool.get('hr.contract_ferias').browse(cr, uid, ferias_ids)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  Limite para aviso até ' + formata_data(date_final)


            pdf = gera_relatorio(rel, ferias_objs)

            dados = {
                'nome': 'listagem_ferias_vencidas.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_ferias_gozadas(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Férias Gozadas'
            rel.monta_contagem = False
            rel.colunas = [
                ['nome','C', 60, u'Funcionário', False],
                ['date_start', 'D', 10, u'Admissão', False],
                ['data_inicial_periodo_aquisitivo', 'D', 10, u'Aquis. de' , False],
                ['data_final_periodo_aquisitivo'  , 'D', 10, u'Aquis. até', False],
                ['data_inicial_periodo_gozo'      , 'D', 10, u'Gozo de' , False],
                ['data_final_periodo_gozo'        , 'D', 10, u'Gozo até', False],
                ['data_pagamento', 'D', 10, u'Dt.pag.', False],
                ['liquido', 'F', 15, u'Líquido', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql = """
                            select
                                rp.name as empresa,
                                e.nome,
                                co.date_start,
                                cf.data_inicial_periodo_aquisitivo,
                                cf.data_final_periodo_aquisitivo,
                                h.date_from,
                                h.date_to,
                                h.date_from -2 as data_pagamento,
                                coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'LIQ_FERIAS'), 0) as liquido


                            from hr_contract_ferias cf
                                join hr_employee e on e.id = cf.employee_id
                                join hr_contract co on co.id = cf.contract_id
                                join hr_payslip h on h.contract_id = cf.contract_id and h.data_inicio_periodo_aquisitivo = cf.data_inicial_periodo_aquisitivo
                                join res_company c on c.id = cf.company_id
                                join res_partner rp on rp.id = c.partner_id
                                left join res_company cc on cc.id = c.parent_id
                                left join res_company ccc on ccc.id = cc.parent_id

                            where
                                cf.vencida = False
                                and cf.proporcional = False
                                and cf.data_inicial_periodo_gozo between '""" + date_inicial + """' and '""" + date_final + """'
                            and h.tipo = 'F'
                            and h.simulacao = False
                            and
                            (
                            c.id = """ + str(rel_obj.company_id.id) + """
                            or c.parent_id = """ + str(rel_obj.company_id.id) + """
                            or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                            )

                            order by cc.name, c.name, e.nome,
                            cf.data_inicial_periodo_aquisitivo, cf.data_final_periodo_aquisitivo;"""

            print(sql)
            cr.execute(sql)

            dados =  cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, date_start,data_inicial_periodo_aquisitivo ,data_final_periodo_aquisitivo, data_inicial_periodo_gozo, data_final_periodo_gozo, data_pagamento, liquido in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['date_start'] = date_start
                linha['data_inicial_periodo_aquisitivo'] = data_inicial_periodo_aquisitivo
                linha['data_final_periodo_aquisitivo'] = data_final_periodo_aquisitivo
                linha['data_inicial_periodo_gozo'] = data_inicial_periodo_gozo
                linha['data_final_periodo_gozo'] = data_final_periodo_gozo
                linha['data_pagamento'] = data_pagamento
                linha['liquido'] = liquido
                linhas.append(linha)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(date_inicial) + u' a ' + formata_data(date_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'listagem_ferias_gozadas.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_afastamentos(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Listagem de Afastamentos'
            rel.colunas = [
                ['employee_id.nome'       , 'C', 60, u'Funcionário', False],
                ['rule_id.name' , 'C', 40, u'Motivo', False],
                ['data_inicial', 'D', 10, u'Afastamento' , False],
                ['data_final'  , 'D', 10, u'Retorno', False],
                ['valor_inss', 'F', 10, u'INSS' , True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                # ['company_id.parent_id.name', u'Empresa', True],
                ['company_id.name', u'Unidade', True],
                # ['employee_id.nome', u'Funcionário', False],
            ]
            rel.monta_grupos(rel.grupos)



            sql = """
                select a.id
                from hr_afastamento a
                join res_company c on c.id = a.company_id
                join hr_employee e on e.id = a.employee_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                where """

            if rel_obj.ano and rel_obj.mes:
                data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
                rel.band_page_header.elements[-1].text = u'Competência ' + MESES_DIC[rel_obj.mes] + '/' + str(rel_obj.ano)
                sql += """

                    (
                        not (a.data_inicial < '""" + data_inicial + """' and a.data_final <= '""" + data_inicial + """') and
                        not (a.data_inicial > '""" + data_final + """' and a.data_final >= '""" + data_final + """')
                    ) or
                        (a.data_inicial <= '""" + data_final + """' and a.data_final is null)
                    and (
                          c.id = """ + str(rel_obj.company_id.id) + """
                          or c.parent_id = """ + str(rel_obj.company_id.id) + """
                          or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                        )

                    """
            else:
                sql += """(
                          c.id = """ + str(rel_obj.company_id.id) + """
                          or c.parent_id = """ + str(rel_obj.company_id.id) + """
                          or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                          )"""

                rel.band_page_header.elements[-1].text = u'Empresa ' + rel_obj.company_id.partner_id.name

            sql += """ order by c.name, e.nome, a.data_inicial, a.data_final;"""

            cr.execute(sql)
            afastamento_ids = []
            for ret in cr.fetchall():
                afastamento_ids.append(ret[0])

            afastamento_objs = self.pool.get('hr.afastamento').browse(cr, uid, afastamento_ids)

            pdf = gera_relatorio(rel, afastamento_objs)

            dados = {
                'nome': 'listagem_afastamentos.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_funcionarios(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data = parse_datetime(rel_obj.data).date()
            date = str(data)[:10]
            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Listagem de Funcionários'
            rel.monta_contagem = True
            rel.colunas = [
                ['name' , 'C', 5, u'Matrícula', False],
                ['employee_id.codigo' , 'I', 5, u'Código', False],
                ['employee_id.nome'   , 'C', 60, u'Nome' , False],
                ['job_id.name', 'C', 30, u'Função', False],
                ['date_start', 'D', 10, u'Admissão' , False],
                ['date_end', 'D', 10, u'Demissão' , False],
                ['wage', 'F', 10, u'Salário base' , True],
                ['centrocusto_id.nome', 'C', 30, u'Centro de Custo' , False],
                ['employee_id.bank_id.bic', 'C', 3, u'Banco' , False],
                ['employee_id.banco_agencia', 'C', 10, u'Agência' , False],
                ['employee_id.banco_conta', 'C', 15, u'Conta Corrente' , False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['company_id.name', u'Unidade', True],
            ]
            rel.monta_grupos(rel.grupos)

            # rel.band_page_header.elements[-1].text = u'Competência ' + MESES_DIC[rel_obj.mes] + '/' + str(rel_obj.ano)

            cr.execute("""select a.id
                          from hr_contract a
                          join res_company c on c.id = a.company_id
                          join res_partner rp on rp.id = c.partner_id
                          left join res_company cc on cc.id = c.parent_id
                          left join res_company ccc on ccc.id = cc.parent_id
                          join hr_employee e on e.id = a.employee_id

                          where
                          a.date_end is null and a.date_start <= '""" + date + """' and a.date_end is null
                          and a.categoria_trabalhador not in ('102','722','901','701','702','703')
                          and (
                          c.id = """ + str(rel_obj.company_id.id) + """
                          or c.parent_id = """ + str(rel_obj.company_id.id) + """
                          or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                          )
                          order by c.name, e.nome;""")

            contrato_ids = []
            for ret in cr.fetchall():
                contrato_ids.append(ret[0])

            contrato_objs = self.pool.get('hr.contract').browse(cr, uid, contrato_ids)

            pdf = gera_relatorio(rel, contrato_objs)

            dados = {
                'nome': 'listagem_funcionarios.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_tomadores_cnpj(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            company_cnpj = rel_obj.company_id.partner_id.cnpj_cpf
            date_inicial = parse_datetime(rel_obj.data_inicial).date()
            date_final = parse_datetime(rel_obj.data_final).date()
            data_inicial = str(date_inicial)[:10]
            data_final = str(date_final)[:10]

            employee_id = rel_obj.employee_id.id

            SQL_RETENCAO = """
                select
                    rp.razao_social,
                    rp.cnpj_cpf

                from
                    sped_documento as sd
                    join res_company c on c.id = sd.company_id
                    join res_partner rp on rp.id = sd.partner_id

                where
                    sd.emissao = '0'
                    and sd.situacao in ('00','01')
                    and sd.previdencia_retido = true
                    and sd.state = 'autorizada'
                    and to_char(sd.data_emissao, 'YYYY-MM-DD') between '{data_inicial}' and '{data_final}'
                    and c.cnpj_cpf = '{cnpj}'

                group by
                    rp.razao_social,
                    rp.cnpj_cpf

                order by
                    rp.razao_social,
                    rp.cnpj_cpf
            """
            sql = SQL_RETENCAO.format(data_inicial=data_inicial, data_final=data_final, cnpj=company_cnpj, employee_id=employee_id)
            cr.execute(sql)
            dados = cr.fetchall()
            retencao_sem_funcionario = {}
            if len(dados):
                for razao_social, cnpj in dados:
                    retencao_sem_funcionario[cnpj] = razao_social

            SQL_TOMADOR = """
                                select
                                    p.cnpj_cpf, p.razao_social, c.name, e.nome, j.name, lotacao.data_alteracao, lotacao.data_limite
                                from
                                    (
                                        select
                                            ca.contract_id,
                                            ca.data_alteracao,
                                            ca.lotacao_id,
                                            (
                                                select
                                                    caa.data_alteracao
                                                from
                                                    hr_contract_alteracao caa
                                                where
                                                        caa.contract_id = ca.contract_id
                                                    and caa.tipo_alteracao = ca.tipo_alteracao
                                                    and caa.data_alteracao > ca.data_alteracao
                                                order by
                                                    caa.data_alteracao
                                                limit 1
                                            ) as data_limite
                                        from
                                            hr_contract_alteracao ca
                                        where
                                            ca.tipo_alteracao = 'L'

                                        union

                                        select
                                            c.id,
                                            c.date_start,
                                            case
                                                when c.lotacao_id is null then cc.partner_id
                                                else c.lotacao_id
                                            end as lotacao_id,
                                            (
                                                select
                                                    caa.data_alteracao
                                                from
                                                    hr_contract_alteracao caa
                                                where
                                                        caa.contract_id = c.id
                                                    and caa.tipo_alteracao = 'L'
                                                    and caa.data_alteracao > c.date_start
                                                order by
                                                    caa.data_alteracao
                                                limit 1
                                            ) as data_limite
                                        from
                                            hr_contract c
                                            join res_company cc on cc.id = c.company_id
                                    ) as lotacao
                                left join res_partner p on p.id = lotacao.lotacao_id
                                join hr_contract c on c.id = lotacao.contract_id
                                join hr_employee e on e.id = c.employee_id
                                join res_company cp on cp.id = c.company_id
                                join res_partner pp on pp.id = cp.partner_id
                                join hr_job j on j.id = c.job_id

                                where
                                        pp.cnpj_cpf = '{cnpj}'
                                    and c.categoria_trabalhador != '901'
                                    and lotacao.data_alteracao <= '{data_final}'
                                    and c.date_end is null
                                    and (
                                           lotacao.data_limite is null
                                        or lotacao.data_limite > '{data_inicial}'
                                    )
                                """

            if employee_id:
                SQL_TOMADOR += """
                                and
                                e.id = {employee_id}

                                order by p.razao_social, p.cnpj_cpf, e.nome, lotacao.data_alteracao, lotacao.data_limite;
                                """
            else:
                SQL_TOMADOR += """
                                order by p.razao_social, p.cnpj_cpf, e.nome, lotacao.data_alteracao, lotacao.data_limite;
                                """

            sql = SQL_TOMADOR.format(data_inicial=data_inicial, data_final=data_final, cnpj=company_cnpj, employee_id=employee_id)
            print(sql)

            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for cnpj_cpf, tomador, codigo, nome, cargo, date_start, date_end in dados:
                linha = DicionarioBrasil()

                #
                # Remove o cnpj do controle de retenção sem alocação, pois já
                # tem gente alocada
                #
                retencao_sem_funcionario.pop(cnpj_cpf, '')

                linha['cnpj_cpf'] = cnpj_cpf or ''
                linha['tomador'] = tomador or ''

                if cnpj_cpf:
                    linha['tomador'] += u' - '
                    linha['tomador'] += cnpj_cpf or ''

                linha['codigo'] = codigo
                linha['nome'] = nome
                linha['cargo'] = cargo
                linha['date_start'] = date_start
                linha['date_end'] = date_end
                linhas.append(linha)

            #
            # Adiciona as retenções que não tem ninguém alocado
            #
            for cnpj in retencao_sem_funcionario:
                linha = DicionarioBrasil()

                print(cnpj, retencao_sem_funcionario[cnpj])

                linha['cnpj_cpf'] = cnpj
                linha['tomador'] = retencao_sem_funcionario[cnpj]

                if cnpj:
                    linha['tomador'] += u' - ' + cnpj

                linha['codigo'] = ''
                linha['nome'] = u'SEM FUNCIONÁRIOS ALOCADOS'
                linha['cargo'] = ''
                linha['date_start'] = None
                linha['date_end'] = None
                linhas.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Tomadores'
            rel.colunas = [
                ['codigo' , 'C', 5, u'Código', False],
                ['nome'   , 'C', 30, u'Nome' , False],
                ['cargo', 'C', 30, u'Função', False],
                ['date_start', 'D', 10, u'Data Início' , False],
                ['date_end', 'D', 10, u'Data Saída' , False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)


            rel.grupos = [
                ['tomador', u'Tomador', False],
            ]

            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = company_obj.name + ' - ' + formata_data(data_inicial) + u' a ' + formata_data(data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'listagem_tomadores.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)
        return True

    def gera_listagem_dependentes(self, cr, uid, ids, contex={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Dependentes'
            rel.colunas = [
                ['employee_id.nome'   , 'C', 60, u'Nome Funcionário' , False],
                ['nome' , 'C', 60, u'Dependente', False],
                ['sexo' , 'C', 5, u'Sexo', False],
                ['data_nascimento' , 'D', 10, u'Data Nasc.', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['employee_id.company_id.name', u'Unidade', True],
                # ['employee_id.name', u'Funcionário', False],
            ]

            rel.monta_grupos(rel.grupos)

            # rel.band_page_header.elements[-1].text = u'Competência ' + MESES_DIC[rel_obj.mes] + '/' + str(rel_obj.ano)

            cr.execute("""select ep.id
                          from hr_employee_dependente as ep
                          inner join hr_employee as e on e.id = ep.employee_id
                          join res_company as c on c.id = e.company_id
                          join res_partner p on p.id = c.partner_id
                          left join res_company cc on cc.id = c.parent_id
                          join hr_contract as co on e.id = co.employee_id

                          where co.date_end is null and
                          (
                               c.id = """ + str(rel_obj.company_id.id) + """
                               or c.parent_id = """ + str(rel_obj.company_id.id) + """
                               or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                          )
                          order by c.name,e.nome,ep.nome  ;""")


            contrato_ids = []
            for ret in cr.fetchall():
                contrato_ids.append(ret[0])

            contrato_objs = self.pool.get('hr.employee_dependente').browse(cr, uid, contrato_ids)

            pdf = gera_relatorio(rel, contrato_objs)

            dados = {
                'nome': 'listagem_dependentes.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_tomadores_unidade(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            company_id = rel_obj.company_id.id
            date_inicial = parse_datetime(rel_obj.data_inicial).date()
            date_final = parse_datetime(rel_obj.data_final).date()
            data_inicial = str(date_inicial)[:10]
            data_final = str(date_final)[:10]

            employee_id = rel_obj.employee_id.id

            SQL_TOMADOR = """
                                select
                                   pp.name, p.cnpj_cpf, p.razao_social, c.name, e.nome, j.name, lotacao.data_alteracao, lotacao.data_limite
                                from
                                    (
                                        select
                                            ca.contract_id,
                                            ca.data_alteracao,
                                            ca.lotacao_id,
                                            (
                                                select
                                                    caa.data_alteracao
                                                from
                                                    hr_contract_alteracao caa
                                                where
                                                        caa.contract_id = ca.contract_id
                                                    and caa.tipo_alteracao = ca.tipo_alteracao
                                                    and caa.data_alteracao > ca.data_alteracao
                                                order by
                                                    caa.data_alteracao
                                                limit 1
                                            ) as data_limite
                                        from
                                            hr_contract_alteracao ca
                                        where
                                            ca.tipo_alteracao = 'L'

                                        union

                                        select
                                            c.id,
                                            c.date_start,
                                            case
                                                when c.lotacao_id is null then cc.partner_id
                                                else c.lotacao_id
                                            end as lotacao_id,
                                            (
                                                select
                                                    caa.data_alteracao
                                                from
                                                    hr_contract_alteracao caa
                                                where
                                                        caa.contract_id = c.id
                                                    and caa.tipo_alteracao = 'L'
                                                    and caa.data_alteracao > c.date_start
                                                order by
                                                    caa.data_alteracao
                                                limit 1
                                            ) as data_limite
                                        from
                                            hr_contract c
                                            join res_company cc on cc.id = c.company_id
                                    ) as lotacao
                                left join res_partner p on p.id = lotacao.lotacao_id
                                join hr_contract c on c.id = lotacao.contract_id
                                join hr_employee e on e.id = c.employee_id
                                join hr_job j on j.id = c.job_id
                                join res_company cp on cp.id = c.company_id
                                join res_partner pp on pp.id = cp.partner_id
                                left join res_company cc on cc.id = cp.parent_id
                                left join res_company ccc on ccc.id = cc.parent_id

                                where
                                    (
                                      cp.id = '{company_id}'
                                      or cp.parent_id = '{company_id}'
                                      or cc.parent_id = '{company_id}'
                                    )
                                    and c.categoria_trabalhador != '901'
                                    and lotacao.data_alteracao <= '{data_final}'
                                    and c.date_end is null
                                    and (
                                           lotacao.data_limite is null
                                        or lotacao.data_limite > '{data_inicial}'
                                    )
                                """

            if employee_id:
                SQL_TOMADOR += """
                                and
                                e.id = {employee_id}

                                order by p.name, p.cnpj_cpf, e.nome, lotacao.data_alteracao, lotacao.data_limite;
                                """
            else:
                SQL_TOMADOR += """
                                order by p.name, p.cnpj_cpf, e.nome, lotacao.data_alteracao, lotacao.data_limite;
                                """

            sql = SQL_TOMADOR.format(data_inicial=data_inicial, data_final=data_final, company_id=company_id, employee_id=employee_id)
            print(sql)

            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, cnpj_cpf, tomador, codigo, nome, cargo, date_start, date_end in dados:
                linha = DicionarioBrasil()

                linha['empresa'] = empresa
                linha['cnpj_cpf'] = cnpj_cpf
                linha['tomador'] = tomador

                if cnpj_cpf:
                    linha['tomador'] += u' - ' + cnpj_cpf

                linha['codigo'] = codigo
                linha['nome'] = nome
                linha['cargo'] = cargo
                linha['date_start'] = date_start
                linha['date_end'] = date_end
                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Tomadores'
            rel.colunas = [
                ['codigo' , 'C', 5, u'Código', False],
                ['nome'   , 'C', 30, u'Nome' , False],
                ['cargo', 'C', 30, u'Função', False],
                ['date_start', 'D', 10, u'Data Início' , False],
                ['date_end', 'D', 10, u'Data Saída' , False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)


            rel.grupos = [
                ['empresa', u'Empresa', False],
                ['tomador', u'Tomador', False],
            ]

            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = company_obj.name + ' - ' + formata_data(data_inicial) + u' a ' + formata_data(data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'listagem_tomadores.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)
        return True


    def gera_listagem_mensalidade_sindical(self, cr, uid, ids, contex={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Mensalidade Sindical'
            rel.colunas = [
                ['nome' , 'C', 60, u'Funcionário', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['company_id.name', u'Unidade', True],
                # ['employee_id.name', u'Funcionário', False],
            ]

            rel.monta_grupos(rel.grupos)

            # rel.band_page_header.elements[-1].text = u'Competência ' + MESES_DIC[rel_obj.mes] + '/' + str(rel_obj.ano)

            cr.execute('''select e.id from hr_employee as e
            inner join res_company as c on c.id = e.company_id
            join hr_contract as co on e.id = co.employee_id
            join hr_contract_regra as cr on co.id = cr.contract_id
            join  hr_salary_rule as sr on sr.id = cr.rule_id
            where co.date_end is null and sr.code = 'M_SINDICAL' order by c.name,e.nome ;''')

            contrato_ids = []
            for ret in cr.fetchall():
                contrato_ids.append(ret[0])

            contrato_objs = self.pool.get('hr.employee').browse(cr, uid, contrato_ids)

            pdf = gera_relatorio(rel, contrato_objs)

            dados = {
                'nome': 'listagem_mensalidade_sindical.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_variaveis(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Rubricas Variáveis'
            rel.colunas = [
                ['employee_id.codigo' , 'I', 5, u'Código', False],
                ['employee_id.nome'   , 'C', 60, u'Nome' , False],
                ['contract_id.job_id.name', 'C', 30, u'Função', False],
                ['amount', 'F', 10, u'Valor' , True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['rule_id.descricao', u'Rubrica', False],
            ]
            rel.monta_grupos(rel.grupos)

            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            rel.band_page_header.elements[-1].text = u'Competência ' + MESES_DIC[rel_obj.mes] + '/' + str(rel_obj.ano)

            filtro = {
                'data_inicial': data_inicial,
                'data_final': data_final,
                'filtro_adicional': '',
            }

            sql = """
                select
                    a.id
                from
                    hr_payslip_input a
                    join res_company c on c.id = a.company_id
                    join hr_employee e on e.id = a.employee_id
                    join hr_contract t on t.id = a.contract_id
                    join hr_job j on j.id = t.job_id
                    join hr_salary_rule r on r.id = a.rule_id
                where
                    (
                        not (a.data_inicial < '{data_inicial}' and a.data_final <= '{data_inicial}') and
                        not (a.data_inicial > '{data_final}' and a.data_final >= '{data_final}')
                    )
                    {filtro_adicional}
                order by
                    r.code,
                    r.name,
                    e.nome;
            """

            if rel_obj.company_id:
                filtro['filtro_adicional'] += ' and (c.id = {company_id} or c.parent_id = {company_id})'.format(company_id=rel_obj.company_id.id)

            if rel_obj.rule_id:
                filtro['filtro_adicional'] += ' and r.id = {rubrica_id}'.format(rubrica_id=rel_obj.rule_id.id)

            sql = sql.format(**filtro)

            cr.execute(sql)
            dados = cr.fetchall()

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            variavel_ids = []
            for var_id, in dados:
                variavel_ids.append(var_id)

            variavel_objs = self.pool.get('hr.payslip.input').browse(cr, uid, variavel_ids)

            pdf = gera_relatorio(rel, variavel_objs)

            dados = {
                'nome': 'listagem_rubricas_variaveis.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_analitico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            competencia = parse_datetime(data_inicial).strftime(b'%B-%Y').decode('utf-8')
            if rel_obj.tipo == 'T' or rel_obj.tipo == 'F':
                tipos = ('N', 'R')
            elif rel_obj.tipo == 'N':
                tipos = "('N')"
            elif rel_obj.tipo == 'D':
                tipos = "('D')"
            else:
                tipos = "('R')"

            #cr.execute("""
            #    select distinct
            #        p.cnpj_cpf
            #    from
            #        res_company c
            #        join res_partner p on p.id = c.partner_id
            #        left join res_company cc on cc.id = c.parent_id

            #    where
            #        p.cnpj_cpf is not null
            #        and p.cnpj_cpf != ''
            #        and (
            #        c.id = """ + str(rel_obj.company_id.id) + """
            #        or c.parent_id = """ + str(rel_obj.company_id.id) + """
            #        or cc.parent_id = """ + str(rel_obj.company_id.id) + """
            #        )
            #    order by
            #        p.cnpj_cpf;
            #""")
            #todos_cnpjs = cr.fetchall()

            #cnpjs = []
            #for cnpj, in todos_cnpjs:
            #    cnpjs.append(cnpj)



            #
            # Adiantamento
            #
            #if rel_obj.tipo == 'D':
            #    if rel_obj.mes == '11':
            #        rel = Report(u'Analítico do Adiantamento do Décimo Terceiro', cr, uid)
            #        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analitico_adiantamento_13.jrxml')
            #        nome_arq = u'analitico_adiantamento_13o_' + competencia + u'.pdf'

            #    else:
            #        rel = Report(u'Analítico do Décimo Terceiro', cr, uid)
            #        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analitico_folha.jrxml')
            #        nome_arq = u'analitico_13o_' + competencia + u'.pdf'
            #else:
            rel = Report(u'Analítico da Folha de Pagamento', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_folha.jrxml')
            nome_arq = u'analitico_folha_' + competencia + u'.pdf'

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['COMPETENCIA'] = competencia
            rel.parametros['TIPOS'] = str(tipos)
            #rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')
            rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
            rel.parametros['COMPLEMENTAR'] = rel_obj.complementar
            rel.parametros['FERIAS'] = rel_obj.tipo == 'F'

            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_seguros(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data = parse_datetime(rel_obj.data).date()
            data_inicial = primeiro_dia_mes(rel_obj.data)
            data_final = ultimo_dia_mes(rel_obj.data)
            date = str(data)[:10]
            cr.execute("""select a.id, e.nome, e.sexo,
                          j.name as cargo,
                          cast(a.wage as numeric(18,2)) as salario,
                          e.data_nascimento as nascimento, e.cpf as cpf

                          from hr_contract a
                          join res_company c on c.id = a.company_id
                          join res_partner rp on rp.id = c.partner_id
                          left join res_company cc on cc.id = c.parent_id
                          left join res_company ccc on ccc.id = cc.parent_id
                          join hr_employee e on e.id = a.employee_id
                          join hr_job j on j.id = a.job_id

                          where
                          (a.date_end is null
                          or
                           a.date_end between '""" + str(data_inicial) + """' and '""" + str(data_final) + """'
                          )
                          and a.date_start <= '""" + date + """'
                          and (
                          c.id = """ + str(rel_obj.company_id.id) + """
                          or c.parent_id = """ + str(rel_obj.company_id.id) + """
                          or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                          )
                          order by
                          c.name, e.nome;""")

            dados = cr.fetchall()
            #print(dados)
            linhas = []
            quantidade = 1
            for id,nome,sexo,cargo,salario,nascimento,cpf in dados:
                linha = DicionarioBrasil()
                linha['id'] = id
                linha['nome'] = nome
                linha['sexo'] = sexo
                linha['cargo'] = cargo
                linha['salario'] = salario
                linha['nascimento'] = nascimento
                linha['cpf'] = cpf
                linha['quantidade'] = quantidade
                linhas.append(linha)
                quantidade += 1

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Seguro de Vida'
            rel.colunas = [
                ['id' , 'I', 5, u'Código', False],
                ['nome' , 'C', 40, u'Matrícula', False],
                ['sexo' , 'C', 5, u'Sexo', False],
                ['cargo' , 'C', 20, u'Cargo', False],
                ['salario' , 'F', 10, u'Salario Base', False],
                ['nascimento' , 'D', 10, u'Nascimento', False],
                ['cpf' , 'C', 16, u'Cpf', False],
                ['quantidade' , 'I', 10, u'Quantidade', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'relacao_seguro.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'relacao_seguro.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True


    def gera_carteira_vigilante(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]
            if rel_obj.todos:
                periodo = ''
                cr.execute("""select e.id,
                                     e.nome,
                                     j.name as cargo,
                                     e.roc_data_expedicao as data_expedicao,
                                     e.roc_data_validade as data_validade,
                                     e.roc_numero as roc_numero,
                                     e.roc_orgao_emissor as roc_orgao
                              from hr_employee e
                              join hr_contract co on co.employee_id = e.id
                              join hr_job j on j.id = co.job_id
                              join res_company c on c.id = co.company_id
                              join res_partner rp on rp.id = c.partner_id
                              left join res_company cc on cc.id = c.parent_id
                              left join res_company ccc on ccc.id = cc.parent_id

                              where
                              co.date_end is null and e.roc_numero is not null
                              and (
                              c.id = """ + str(rel_obj.company_id.id) + """
                              or c.parent_id = """ + str(rel_obj.company_id.id) + """
                              or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                              )
                              order by
                              c.name, e.nome;""")
            else:
                periodo = u' -  PERIODO ' + formata_data(date_inicial) + u' a ' + formata_data(date_final)
                cr.execute("""select e.id,
                                     e.nome,
                                     j.name as cargo,
                                     e.roc_data_expedicao as data_expedicao,
                                     e.roc_data_validade as data_validade,
                                     e.roc_numero as roc_numero,
                                     e.roc_orgao_emissor as roc_orgao
                              from hr_employee e
                              join hr_contract co on co.employee_id = e.id
                              join hr_job j on j.id = co.job_id
                              join res_company c on c.id = co.company_id
                              join res_partner rp on rp.id = c.partner_id
                              left join res_company cc on cc.id = c.parent_id
                              left join res_company ccc on ccc.id = cc.parent_id

                              where
                              co.date_end is null and e.roc_data_validade between '""" + date_inicial + """' and '""" + date_final + """'
                              and e.roc_numero is not null
                              and
                              (
                              c.id = """ + str(rel_obj.company_id.id) + """
                              or c.parent_id = """ + str(rel_obj.company_id.id) + """
                              or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                              )
                              order by
                              c.name, e.nome;""")

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for id,nome,cargo,data_expedicao,data_validade,roc_numero,roc_orgao in dados:
                linha = DicionarioBrasil()
                linha['id'] = id
                linha['nome'] = nome
                linha['cargo'] = cargo
                linha['data_expedicao'] = data_expedicao
                linha['data_validade'] = data_validade
                linha['roc_numero'] = roc_numero
                linha['roc_orgao'] = roc_orgao
                linhas.append(linha)


            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Carteirinha de Vigilante'
            rel.colunas = [
                ['id' , 'I', 5, u'Código', False],
                ['nome' , 'C', 40, u'Funcionário', False],
                ['cargo' , 'C', 20, u'Cargo', False],
                ['data_expedicao' , 'D', 10, u'Data Expedição', False],
                ['data_validade' , 'D', 10, u'Data de Validade', False],
                ['roc_numero' , 'C', 20, u'Registro DRT', False],
                ['roc_orgao' , 'C', 30, u'Orgão Expedidor', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + periodo

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'relacao_carteira_vigilante.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_pagamento_salario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]

            dados_filtro = {
                'data_inicial': str(data_inicial),
                'data_final': str(data_final),
                'company_id': company_id,
                'tipo': 'N',
            }

            if rel_obj.tipo == 'T':
                dados_filtro['tipo'] = '%'

            elif rel_obj.tipo == 'D':
                dados_filtro['tipo'] = 'D'

            elif rel_obj.tipo == 'F':
                dados_filtro['tipo'] = 'F'

            sql = """
                select
                    coalesce(b.name, '') as banco,
                    e.nome as nome,
                    j.name as cargo,
                    c.name as name,
                    coalesce(cast(l.valor_liquido as numeric(18,2)), 0) as liquido,
                    coalesce(e.banco_agencia, '') as banco_agencia,
                    coalesce(e.banco_conta,'') as banco_conta

                from
                         hr_payslip as l
                    join hr_employee e on e.id = l.employee_id
                    join hr_contract co on co.id = l.contract_id
                    left join hr_job j on j.id = co.job_id
                    left join res_bank b on b.id = e.bank_id
                    join res_company c on c.id = co.company_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                where
                    l.tipo like '{tipo}'
                    and coalesce(l.simulacao, False) = False
                    -- and l.state = 'done'
                    and
                    (
                        (l.tipo in ('N', 'D') and l.date_from >= '{data_inicial}' and l.date_to <= '{data_final}')
                        or (l.tipo = 'R' and l.data_afastamento between '{data_inicial}' and '{data_final}')
                        or (l.tipo = 'F' and l.date_from >= cast('{data_inicial}' as date) - interval '2 days' and l.date_from <= cast('{data_final}' as date) - interval '2 days')
                    )
                    and (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                    )

                order by
                    c.name, e.nome;
                """
            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for banco, empregado, cargo, empresa, liquido, banco_agencia, banco_conta in dados:
                linha = DicionarioBrasil()
                linha['banco'] = banco
                linha['empregado'] = empregado
                linha['empresa'] = empresa
                linha['cargo'] = cargo
                linha['liquido'] = liquido
                linha['banco_agencia'] = banco_agencia
                linha['banco_conta'] = banco_conta
                linhas.append(linha)


            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Pagamento de Salário'

            if rel_obj.tipo == 'D':
                rel.title = u'Relação para Pagamento de 13º'

            if rel_obj.tipo == 'F':
                rel.title = u'Relação para Pagamento de Férias'

            rel.colunas = [
                ['empresa' , 'C', 50, u'Unidade', False],
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['cargo' , 'C', 20, u'Cargo', False],
                ['liquido' , 'F', 10, u'Salário', True],
                ['banco_agencia' , 'C', 10, u'Agência', False],
                ['banco_conta' , 'C', 10, u'Conta Corrente', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Unidade', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(date_inicial) + u' a ' + formata_data(date_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relacao_pagamento_salario_.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def relatorio_resumo_cbo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            sql = """
                select
                    co.name as empresa,
                    cbo.codigo as cbo,
                    cbo.ocupacao,
                    c.name as codigo,
                    c.date_start as data_admissao,
                    e.nome as empregado,
                    j.name as cargo,
                    case
                    when c.unidade_salario = '1' then coalesce((select cast(hl.quantity as numeric(18, 2)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'SALARIO_BASE'), 0.00)
                    else c.horas_mensalista
                    end as carga_horaria

                from
                        hr_payslip h
                    join hr_contract c on c.id = h.contract_id
                    join hr_employee e on e.id = h.employee_id
                    join hr_job j on j.id = c.job_id
                    join hr_cbo cbo on cbo.id = j.cbo_id
                    join res_company co on co.id = h.company_id
                    left join res_company cc on cc.id = co.parent_id
                    left join hr_payslip_afastamento hf on hf.payslip_id = h.id

                where
                        h.tipo = 'N'
                    and c.date_end is null
                    and c.categoria_trabalhador not in ('102','722','901','701','702','703')
                    and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                    -- and h.holerite_anterior_id is null
                    and hf.id is null
                    and (
                        co.id = {company_id}
                        or co.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )

                order by
                    cbo.codigo,
                    j.name,
                    e.nome;
                """

            sql = sql.format(company_id=rel_obj.company_id.id, data_inicial=rel_obj.data_inicial, data_final=rel_obj.data_final)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, cbo, ocupacao, codigo, data_admissao, empregado, cargo, carga_horaria in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['cbo'] = cbo
                #linha['ocupacao'] = ocupacao
                linha['codigo'] = codigo
                linha['data_admissao'] = data_admissao
                linha['empregado'] = empregado
                linha['cargo'] = cargo
                linha['carga_horaria'] = D(carga_horaria)
                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Resumo CBO-Função'
            rel.monta_contagem = True
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['data_admissao' , 'D', 10, u'Dt.Admissão', False],
                ['cargo' , 'C', 20, u'Função', False],
                ['carga_horaria' , 'F', 13, u'Carga horária', False],
                ['empresa', 'C', 50, u'Unidade', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['cbo', u'CBO', False],
                ['cargo', u'Função', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel_csv = RHRelatorioAutomaticoRetrato()
            rel_csv.title = u'Resumo CBO-Função'
            rel_csv.monta_contagem = True
            rel_csv.colunas = [
                ['empresa', 'C', 30, u'Empresa', False],
                ['cbo', 'C', 15, u'CBO', False],
                ['codigo' , 'C', 10, u'Código', False],
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['cargo' , 'C', 20, u'Função', False],
                ['cargo' , 'C', 20, u'Função', False],
                ['carga_horaria' , 'F', 13, u'Carga horária', False],
            ]
            rel_csv.monta_detalhe_automatico(rel_csv.colunas)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel_csv, linhas)

            dados = {
                'nome': u'resumo_cbo.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'resumo_cbo.csv',
                'arquivo_csv': base64.encodestring(csv)
            }

            rel_obj.write(dados)

        return True

    def gera_irrf_empregado(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = rel_obj.data_inicial
            data_final = rel_obj.data_final

            if rel_obj.tipo_pagamento == 'T':
                tipo_pagamento =  "('N','R','F','D')"
            elif rel_obj.tipo_pagamento == 'N':
                tipo_pagamento =  "('N')"
            elif rel_obj.tipo_pagamento == 'R':
                tipo_pagamento =  "('R')"
            elif rel_obj.tipo_pagamento == 'F':
                tipo_pagamento =  "('F')"
            else:
                tipo_pagamento =  "('D')"

            sql = """
select
co.name as empresa,
e.nome as empregado,
j.name as cargo,
h.valor_irpf,
h.base_irpf,
h.deducao_dependente as dependentes,
to_char(h.date_from, 'MM/YYYY') as data_periodo,
CASE
  WHEN h.tipo = 'R' THEN 'Rescisão'
  WHEN h.tipo = 'N' THEN 'Normal'
  WHEN h.tipo = 'F' THEN 'Férias'
  WHEN h.tipo = 'D' THEN 'Décimo Tercerio'
END as tipo,
h.data_pagamento_irpf,
h.data_vencimento_irpf as data_irpf,
case
  when h.state = 'done' then 'Fechado'
  else 'Rascunho'
end as state

from hr_payslip h
join hr_contract c on c.id = h.contract_id
join hr_employee e on e.id = h.employee_id
left join hr_job j on j.id = c.job_id
join res_company co on co.id = c.company_id
left join res_company cc on cc.id = co.parent_id

where
h.tipo in {tipo}
and h.valor_irpf > 0
and (h.simulacao = False or h.simulacao is null)
and h.data_pagamento_irpf between '{data_inicial}' and '{data_final}'
and (
  co.id = {company_id}
  or co.parent_id = {company_id}
  or cc.parent_id = {company_id}
)

order by
co.name,
e.nome;"""

            sql = sql.format(tipo=tipo_pagamento, company_id=rel_obj.company_id.id, data_inicial=rel_obj.data_inicial, data_final=rel_obj.data_final)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, empregado, cargo, valor_irrf, base_irpf, depedentes, data_periodo, tipo,data_pagamento_irrf, data_irpf, state in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['empregado'] = empregado
                linha['cargo'] = cargo
                linha['valor_irrf'] = valor_irrf
                linha['base_irpf'] = base_irpf
                linha['depedentes'] = depedentes
                linha['data_pagamento_irrf'] = data_pagamento_irrf
                linha['data_irpf'] = data_irpf
                linha['competencia'] = data_periodo
                linha['tipo'] = tipo
                linha['state'] = state
                linhas.append(linha)


            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para IRRF de Empregados'
            rel.colunas = [
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['cargo' , 'C', 20, u'Cargo', False],
                ['valor_irrf' , 'F', 10, u'Valor IRRF', True],
                ['base_irpf' , 'F', 10, u'Base IRRF', True],
                ['depedentes' , 'F', 10, u'Dedução', True],
                ['data_pagamento_irrf' , 'D', 13, u'Data Pagamento', False],
                ['data_irpf' , 'D', 10, u'Vencimento', False],
                ['competencia' , 'V', 12, u'Compentência', False],
                ['tipo' , 'C', 10, u'Origem', False],
                ['state' , 'C', 10, u'Situação', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  PERIODO ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relacao_irrf_empregados_.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_funcionarios_ativos_demitidos(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Funcionários', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_funcionarios_ativos_demitidos.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['UID'] = uid
        if rel_obj.tipo_funcionario == '1':
            rel.parametros['NOME'] = '1'
            relatorio = u'funcionarios_ativos_'
        else:
            rel.parametros['TIPO'] = 'hr_funcionarios_demitidos_lancamentos.jasper'
            rel.parametros['NOME'] = '2'
            relatorio = u'funcionarios_demitidos_'
        rel.outputFormat = rel_obj.formato


        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_dif_decimo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            ano = rel_obj.ano or 2014

            dados_filtro = {
                'company_id': company_id,
                'ano': ano,
            }

            sql = """
select
  c.name as empresa,
  e.nome as funcionario,
  coalesce((select hi.total from hr_payslip_line hi where hi.slip_id = h.id and hi.code = 'BRUTO'), 0.00) as decimo_final,
  coalesce((select hi.total from hr_payslip_line hi where hi.slip_id = h.id and hi.code = 'DECIMO_TERCEIRO_PAGO'), 0.00) as decimo_pago,
  coalesce((select hi.total from hr_payslip_line hi where hi.slip_id = h.id and hi.code = 'DIF_13'), 0.00) as diferenca

from
  hr_payslip h
  join hr_employee e on e.id = h.employee_id
  join hr_contract t on t.id = h.contract_id
  join res_company c on c.id = h.company_id
  left join res_company cc on cc.id = c.parent_id
  left join res_company ccc on ccc.id = cc.parent_id

where
  h.mes = '12'
  and h.ano = {ano}
  and h.tipo = 'D'
  and h.simulacao = True
  and t.categoria_trabalhador not in ('722','701','702','703')
  and (
    c.id = {company_id}
    or c.parent_id = {company_id}
    or cc.parent_id = {company_id}
  )

order by
  c.name,
  e.nome;
                """
            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, empregado, decimo_final, decimo_pago, diferenca in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['empregado'] = empregado
                linha['decimo_final'] = D(decimo_final)
                linha['decimo_pago'] = D(decimo_pago)
                linha['diferenca'] = D(diferenca)
                linhas.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relação para Conferência de Dif. de 13º'

            rel.colunas = [
                #['empresa' , 'C', 50, u'Unidade', False],
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['decimo_final' , 'F', 10, u'13º final', True],
                ['decimo_pago' , 'F', 10, u'13º pago', True],
                ['diferenca' , 'F', 10, u'Diferença', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Unidade', True],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name + u' -  ANO ' + str(ano).zfill(4)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'conferencia_dif_decimo.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_comprovante_redimentos_irpf(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.contract_id.id
        ano = str(rel_obj.ano)
        data_inicial = ano + '-01-01'
        data_final = ano + '-12-31'

        rel = Report('Relatório de Funcionários', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'comprovante_redimentos_irpf.jrxml')
        rel.parametros['REGISTRO_ID'] = contract_id
        rel.parametros['DATA_INICIAL'] = data_inicial
        rel.parametros['DATA_FINAL'] = data_final
        nome = limpa_caged(rel_obj.contract_id.employee_id.name)
        relatorio = u'CR_' + nome
        rel.outputFormat = rel_obj.formato


        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_pedido_demissao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.contract_id.id

        rel = Report(u'Pedido de Demissão', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_pedido_demissao.jrxml')
        rel.parametros['CONTRACT_ID'] = contract_id
        nome = limpa_caged(rel_obj.contract_id.employee_id.name)
        relatorio = u'demissao_' + nome
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_aviso_previo_indenizado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.contract_id.id

        rel = Report(u'Aviso Prévio Indenizado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_aviso_previo_indenizado.jrxml')
        rel.parametros['CONTRACT_ID'] = contract_id
        rel.parametros['DATA_AFASTAMENTO'] = rel_obj.data_inicial
        nome = limpa_caged(rel_obj.contract_id.employee_id.name)
        relatorio = u'aviso_previo_' + nome
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_aviso_previo_trabalhado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.contract_id.id

        rel = Report(u'Aviso Prévio Trabalhado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_aviso_previo_trabalhado.jrxml')
        rel.parametros['CONTRACT_ID'] = contract_id

        data_inicial, data_final, dias_aviso, data_afastamento = rel_obj.contract_id.calcula_data_aviso_previo(rel_obj.data_inicial, True)

        rel.parametros['DATA_AVISO'] = rel_obj.data_inicial
        rel.parametros['DATA_AFASTAMENTO'] = str(data_afastamento)[:10]
        nome = limpa_caged(rel_obj.contract_id.employee_id.name)
        relatorio = u'aviso_previo_' + nome
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + '_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_dados_colaboradores(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()


        rel = Report(u'Aviso Prévio Trabalhado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_dados_colaboradores.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = 'xls'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Dados_Colaboradores_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.xls',
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

    def gera_relatorio_funcionarios_admitidos(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Funcionários', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_funcionarios_admitidos.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato

        relatorio = u'funcionarios_admitidos_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

    def gera_ficha_financeira(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        ano = str(rel_obj.ano) + '%'
        contract_id = rel_obj.contract_id.id

        rel = Report('Ficha Financeira por Funcionário', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_ficha_financeira_rh.jrxml')
        rel.parametros['CONTRACT_ID'] = int(contract_id)
        rel.parametros['ANO'] = ano
        rel.outputFormat = rel_obj.formato

        relatorio = u'ficha_financeria_de_' + rel_obj.contract_id.employee_id.nome

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

    def gera_relatorio_sindical(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            if not rel_obj.inclui_valores:
                sql = """
                    select distinct
                        rp.name,
                        rps.name,
                        co.date_start,
                        e.nome,
                        e.cpf,
                        e.rg_numero,
                        e.carteira_trabalho_numero ||'-' || e.carteira_trabalho_serie || '/' || e.carteira_trabalho_estado as ctps,
                        e.nis,
                        'N' as tipo,
                        '' as rubrica,
                        0 as valor,
                        f.name as cargo,
                        co.wage as salario

                    from
                        hr_contract co
                        join hr_employee e on e.id = co.employee_id
                        join res_company c on c.id = co.company_id
                        join res_partner rp on rp.id = c.partner_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                        join hr_job f on f.id = co.job_id

                        join res_partner rps on rps.id = co.sindicato_id

                    where
                        (co.date_end is null or co.date_end > '{data_final}')
                        and co.date_start <= '{data_final}'
                        and (
                            c.id = {company_id}
                            or c.parent_id = {company_id}
                            or cc.parent_id = {company_id}
                        )

                    order by
                    rps.name,
                    e.nome

                """
            else:
                sql = """
                    select distinct
                        rp.name,
                        rps.name,
                        co.date_start,
                        e.nome,
                        e.cpf,
                        e.rg_numero,
                        e.carteira_trabalho_numero ||'-' || e.carteira_trabalho_serie || '/' || e.carteira_trabalho_estado as ctps,
                        e.nis,
                        h.tipo,
                        r.name as rubrica,
                        hl.total,
                        f.name as cargo,
                        co.wage as salario

                    from
                        hr_contract co
                        join hr_employee e on e.id = co.employee_id
                        join res_company c on c.id = co.company_id
                        join res_partner rp on rp.id = c.partner_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                        join hr_job f on f.id = co.job_id

                        join res_partner rps on rps.id = co.sindicato_id
                        join hr_payslip as h on h.contract_id = co.id
                        join hr_payslip_line as hl on hl.slip_id = h.id
                        join hr_salary_rule r on r.id = hl.salary_rule_id

                    where
                        hl.code in ('R_297', 'R_6', 'C_SINDICAL', 'DESC_CONVENIO', 'DEV_CONT', 'M_SINDICAL', 'TAXA_ASSISTENCIAL')
                        and h.date_from >=  '{data_inicial}' and h.date_to <= '{data_final}'
                        and h.simulacao = False
                        and (
                            c.id = {company_id}
                            or c.parent_id = {company_id}
                            or cc.parent_id = {company_id}
                        )

                    order by
                    rps.name,
                    r.name,
                    e.nome
                """

            sql = sql.format(company_id=rel_obj.company_id.id, data_inicial=rel_obj.data_inicial, data_final=rel_obj.data_final)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            for empresa, sindicato, data_inicial, nome, cpf, rg_numero, ctps, nis, tipo, rubrica, valor, cargo, salario in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['sindicato'] = sindicato
                linha['data_inicial'] = data_inicial
                linha['nome'] = nome
                linha['tipo'] = tipo
                linha['cpf'] = cpf
                linha['rg_numero'] = rg_numero
                linha['ctps'] = ctps
                linha['nis'] = nis
                linha['rubrica'] = rubrica
                linha['valor'] = valor
                linha['cargo'] = cargo
                linha['salario'] = salario or 0
                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Sindicatos'
            rel.colunas = [
                ['nome' , 'C', 50, u'Nome', False],
                ['data_inicial' , 'D', 10, u'Admissão', False],
                ['tipo' , 'C', 5, u'Tipo', False],
                ['cpf' , 'C', 15, u'CPF', False],
                ['rg_numero' , 'C', 15, u'RG', False],
                ['ctps' , 'C', 15, u'CTPS', False],
                ['nis' , 'C', 15, u'PIS', False],
                ['cargo' , 'C', 25, u'Cargo', False],
                ['salario' , 'F', 10, u'Salário', False],
            ]

            if rel_obj.inclui_valores:
                rel.colunas.append(['valor' , 'F', 10, u'Valor', True])

            rel.monta_detalhe_automatico(rel.colunas)

            if rel_obj.inclui_valores:
                rel.grupos = [
                    #['empresa', u'Empresa', False],
                    ['sindicato', u'Sindicato', False],
                    ['rubrica', u'Rubrica', False],
                ]
            else:
                rel.grupos = [
                    #['empresa', u'Empresa', False],
                    ['sindicato', u'Sindicato', False],
                ]

            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name  + u' -  PERIODO ' + formata_data(rel_obj.data_inicial) + ' - ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            rel.colunas.insert(0, ['empresa' , 'C', 60, u'Unidade', True])
            rel.colunas.insert(1, ['sindicato' , 'C', 60, u'Sindicato', True])
            rel.monta_detalhe_automatico(rel.colunas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'relacao_sindicato.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'relacao_sindicato.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True


    def gerar_resumo_folha_por_rubrica(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            if rel_obj.tipo == 'T':
                tipos = ('N', 'R')
            elif rel_obj.tipo == 'N':
                tipos = "('N')"
            elif rel_obj.tipo == 'D':
                tipos = "('D')"
            else:
                tipos = "('R')"

            cr.execute("""
                select distinct
                    p.cnpj_cpf
                from
                    res_company c
                    join res_partner p on p.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id

                where
                    p.cnpj_cpf is not null
                    and p.cnpj_cpf != ''
                    and (
                    c.id = """ + str(rel_obj.company_id.id) + """
                    or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                    )
                order by
                    p.cnpj_cpf;
            """)
            todos_cnpjs = cr.fetchall()

            cnpjs = []
            for cnpj, in todos_cnpjs:
                cnpjs.append(cnpj)


            rel = Report(u'Resumo Folha por Rubrica', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_resumo_folha_por_rubrica.jrxml')
            nome_arq = u'Resumo_folha_.pdf'

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['TIPOS'] = str(tipos)
            rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_calculo_gps(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            if rel_obj.tipo == 'T':
                tipos = ('N', 'R')
            elif rel_obj.tipo == 'N':
                tipos = "('N')"
            elif rel_obj.tipo == 'D':
                tipos = "('D')"
            else:
                tipos = "('R')"

            cr.execute("""
                select distinct
                    p.cnpj_cpf
                from
                    res_company c
                    join res_partner p on p.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id

                where
                    p.cnpj_cpf is not null
                    and p.cnpj_cpf != ''
                    and (
                    c.id = """ + str(rel_obj.company_id.id) + """
                    or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                    )
                order by
                    p.cnpj_cpf;
            """)
            todos_cnpjs = cr.fetchall()

            cnpjs = []
            for cnpj, in todos_cnpjs:
                cnpjs.append(cnpj)


            rel = Report(u'Resuma Folho por Rubrica', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_calculo_gps.jrxml')
            nome_arq = u'Resumo_Calculo_GPS_.pdf'

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['TIPOS'] = str(tipos)
            rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_cargo_salario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            sql = """
                select
                     rp.name as empresa,
                     hca.data_alteracao as data_alteracao,
                     e.nome,
                     co.id,
                     '[' || co.name || '] ' || e.nome as codigo,
                     job.name,
                     coalesce(
                     case when hca.wage = 0 then
                     co.wage
                     else
                     hca.wage
                     end, 0) as salario,

                     case
                     when hca.unidade_salario = '1' then
                     'Por hora'
                     else
                     'Por mês'
                     end as unidade_salarial,
                     case
                     when hca.tipo_alteracao = 'R' then
                     'Remuneração'
                     else
                     'Cargo'
                     end as Alteracao,
                    coalesce(m.descricao, '') as motivo

                from hr_contract_alteracao hca
                join hr_contract co on co.id = hca.contract_id
                join hr_employee e on e.id = co.employee_id
                join hr_job job on job.id = co.job_id
                join res_company c on c.id = co.company_id
                join res_partner rp on rp.id = c.partner_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                left join hr_motivo_alteracao_contratual m on m.id = hca.motivo_id

                where
                hca.tipo_alteracao in ('R','C')

                """

            if rel_obj.contract_id:
                sql += """
                and hca.contract_id = """ + str(rel_obj.contract_id.id)

            if rel_obj.company_id:
                data_inicial = parse_datetime(rel_obj.data_inicial).date()
                data_final = parse_datetime(rel_obj.data_final).date()
                date_inicial = str(data_inicial)[:10]
                date_final = str(data_final)[:10]
                sql += """
                and (
                    c.id = """ + str(rel_obj.company_id.id) + """
                    or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                )"""
                sql += """
                and data_alteracao between '""" + date_inicial + """' and '""" + date_final + """'"""

            sql += """
                order by
                 rp.name , e.nome, data_alteracao, salario """

            sql = sql.format()
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')
            salario_anterior = 0
            id_anterior = 0
            for empresa, data_alteracao, empregado, id,  codigo, cargo, salario, unidade_salarial, Alteracao, motivo in dados:
                linha = DicionarioBrasil()

                if id_anterior == 0:
                    id_anterior = id

                linha['empresa'] = empresa
                linha['empregado'] = empregado
                linha['codigo'] =  codigo
                linha['data_alteracao'] = data_alteracao
                linha['cargo'] = cargo
                linha['motivo'] = motivo

                if id_anterior == id:
                    if salario > 0:
                        if salario_anterior == 0:
                            percentual = 0
                            salario_anterior = salario

                        elif salario > salario_anterior :
                            percentual = (salario / salario_anterior -1 ) * 100
                            salario_anterior = salario

                    else:
                        percentual = 0

                    if salario == 0:
                        linha['salario'] = salario_anterior
                    else:
                        linha['salario'] = salario
                else:
                    percentual = 0
                    salario_anterior = salario
                    linha['salario'] = salario
                    id_anterior = id

                linha['percentual'] = D(percentual)
                linha['unidade_salarial'] = unidade_salarial
                linha['Alteracao'] = Alteracao
                linhas.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório Histórico de Cargo e Salário'
            rel.colunas = [
                ['data_alteracao' , 'D', 10, u'Data Alteração', False],
                ['salario' , 'F', 10, u'Salário', False],
                ['percentual' , 'F', 10, u'Perc. %', False],
                ['cargo' , 'C', 25, u'Cargo', False],
                ['unidade_salarial' , 'C', 10, u'Unidade Salarial', False],
                ['Alteracao' , 'C', 20, u'Tipo Alteração', False],
                ['motivo' , 'C', 30, u'Motivo', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                    ['empresa', u'Empresa', False],
                    ['codigo', u'Nome', False],
                ]

            rel.monta_grupos(rel.grupos)


            #company_obj = self.pool.get('res.company').browse(cr, uid, 1)
            #rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name  + u' -  PERIODO ' + formata_data(rel_obj.data_inicial) + ' - ' + formata_data(rel_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'relatorio_cargo_salario.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def onchange_contrato(self, cr, uid, ids, contract_id,  context={}):
        valores = {}
        retorno = {'value': valores}

        if contract_id:
            valores['company_id'] = ''
        else:
            valores['contract_id'] = ''
        return retorno

    def relatorio_media_salario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
            }

            sql = """
select
    co.name as empresa,
    cbo.codigo as cbo,
    cbo.ocupacao,
    c.name as codigo,
    e.nome as empregado,
    j.name as cargo,
    case
    when c.unidade_salario = '1' then coalesce((select cast(hl.quantity as numeric(18, 2)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'SALARIO_BASE'), 0.00)
    else c.horas_mensalista
    end as carga_horaria,
    c.wage as salario,
    c.unidade_salario

from
        hr_payslip h
    join hr_contract c on c.id = h.contract_id
    join hr_employee e on e.id = h.employee_id
    join hr_job j on j.id = c.job_id
    join hr_cbo cbo on cbo.id = j.cbo_id
    join res_company co on co.id = h.company_id
    left join res_company cc on cc.id = co.parent_id
    left join hr_payslip_afastamento hf on hf.payslip_id = h.id

where
        h.tipo = 'N'
    and c.date_end is null
    and c.categoria_trabalhador not in ('102','722','901','701','702','703')
    and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
    and (h.simulacao is null or h.simulacao = False)
    """
    #and hf.id is null"""

            if rel_obj.company_id:
                filtro['company_id'] = rel_obj.company_id.id
                sql += """
    and (
        co.id = {company_id}
        or co.parent_id = {company_id}
        or cc.parent_id = {company_id}
    )"""

            if rel_obj.job_id:
                filtro['job_id'] = rel_obj.job_id.id
                sql += """
    and j.id = {job_id}
    """

            sql += """
order by
    cbo.codigo,
    j.name,
    c.unidade_salario,
    e.nome;
"""

            sql = sql.format(**filtro)

            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            medias = {}
            quantidade = 1
            for empresa, cbo, ocupacao, codigo, empregado, cargo, carga_horaria, salario, unidade_salario in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['cbo'] = cbo
                #linha['ocupacao'] = ocupacao
                linha['codigo'] = codigo
                linha['empregado'] = empregado
                linha['cargo'] = cargo
                linha['carga_horaria'] = D(carga_horaria)
                linha['salario'] = D(salario)

                if unidade_salario == '1':
                    linha['salario_hora'] = D(salario)
                    salario_hora = D(salario)
                else:
                    salario_hora = D(salario) / D(carga_horaria or 1)
                    salario_hora = salario_hora.quantize(D('0.01'))
                    linha['salario_hora'] = salario_hora

                #chave = cargo + unidade_salario
                chave = cargo

                linha['chave'] = chave

                linhas.append(linha)

                if chave not in medias:
                    medias[chave] = [D(1), salario_hora, salario_hora, salario_hora, salario_hora]
                else:
                    medias[chave][0] += D(1)
                    medias[chave][1] += D(salario_hora)
                    medias[chave][2] = medias[chave][1] / medias[chave][0]
                    medias[chave][2] = medias[chave][2].quantize(D('0.01'))

                    if D(salario) > medias[chave][3]:
                        medias[chave][3] = D(salario_hora)

                    if D(salario) < medias[chave][4]:
                        medias[chave][4] = D(salario_hora)

            for linha in linhas:
                chave = linha.chave
                salario = linha.salario_hora

                media = medias[chave][2]
                maior = medias[chave][3]
                menor = medias[chave][4]

                if salario == media:
                    texto_media =     u'= média (' + formata_valor(salario) + ')'
                elif salario > media:
                    if salario == maior:
                        texto_media = u'* maior (' + formata_valor(media) + ')'
                    else:
                        texto_media = u'  acima (' + formata_valor(media) + ')'
                elif salario < media:
                    if salario == menor:
                        texto_media = u'* menor (' + formata_valor(media) + ')'
                    else:
                        texto_media = u' abaixo (' + formata_valor(media) + ')'

                linha['media'] = texto_media

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Média de Salário'
            rel.monta_contagem = True
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['empregado' , 'C', 30, u'Funcionário', False],
                ['salario' , 'F', 15, u'Salário contratual', False],
                ['carga_horaria' , 'F', 13, u'Carga horária', False],
                ['salario_hora' , 'F', 15, u'Salário hora', True],
                ['media' , 'C', 20, u'Média', False],

            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['cbo', u'CBO', False],
                ['cargo', u'Função', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'De ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u', empresa/Unidade ' + rel_obj.company_id.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'media_salario.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_estrutura_salario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):

            rel = Report(u'Estrutura de Salário', cr, uid)


            if rel_obj.struct_id.id:
                rel.parametros['REGISTRO_ID'] = rel_obj.struct_id.id
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_estrutura_salario.jrxml')
                recibo = 'estrutura_' + rel_obj.struct_id.name + '.pdf'
            else:

                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_estrutura_salario_sintetico.jrxml')
                recibo = 'estruturas_salario.pdf'

            pdf, formato = rel.execute()

            dados = {
                    'nome': recibo,
                    'arquivo': base64.encodestring(pdf),
                }
            rel_obj.write(dados)

            return True

    def gera_relatorio_regra_salario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):

            rel = Report(u'Regras de Salário', cr, uid)

            if rel_obj.rule_id:
                rel.parametros['REGISTRO_ID'] = rel_obj.rule_id.id
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_regra_salario.jrxml')
                recibo = 'regra_' + rel_obj.rule_id.name + '.pdf'
            else:

                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_regra_salario_sintetico.jrxml')
                recibo = 'regras_salario.pdf'

            pdf, formato = rel.execute()

            dados = {
                    'nome': recibo,
                    'arquivo': base64.encodestring(pdf),
                }
            rel_obj.write(dados)

            return True

    def gera_relatorio_hierarquia_salario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):

            rel = Report(u'Hierarquia da Estrutura de Salários', cr, uid)
            rel.parametros['REGISTRO_ID'] = rel_obj.rule_id.id
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_estrutura_hierarquica.jrxml')
            recibo = 'estrutura_hierarquica_salarios.pdf'

            pdf, formato = rel.execute()

            dados = {
                    'nome': recibo,
                    'arquivo': base64.encodestring(pdf),
                }
            rel_obj.write(dados)

            return True

    def gera_relatorio_folha(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            competencia = parse_datetime(data_inicial).strftime(b'%B-%Y').decode('utf-8')
            if rel_obj.tipo == 'T':
                tipos = ('N', 'R')
            elif rel_obj.tipo == 'N':
                tipos = "('N')"
            elif rel_obj.tipo == 'D':
                tipos = "('D')"
            else:
                tipos = "('R')"

            ##cr.execute("""
                ##select distinct
                    ##p.id
                ##from
                    ##res_company c
                    ##join res_partner p on p.id = c.partner_id
                    ##left join res_company cc on cc.id = c.parent_id

                ##where
                    ##p.cnpj_cpf is not null
                    ##and p.cnpj_cpf != ''
                    ##and (
                    ##c.id = """ + str(rel_obj.company_id.id) + """
                    ##or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    ##or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                    ##)
                ##order by
                    ##p.cnpj_cpf;
            ##""")
            ##todos_cnpjs = cr.fetchall()

            ##cnpjs = []
            ##for cnpj, in todos_cnpjs:
                ##cnpjs.append(cnpj)


            #
            # Adiantamento
            #
            #if rel_obj.tipo == 'D':
            #    if rel_obj.mes == '11':
            #        rel = Report(u'Analítico do Adiantamento do Décimo Terceiro', cr, uid)
            #        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analitico_adiantamento_13.jrxml')
            #        nome_arq = u'analitico_adiantamento_13o_' + competencia + u'.pdf'

            #    else:
            #        rel = Report(u'Analítico do Décimo Terceiro', cr, uid)
            #        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analitico_folha.jrxml')
            #        nome_arq = u'analitico_13o_' + competencia + u'.pdf'

            rel = Report(u'Analítico GPS-SEFIP', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_folha.jrxml')
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['COMPETENCIA'] = competencia
            rel.parametros['TIPOS'] = str(tipos)
            #rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')
            rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
            rel.parametros['COMPLEMENTAR'] = rel_obj.complementar
            rel.parametros['DETALHE_HOLERITE'] = rel_obj.detalhe_holerite
            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()
            nome_arq = u'analitico_gps_sefip_' + competencia + u'.' + rel_obj.formato_rel

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_salario_contribuicao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):

            rel = Report(u'RELAÇÃO DOS SALÁRIOS-DE-CONTRIBUIÇÃO', cr, uid)

            rel.parametros['CONTRACT_ID'] = rel_obj.contract_id.id
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_salario_contribuicao.jrxml')
            recibo = 'salario_contribucao_' + rel_obj.contract_id.employee_id.nome + '.pdf'

            pdf, formato = rel.execute()

            dados = {
                    'nome': recibo,
                    'arquivo': base64.encodestring(pdf),
                }
            rel_obj.write(dados)

            return True

    def gera_relatorio_quadro_horario(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            if not rel_obj.company_id.partner_id.cnpj_cpf and rel_obj.somente_cnpj:
                raise osv.except_osv(u'Erro!', u'Empresa selecionada não possue CNPJ!')

            elif rel_obj.company_id.partner_id.cnpj_cpf:
                cnpj = rel_obj.company_id.partner_id.cnpj_cpf
                raiz_cnpj = cnpj[:10]

            if rel_obj.somente_cnpj:
                cr.execute("""
                    select distinct
                    c.id

                    from res_company c
                    join res_partner p on p.id = c.partner_id
                    join sped_municipio m on m.id = p.municipio_id
                    join sped_cnae cn on cn.id = p.cnae_id

                    where
                    p.fone != ''
                    and p.cnpj_cpf like '""" + raiz_cnpj +  """%'

                """)

            else:
                cr.execute("""
                    select distinct
                    c.id

                    from res_company c
                    join res_partner p on p.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    join sped_municipio m on m.id = p.municipio_id
                    join sped_cnae cn on cn.id = p.cnae_id

                    where
                    (c.id = """ + str(rel_obj.company_id.id) + """
                    or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                    )
                    """)

            lista_cnpjs = cr.fetchall()
            conpany_ids = []
            for lista_cnpj in lista_cnpjs:
                conpany_ids.append(lista_cnpj[0])


            rel = Report(u'Quadro de Horário', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_quadro_horario.jrxml')
            nome_arq = u'QUADRO_HORARIO_'+  rel_obj.company_id.partner_id.name + '.' + rel_obj.formato_rel

            rel.parametros['COMPANY_IDS'] = str(tuple(conpany_ids)).replace("u'", "'").replace(',)', ')')
            rel.parametros['UID'] = uid
            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_provisao_ferias(self, cr, uid, ids, context={}):
        for rel_obj in self.browse(cr, uid, ids):
            #sql = SQL_PROVISAO_FERIAS_RELATORIO

            #filtro = {
                #'competencia': str(rel_obj.ano).zfill(4) + '-' + rel_obj.mes.zfill(2),
                #'company_id': rel_obj.company_id.id,
            #}

            #sql_relatorio = sql.format(**filtro)

            #print(sql_relatorio)

            #data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            #data_inicial_mespassado =  parse_datetime(data_inicial) + relativedelta(months=-1)

            #rel = Report(u'Provisão de Férias', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_provisao_ferias.jrxml')
            #nome_arq = u'provisao_ferias_' +  rel_obj.company_id.partner_id.name + '.pdf'

            #rel.parametros['SQL'] = sql_relatorio
            #rel.parametros['UID'] = uid
            #rel.parametros['MES_PASSADO'] = str(data_inicial_mespassado)[:10]
            #rel.parametros['DATA_INICIAL'] = str(parse_datetime(data_inicial))[:10]
            #rel.parametros['DATA_FINAL'] = str(parse_datetime(data_final))[:10]

            #if rel_obj.is_sintetico:
                #rel.parametros['IS_ANALITICO'] = False
            #else:
                #rel.parametros['IS_ANALITICO'] = True
                #if rel_obj.imprime_recibo:
                    #rel.parametros['RECIBO'] = True

            #pdf, formato = rel.execute()

            #dados = {
                #'nome': nome_arq,
                #'arquivo': base64.encodestring(pdf)
            #}
            #rel_obj.write(dados)
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            competencia = parse_datetime(data_inicial).strftime(b'%B-%Y').decode('utf-8')

            rel = Report(u'Analítico de Provisão de Férias', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_provisao.jrxml')
            nome_arq = u'analitico_provisao_ferias_' + competencia + u'.pdf'

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['COMPETENCIA'] = competencia
            rel.parametros['TIPOS'] = "('F')"
            #rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')
            rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
            rel.parametros['COMPLEMENTAR'] = False
            rel.parametros['DETALHE_HOLERITE'] = True
            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_provisao_13(self, cr, uid, ids, context={}):
        for rel_obj in self.browse(cr, uid, ids):
            #sql = SQL_PROVISAO_DECIMO_RELATORIO

            #data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            #data_inicial_mespassado =  parse_datetime(data_inicial) + relativedelta(months=-1)

            #filtro = {
                #'competencia': str(rel_obj.ano).zfill(4) + '-' + rel_obj.mes.zfill(2),
                #'competencia_anterior': str(data_inicial_mespassado)[0:7],
                #'company_id': rel_obj.company_id.id,
            #}

            #sql = sql.format(**filtro)

            #print(sql)

            #rel = Report(u'Provisão de 13º', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_provisao_13.jrxml')
            #nome_arq = u'provisao_13_' +  rel_obj.company_id.partner_id.name + '.pdf'

            #rel.parametros['SQL'] = sql
            #rel.parametros['UID'] = uid
            #rel.parametros['MES_PASSADO'] = str(data_inicial_mespassado)[:10]
            #rel.parametros['DATA_INICIAL'] = str(parse_datetime(data_inicial))[:10]
            #rel.parametros['DATA_FINAL'] = str(parse_datetime(data_final))[:10]

            #if rel_obj.is_sintetico:
                #rel.parametros['IS_ANALITICO'] = False
            #else:
                #rel.parametros['IS_ANALITICO'] = True

            #if rel_obj.imprime_recibo:
                #rel.parametros['RECIBO'] = True
            #else:
                #rel.parametros['RECIBO'] = False

            #pdf, formato = rel.execute()

            #dados = {
                #'nome': nome_arq,
                #'arquivo': base64.encodestring(pdf)
            #}
            #rel_obj.write(dados)
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            competencia = parse_datetime(data_inicial).strftime(b'%B-%Y').decode('utf-8')

            rel = Report(u'Analítico de Provisão de 13º', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_provisao.jrxml')
            nome_arq = u'analitico_provisao_decimo_terceiro_' + competencia + u'.pdf'

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['COMPETENCIA'] = competencia
            rel.parametros['TIPOS'] = "('D')"
            #rel.parametros['CNPJS'] = str(tuple(cnpjs)).replace("u'", "'").replace(',)', ')')
            rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
            rel.parametros['COMPLEMENTAR'] = False
            rel.parametros['DETALHE_HOLERITE'] = True
            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_curso_treinamento(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            dados_filtro = {
                'company_id': company_id,
            }

            if rel_obj.tipo == 'T':
                dados_filtro['tipo'] = '%'

            elif rel_obj.tipo == 'D':
                dados_filtro['tipo'] = 'D'

            elif rel_obj.tipo == 'F':
                dados_filtro['tipo'] = 'F'

            sql = """
               select
                    rp.name as empresa,
                    e.nome as funcionario,
                    t.nome as curso,
                    hc.carga_horaria as carga_horaria,
                    hc.data_inicial,
                    hc.data_final,
                    case
                    when hc.situacao = '1' then
                    'Cursando'
                    when hc.situacao = '2' then
                    'Suspenso'
                    else
                    'Concluido'
                    end as situacao

                from hr_contract_curso_treinamento hc
                    join hr_curso_treinamento t on t.id = hc.curso_id
                    join hr_contract co on co.id = hc.contract_id
                    join hr_employee e on e.id = co.employee_id
                    join res_company c on c.id = co.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id
                where
                    co.date_end is null
                    and (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                    )"""

            if rel_obj.contract_id:
                sql +="""
                    and co.id = """ + str(rel_obj.contract_id.id)

            if rel_obj.curso_id:
                sql +="""
                    and t.id = """ + str(rel_obj.curso_id.id)

            sql +="""
                    order by
                    c.id, e.nome;"""

            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, funcionario, curso, carga_horaria, data_inicial, data_final, situacao in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['funcionario'] = funcionario
                linha['curso'] = curso
                linha['carga_horaria'] = carga_horaria
                linha['data_inicial'] = data_inicial
                linha['data_final'] = data_final
                linha['situacao'] = situacao
                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Cursos e Treinamentos Funcionários'
            rel.colunas = [
                ['curso', 'C', 80, u'Curso/Treinamento', False],
                ['carga_horaria', 'F', 10, u'Carga Horária', False],
                ['data_inicial', 'D', 10, u'Período de ', False],
                ['data_final', 'D', 10, u'Período até', False],
                ['situacao', 'C', 10, u'Situação', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Unidade', False],
                ['funcionario', u'Funcionário', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relacao_curso_treinamento.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_relacao_irrf(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))
            competencia = parse_datetime(data_inicial).strftime(b'%B-%Y').decode('utf-8')
            if rel_obj.tipo == 'T':
                tipos = ('N', 'R')
            elif rel_obj.tipo == 'N':
                tipos = "('N')"
            elif rel_obj.tipo == 'D':
                tipos = "('D')"
            else:
                tipos = "('R')"

            rel = Report(u'MEMÓRIA DE CÁLCULO E RELAÇÃO DE PAGAMENTO DE IRRF', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_relatorio_irrf.jrxml')
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['COMPETENCIA'] = competencia
            rel.parametros['TIPOS'] = str(tipos)
            rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
            rel.parametros['COMPLEMENTAR'] = rel_obj.complementar
            rel.outputFormat = rel_obj.formato_rel

            pdf, formato = rel.execute()
            nome_arq = u'memorio_calculo_pagamento_irrf_' + competencia + u'.' + rel_obj.formato_rel

            dados = {
                'nome': nome_arq,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_anivirsario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            if not rel_obj.is_sintetico:
                data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            else:
                date_inicial = parse_datetime(rel_obj.data_inicial).date()
                date_final = parse_datetime(rel_obj.data_final).date()

                data_inicial = str(date_inicial)[:10]
                data_final = str(date_final)[:10]

                mes_inicial = data_inicial[5:7]
                mes_final = data_final[5:7]

            dados_filtro = {
                'company_id': company_id,
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            if not rel_obj.is_sintetico:
                dados_filtro['mes'] =  data_inicial[5:7]

            else:
                dados_filtro['mes_inicial'] =  mes_inicial
                dados_filtro['mes_final'] =  mes_final

            sql = """
                select
                    rp.name as empresa,
                    e.nome,
                    job.name as job,
                    co.date_start,
                    e.data_nascimento,
                    e.cpf,
                    e.sexo,
                    (select dp.name
                    from hr_contract_alteracao caa
                    join hr_department dp on dp.id = caa.department_id
                    where
                    caa.contract_id = co.id                
                    order by
                        caa.data_alteracao desc
                    limit 1
                    ) as departamento_lotacao,
                    to_char(e.data_nascimento,'DD/MM') || '/2016' as data_order

                from
                    hr_contract co
                    join hr_employee e on e.id = co.employee_id
                    join hr_job job on job.id = co.job_id
                    join res_company c on c.id = co.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                where
                    (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                    )"""

            if not rel_obj.is_sintetico:
                sql += """
                    and (co.date_end is null                    
                    or
                    co.date_end between '{data_inicial}' and '{data_final}'
                    )
                    and to_char(e.data_nascimento,'MM') between '{mes}' and '{mes}' """
            else:
                sql += """
                    and co.date_end is null
                    and to_char(e.data_nascimento,'MM') between '{mes_inicial}' and '{mes_final}' """

            sql += """
                order by
                    rp.name,                    
                    e.nome;"""

            sql = sql.format(**dados_filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, cargo, date_start, data_nascimento, cpf, sexo, departamento_lotacao, data_order in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['cargo'] = cargo
                linha['date_start'] = date_start
                linha['data_nascimento'] = data_nascimento
                linha['cpf'] = cpf
                linha['sexo'] = sexo
                linha['departamento'] = departamento_lotacao
                data_inicial = parse_datetime(data_inicial)
                data_nascimento =parse_datetime(data_nascimento)
                linha['anos'] = idade_anos(data_nascimento,data_nascimento + relativedelta(year=rel_obj.ano))
                linha['dia'] = data_order

                linhas.append(linha)

            if rel_obj.is_sintetico:
                rel = RHRelatorioAutomaticoPaisagem()
            else:
                rel = RHRelatorioAutomaticoRetrato()
                
            rel.title = u'Aniversários ' + MESES_DIC[rel_obj.mes] + u'/' + str(rel_obj.ano)
            rel.colunas = [
                #['dia', 'D', 15, u'Data ', False],
                ['nome', 'C', 30, u'Nome', False],
                ['sexo', 'C', 4, u'Sexo', False],
                ['cpf', 'C', 12, u'CPF', False],
                ['cargo', 'C', 30, u'Cargo', False],
            ]
            
            if rel_obj.is_sintetico:
                rel.colunas += [
                    ['departamento', 'C', 20, u'Departamento', False],                
                    ['date_start', 'D', 15, u'Data Inicio ', False],
                    ['data_nascimento', 'D', 15, u'Data Nascimento ', False],
                    ['anos', 'I', 5, u'Anos', False],
                ]
            else:
                rel.colunas += [                
                    ['date_start', 'D', 15, u'Data Inicio ', False],
                    ['data_nascimento', 'D', 15, u'Data Nascimento ', False],
                    ['anos', 'I', 5, u'Anos', False],
                ]
                
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)


            dados = {
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)


            dados = {
                'nome': u'relatorio_aniversariantes_' + str(rel_obj.ano) + u'_' + str(rel_obj.mes) + '.' + rel_obj.formato,
                'arquivo': base64.encodestring(pdf),
                'nome_csv': u'relatorio_aniversariantes_' + str(rel_obj.ano) + u'_' + str(rel_obj.mes) + u'.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_falta(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]


            dados_filtro = {
                'company_id': company_id,
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            if rel_obj.tipo_falta == 'F':
                dados_filtro['tipo'] = "('F')"
                nome_rel = u'Falta'

            elif rel_obj.tipo_falta == 'S':
                dados_filtro['tipo'] = "('S')"
                nome_rel = u'Suspensão'

            elif rel_obj.tipo_falta == 'A':
                dados_filtro['tipo'] = "('A')"
                nome_rel = u'Advertência'

            else:
                dados_filtro['tipo'] = "('F','S','A')"
                nome_rel = u'Falta/Suspensão/Advertência'

            sql = """
                select
                    rp.name as empresa,
                    e.nome,
                    co.date_start,
                    case
                    when f.tipo = 'F' then
                    'Falta'
                    when f.tipo = 'S' then
                    'Suspensão'
                    else
                    'Advertência' end as tipo,
                    f.data,
                    f.obs

                from
                    hr_falta f
                    join hr_contract co on co.id = f.contract_id
                    join hr_employee e on e.id = co.employee_id
                    join res_company c on c.id = co.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                where
                    f.tipo in {tipo}
                    and f.data between '{data_inicial}' and '{data_final}'
                    and(
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )"""

            if rel_obj.contract_id:
                sql += """
                    and co.id = """ + str(rel_obj.contract_id.id)

            sql += """
                order by
                    e.nome,
                    data;"""

            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, date_start, tipo, data, obs in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['date_start'] = date_start
                linha['tipo'] = tipo
                linha['data'] = data
                linha['obs'] = obs

                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de ' + nome_rel
            rel.colunas = [
                ['nome', 'C', 30, u'Nome', False],
                ['date_start', 'D', 10, u'Dt. Inicio Contr. ', False],
                ['data', 'D', 10, u'Data', False],
                ['tipo', 'C', 15, u'Tipo', False],
                ['obs', 'C', 40, u'Observações', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade: ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relato_faltas_suspensao_advertencia.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_exame(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]


            dados_filtro = {
                'company_id': company_id,
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            sql = """
                select
                    rp.name as empresa,
                    e.nome,
                    ce.data_exame,
                    ce.data_validade,
                    he.descricao,
                    job.name as job

                    from hr_contract_exame ce
                    join hr_exame as he on he.id = ce.exame_id
                    join hr_contract co on co.id = ce.contract_id
                    join hr_job job on job.id = co.job_id
                    join hr_employee e on e.id = co.employee_id
                    join res_company c on c.id = co.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                where
                    ce.data_validade between '{data_inicial}' and '{data_final}'
                    and(
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )"""

            if rel_obj.contract_id:
                sql += """
                    and co.id = """ + str(rel_obj.contract_id.id)

            if rel_obj.exame_id:
                sql += """
                    and he.id = """ + str(rel_obj.exame_id.id)

            sql += """
                order by
                    ce.data_validade,
                    e.nome,
                    he.descricao;"""

            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, date_exame, date_validade, descricao, cargo in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['date_exame'] = date_exame
                linha['date_validade'] = date_validade
                dia_vencido = hoje() - parse_datetime(date_validade).date()
                linha['dia_vencido'] =  dia_vencido.days
                linha['descricao'] = descricao
                linha['cargo'] = cargo
                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Exames'
            rel.colunas = [
                ['nome', 'C', 40, u'Nome', False],
                ['cargo', 'C', 25, u'Função', False],
                ['descricao', 'C', 25, u'Exame', False],
                ['date_exame', 'D', 10, u'Dt.Exame. ', False],
                ['date_validade', 'D', 10, u'Dt.Validade', False],
                ['dia_vencido', 'I', 10, u'Dias Atraso', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade: ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relato_faltas_suspensao_advertencia.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_experiencia(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]


            dados_filtro = {
                'company_id': company_id,
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            sql = """
               select
                    rp.name as empresa,
                    e.nome,
                    co.date_start,
                    co.final_prim_esperiencia,
                    co.final_seg_esperiencia

                    from hr_contract co
                    join hr_job job on job.id = co.job_id
                    join hr_employee e on e.id = co.employee_id
                    join res_company c on c.id = co.company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                where
                    co.date_start between '{data_inicial}' and '{data_final}'
                    and(
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )"""

            if rel_obj.contract_id:
                sql += """
                    and co.id = """ + str(rel_obj.contract_id.id)

            sql += """
                order by
                    rp.name,
                    co.date_start,
                    e.nome;"""

            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, date_start, final_prim_esperiencia, final_seg_esperiencia in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['date_start'] = date_start
                linha['final_prim_esperiencia'] = final_prim_esperiencia
                linha['final_seg_esperiencia'] = final_seg_esperiencia

                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Vencimento Experiência'
            rel.colunas = [
                ['nome', 'C', 40, u'Nome', False],
                ['date_start', 'D', 10, u'Dt.Admissão ', False],
                ['final_prim_esperiencia', 'D', 20, u'Dt. Primeira Experiência', False],
                ['final_seg_esperiencia', 'D', 20, u'Dt .Segunda Experiência', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade: ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'relatorio_vencimento_experiencia.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_endereco_funcionario(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            #data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            #date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]


            dados_filtro = {
                'company_id': company_id,
                'data_final': data_final,
            }

            sql = """

                select DISTINCT

                       rp.name  || ' - ' || c.cnpj_cpf as empresa,
                       e.nome as pmpregado,
                       e.endereco as endereco,
                       e.numero as numero,
                       e.bairro as bairro,
                       e.cidade  || '- ' || e.estado as cidade,
                       e.cep as cep


                from hr_contract co
                join hr_employee e on e.id = co.employee_id
                join res_company c on c.id = co.company_id
                join res_partner rp on rp.id = c.partner_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id

                where (co.date_end is null or co.date_end > cast('{data_final}' as date))
                and co.date_start <= cast('{data_final}' as date)
                and co.categoria_trabalhador not in ('102','722','901','701','702','703')
                and(
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                )

                order by
                    1,
                    e.nome;"""

            cr.execute(sql.format(**dados_filtro))

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for empresa, nome, endereco, numero, bairro, cidade, cep in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['nome'] = nome
                linha['endereco'] = endereco
                linha['numero'] = numero
                linha['bairro'] = bairro
                linha['cidade'] = cidade
                linha['cep'] = cep

                linhas.append(linha)


            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório Endereço de Funcionário'
            rel.colunas = [
                ['nome', 'C', 40, u'Funcionário', False],
                ['endereco', 'C', 25, u'Endereço ', False],
                ['numero', 'C', 10, u'Número', False],
                ['bairro', 'C', 15, u'Bairro', False],
                ['cidade', 'C', 25, u'Cidade/Estado', False],
                ['cep', 'C', 10, u'CEP', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade: ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': u'relatorio_endereco_funcionarios.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': u'relatorio_endereco_funcionarios.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True


hr_relatorio()
