# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, idade, agora
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
import csv
from gdata.health import Ccr
from pybrasil.base import DicionarioBrasil
from integra_rh.constantes_rh import *


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
    # ('13', 'décimo terceiro'),
)

MESES_DIC = dict(MESES)

TIPOS = (
    ('T', 'Todos'),
    ('N', 'Somente holerites'),
    ('R', 'Somente rescisões'),
)
SEXO = (
    ('M', 'Masculino'),
    ('F', 'Feminino'),
    ('', 'Ambos'),
)


class hr_relatorio(osv.osv_memory):
    _inherit = 'hr.relatorio'
    _name = 'hr.relatorio'

    _columns = {
        'department_id': fields.many2one('hr.department', u'Departamento', ondelete='restrict'),
        'company_ids': fields.many2many('res.company','hr_relatorio_company', 'hr_relatorio_id', 'company_id', string=u'Empresas'),
    }

    def gera_listagem_seguros_seguranca(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            sql = '''
            select
                a.name,
                e.nome,
                e.sexo,
                case
                    when a.unidade_salario = '1' then cast(a.wage * coalesce(a.horas_mensalista, 220) as numeric(18,2))
                    else cast(a.wage as numeric(18,2))
                end as salario,
                e.data_nascimento as nascimento,
                e.cpf as cpf,
                case
                    when a.unidade_salario = '1' then cast(a.wage * coalesce(a.horas_mensalista, 220) as numeric(18,2)) * 26
                    else cast(a.wage as numeric(18,2)) * 26
                end as pagamento,
                case
                    when a.unidade_salario = '1' then trunc(cast(a.wage * coalesce(a.horas_mensalista, 220) * 26 as numeric(18, 2)) * 0.02596 / 100, 2)
                    else trunc((a.wage * 26) * 0.02596 / 100 , 2)
                end as variavel_pagamento

            from
                hr_contract a
                join res_company c on c.id = a.company_id
                join hr_employee e on e.id = a.employee_id

            where
                (a.date_end is null or a.date_end > '{data}')
                and a.date_start <= '{data}'
                and a.categoria_trabalhador not in ('102','722','901','701','702','703')
                and (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                )
            order by
                c.name,
                e.nome;
            '''

            sql = sql.format(data=rel_obj.data, company_id=rel_obj.company_id.id)

            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []

            for matricula,nome,sexo,salario,nascimento,cpf, pagamento, variavel_pagamento in dados:
                linha = DicionarioBrasil()
                linha['matricula'] = matricula
                linha['nome'] = nome
                linha['sexo'] = sexo
                linha['salario'] = salario
                linha['nascimento'] = nascimento
                linha['cpf'] = cpf
                linha['pagamento'] = pagamento
                linha['variavel_pagamento'] = variavel_pagamento
                linha['cpf'] = cpf
                linha['numero_apolice'] = '859501'
                linha['numero'] = '001'
                linha['endereco'] = 'SVR TILIA, 26'
                linha['bairro'] = 'CENTRO'
                linha['cidade'] = 'CHAPECO'
                linha['cep'] = '89802242'
                linha['uf'] = 'SC'
                linhas.append(linha)


            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Seguro de Vida Segurança'
            rel.colunas = [
                ['matricula' , 'C', 10, u'Matrícula', False],
                ['nome' , 'C', 35, u'Matrícula', False],
                ['nascimento' , 'D', 10, u'Nascimento', False],
                ['salario' , 'F', 10, u'Salario Base', False],
                ['numero_apolice' , 'C', 10, u'Nº Apólice', False],
                ['numero' , 'C', 5, u'', False],
                ['sexo' , 'C', 5, u'Sexo', False],
                ['cpf' , 'C', 16, u'Cpf', False],
                ['endereco' , 'C', 10, u'Endereço', False],
                ['bairro' , 'C', 8, u'Bairro', False],
                ['cidade' , 'C', 8, u'Cidade', False],
                ['cep' , 'C', 8, u'Cep', False],
                ['uf' , 'C', 2, u'UF', False],
                ['pagamento' , 'F', 15, u'Valor do Seguro', False],
                ['variavel_pagamento' , 'F', 8, u'Variavel', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + rel_obj.company_id.name  + u' -  Até ' + formata_data(rel_obj.data)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'relacao_seguro_segurança.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'relacao_seguro.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_funcionarios_telma(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial, data_final = primeiro_ultimo_dia_mes(rel_obj.ano, int(rel_obj.mes))

            sql = """
                select
                    co.name as empresa,
                    c.name as matricula,
                    e.id as codigo,
                    e.nome as empregado,
                    j.name as cargo,
                    c.date_start as data_contratacao,
                    cast(case
                        when (c.wage is null or c.wage = 0) then coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'BASE_INSS'), 0.00)
                        when c.unidade_salario = '1' then coalesce((select sum(coalesce(hl.total, 0.00)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code in ('SALARIO_BASE', 'DSR_HORISTA')), 0.00)
                        else cast(c.wage as numeric(18,2))
                    end as numeric(18,2)) as salario,
                    case
                        when (c.wage is null or c.wage = 0) then trunc(cast(coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'BASE_INSS'), 0.00) as numeric(18,2)) / 100, 2)
                        when c.unidade_salario = '1' then trunc(cast(coalesce((select sum(coalesce(hl.total, 0.00)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code in ('SALARIO_BASE', 'DSR_HORISTA')), 0.00) as numeric(18,2)) / 100, 2)
                        else trunc(cast(c.wage as numeric(18,2)) / 100.00, 2)
                    end as seguro

                from
                    hr_contract c
                    join res_company co on co.id = c.company_id
                    join hr_employee e on e.id = c.employee_id
                    join hr_job j on j.id = c.job_id
                    join hr_payslip h on h.contract_id = c.id
                    left join hr_payslip_afastamento hf on hf.payslip_id = h.id

                where
                        c.date_end is null
                    and h.tipo ='N'
                    and h.date_from >= '{data_inicial}' and  h.date_to <= '{data_final}'
                    and h.holerite_anterior_id is null
                    and hf.id is null
                    and c.categoria_trabalhador not in ('102','722','901','701','702','703')
                    and c.company_id in (38,44,67,69,72)
                order by
                    co.name, e.nome;
            """

            cr.execute(sql.format(data_inicial=data_inicial, data_final=data_final))

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            for empresa, matricula, codigo, nome, cargo, date_start, salario, seguro in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['matricula'] = matricula
                linha['codigo'] = codigo
                linha['nome'] = nome
                linha['cargo'] = cargo
                linha['date_start'] = date_start
                linha['salario'] = salario
                linha['seguro'] = seguro
                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Seguro 1%'
            rel.colunas = [
                ['matricula' , 'C', 10, u'Matrícula', False],
                ['codigo' , 'I', 5, u'Código', False],
                ['nome' , 'C', 40, u'Nome', False],
                ['cargo' , 'C', 20, u'Cargo', False],
                ['date_start' , 'D', 10, u'Admissão', False],
                ['salario' , 'F', 10, u'Salario Base', True],
                ['seguro' , 'F', 10, u'Seguro', True],

            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name  + u' -  PERIODO ' + formata_data(data_inicial) + ' - ' + formata_data(data_final)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'relacao_seguro_funcionario.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'relacao_seguro_funcionario.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_funcionarios_ativos_sexo_categoria(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            data_inicial = rel_obj.data_inicial
            data_final = rel_obj.data_final

            sql = """
select
    c.name as unidade,
    rp.cnpj_cpf,
    e.nome as funcionario,
    e.sexo as sexo,
    co.categoria_trabalhador,
    e.data_nascimento

from
    hr_contract co
    join hr_employee e on e.id = co.employee_id
    join res_company c on c.id = co.company_id
    join res_partner rp on rp.id = c.partner_id

where
    (co.date_end is null or co.date_end > '{data_inicial}')
    and co.date_start <= '{data_final}'
    and co.categoria_trabalhador not in ('102','722','901','701','702','703')
    and (c.id = {company_id}
    or c.parent_id = {company_id})

order by
    c.name,
    c.cnpj_cpf,
    e.sexo,
    co.categoria_trabalhador,
    e.nome;
            """

            cr.execute(sql.format(data_inicial=data_inicial, data_final=data_final, company_id=company_id))

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            for empresa, cnpj_cpf, funcionario, sexo, categoria_trabalhador, data_nascimento in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa + ' - ' + cnpj_cpf
                linha['funcionario'] = funcionario

                if sexo == 'F':
                    linha['sexo'] = 'Feminino'
                else:
                    linha['sexo'] = 'Masculino'

                linha['categoria'] = CATEGORIA_TRABALHADOR_DIC[categoria_trabalhador or '101']
                linha['data_nascimento'] = None
                linha['idade'] = 0

                if data_nascimento:
                    linha['data_nascimento'] = parse_datetime(data_nascimento)
                    linha['idade'] = idade(data_nascimento, data_final)

                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.monta_contagem = True
            rel.title = u'Funcionários ativos por sexo e categoria'
            rel.colunas = [
                ['empresa' , 'C', 60, u'Empresa', False],
                ['sexo' , 'C', 10, u'Sexo', False],
                ['categoria' , 'C', 30, u'Categoria', False],
                ['funcionario' , 'C', 60, u'Nome', False],
                ['data_nascimento' , 'D', 10, u'Nascimento', False],
                ['idade' , 'I', 5, u'Idade', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
                ['sexo', u'Sexo', False],
                ['categoria', u'Categoria', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + rel_obj.company_id.name  + u' -  PERIODO ' + formata_data(data_inicial) + ' - ' + formata_data(data_final)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'funcionarios_ativos_sexo_categoria.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'funcionarios_ativos_sexo_categoria.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_quadro_lotacao(self, cr, uid, ids, context={}):

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        filtro = {
            'filtro_company': '',
        }
        sql = """
            select
                dp.name as departamento,
                j.name as cargo,
                sum(case when c.name ilike '%CHAP%' then 1 else 0 end) as chapeco,
                sum(case when c.name ilike '%XAX%' then 1 else 0 end) as xaxin,
                sum(case when c.name ilike '%CAC%' then 1 else 0 end) as cacador,
                sum(case when c.name ilike '%SANTA%' then 1 else 0 end) as santa_cecilia,
                sum(case when c.name ilike '%LEB%' then 1 else 0 end) as lebon_regis,
                sum(case when c.name ilike '%BAL%' then 1 else 0 end) as balneario,
                sum(case when c.name ilike '%MIG%' then 1 else 0 end) as sao_miguel,
                sum(case when c.name ilike '%VILH%' then 1 else 0 end) as maravilha,
                sum(case when c.name ilike '%CUNH%' then 1 else 0 end) as cunha_poran,
                count(co.id) as contratos,

                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%CHAP%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as chapeco_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%XAX%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as xaxin_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%CAC%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as cacador_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%SANTA%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as santa_cecilia_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%LEB%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as lebon_regis_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%BAL%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as balneario_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%MIG%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as sao_miguel_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%VILH%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as maravilha_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id and cj.name ilike '%CUNH%'
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as cunha_poran_orcado,
                max(coalesce(
                    (select
                        sum(coalesce(jo.quantidade, 0)) as orcado
                    from
                        hr_job_orcamento jo
                        join res_company cj on cj.id = jo.company_id
                    where
                        jo.job_id = j.id
                        {filtro_company_orcamento}
                    )
                , 0)) as contratos_orcados

            from hr_contract co
                join hr_job j on j.id = co.job_id
                left join hr_department dp on dp.id = j.department_id
                join res_company c on c.id = co.company_id

            where
                co.date_end is null
                and co.categoria_trabalhador not in ('102','722','901','701','702','703')
                {filtro_company}

            group by
                dp.name,
                j.name

            order by
                dp.name,
                j.name;
        """

        if len(rel_obj.company_ids) == 1:

            filtro['filtro_company'] = """
            and (
                c.id = {company_id}
                or c.parent_id = {company_id}
            )
            """.format(company_id=rel_obj.company_ids[0].id)

            filtro['filtro_company_orcamento'] = """
            and (
                cj.id = {company_id}
                or cj.parent_id = {company_id}
            )
            """.format(company_id=rel_obj.company_ids[0].id)


        elif len(rel_obj.company_ids) > 1:


            company_ids = []
            for company_obj in rel_obj.company_ids:
                company_ids.append(company_obj.id)

            filtro['filtro_company'] = """
            and (
                c.id in {company_ids}
                or c.parent_id in {company_ids}
            )
            """.format(company_ids=str(tuple(company_ids)).replace(',)', ')'))

            filtro['filtro_company_orcamento'] = """
            and (
                cj.id in {company_ids}
                or cj.parent_id in {company_ids}
            )
            """.format(company_ids=str(tuple(company_ids)).replace(',)', ')'))


        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)

        dados = cr.fetchall()
        linhas = []
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')
        linhas = []

        total_chapeco = 0
        total_xaxin = 0
        total_cacador = 0
        total_santa_cecilia = 0
        total_lebon_regis = 0
        total_balneario = 0
        total_sao_miguel = 0
        total_maravilha = 0
        total_cunha_poran = 0
        total_contratos = 0
        total_chapeco_orcado = 0
        total_xaxin_orcado = 0
        total_cacador_orcado = 0
        total_santa_cecilia_orcado = 0
        total_lebon_regis_orcado = 0
        total_balneario_orcado = 0
        total_sao_miguel_orcado = 0
        total_maravilha_orcado = 0
        total_cunha_poran_orcado = 0
        total_contratos_orcados = 0

        for departamento, cargo, \
            chapeco, \
            xaxin, \
            cacador, \
            santa_cecilia, \
            lebon_regis, \
            balneario, \
            sao_miguel, \
            maravilha, \
            cunha_poran, \
            contratos, \
            chapeco_orcado, \
            xaxin_orcado, \
            cacador_orcado, \
            santa_cecilia_orcado, \
            lebon_regis_orcado, \
            balneario_orcado, \
            sao_miguel_orcado, \
            maravilha_orcado, \
            cunha_poran_orcado, \
            contratos_orcados in dados:

            linha = DicionarioBrasil()

            linha['departamento'] = departamento
            linha['cargo'] = cargo
            linha['chapeco'] = chapeco
            total_chapeco += chapeco
            linha['xaxin'] = xaxin
            total_xaxin += xaxin
            linha['cacador'] = cacador
            total_cacador += cacador
            linha['santa_cecilia'] = santa_cecilia
            total_santa_cecilia += santa_cecilia
            linha['lebon_regis'] = lebon_regis
            total_lebon_regis += lebon_regis
            linha['balneario'] = balneario
            total_balneario += balneario
            linha['sao_miguel'] = sao_miguel
            total_sao_miguel += sao_miguel
            linha['maravilha'] = maravilha
            total_maravilha += maravilha
            linha['cunha_poran'] = cunha_poran
            total_cunha_poran += cunha_poran
            linha['contratos'] = contratos
            total_contratos += contratos

            linha['chapeco_orcado'] = int(chapeco_orcado)
            total_chapeco_orcado += int(chapeco_orcado)
            linha['xaxin_orcado'] = int(xaxin_orcado)
            total_xaxin_orcado += int(xaxin_orcado)
            linha['cacador_orcado'] = int(cacador_orcado)
            total_cacador_orcado += int(cacador_orcado)
            linha['santa_cecilia_orcado'] = int(santa_cecilia_orcado)
            total_santa_cecilia_orcado += int(santa_cecilia_orcado)
            linha['lebon_regis_orcado'] = int(lebon_regis_orcado)
            total_lebon_regis_orcado += int(lebon_regis_orcado)
            linha['balneario_orcado'] = int(balneario_orcado)
            total_balneario_orcado += int(balneario_orcado)
            linha['sao_miguel_orcado'] = int(sao_miguel_orcado)
            total_sao_miguel_orcado += int(sao_miguel_orcado)
            linha['maravilha_orcado'] = int(maravilha_orcado)
            total_maravilha_orcado += int(maravilha_orcado)
            linha['cunha_poran_orcado'] = int(cunha_poran_orcado)
            total_cunha_poran_orcado += int(cunha_poran_orcado)
            linha['contratos_orcados'] = int(contratos_orcados)
            total_contratos_orcados += int(contratos_orcados)

            linhas.append(linha)

        linhas_totais = DicionarioBrasil()
        linhas_totais = {
            'chapeco':  total_chapeco,
            'xaxin': total_xaxin,
            'cacador': total_cacador,
            'santa_cecilia': total_santa_cecilia,
            'lebon_regis': total_lebon_regis,
            'balneario': total_balneario,
            'sao_miguel': total_sao_miguel,
            'maravilha': total_maravilha,
            'cunha_poran': total_cunha_poran,
            'contratos': total_contratos,

            'chapeco_orcado':  total_chapeco_orcado,
            'xaxin_orcado': total_xaxin_orcado,
            'cacador_orcado': total_cacador_orcado,
            'santa_cecilia_orcado': total_santa_cecilia_orcado,
            'lebon_regis_orcado': total_lebon_regis_orcado,
            'balneario_orcado': total_balneario_orcado,
            'sao_miguel_orcado': total_sao_miguel_orcado,
            'maravilha_orcado': total_maravilha_orcado,
            'cunha_poran_orcado': total_cunha_poran_orcado,
            'contratos_orcados': total_contratos_orcados,
        }

        dados = {
            'titulo': u'QUADRO DE LOTAÇÃO',
            'data': formata_data(agora()),
            'linhas': linhas,
            'linhas_totais': linhas_totais,
        }

        print(dados)

        nome_arquivo = JASPER_BASE_DIR + 'hr_quadro_lotacao.ods'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)

        dados = {
            'nome': 'quadro_lotacao.xlsx',
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True


hr_relatorio()

# #class ListagemSeguro(RelatoAutomatico):
    # #def __init__(self, *args, **kwargs):
        # #super(ListagemSeguro, self).__init__(*args, **kwargs)
        # #self.margin_top = 1 * cm
        # #self.margin_bottom = 1 * cm
        # #self.margin_left = 1 * cm
        # #self.margin_right = 1 * cm
        # #self.largura_maxima = self.largura_maxima + 2

        # #self.title = u'Relação para Seguro de Vida'
        # #self.author = 'ERP Integra'

        # #self.band_page_header = Cabecalho()

        # #for elemento in self.band_page_header.elements:
            # #elemento.width = self.largura_maxima *  cm

        # #self.band_page_header.child_bands = [self.band_titulos]
        # #self.band_page_footer = Rodape()

        # #for elemento in self.band_page_footer.elements:
            # #elemento.width = self.largura_maxima *  cm

        # #self.colunas = [
            # #['employee_id.nome'   , 'C', 60, u'Nome' , False],
            # #['employee_id.sexo'   , 'C', 1, u'Sexo' , False],
            # #['job_id.name', 'C', 30, u'Função', False],
            # #['wage', 'F', 10, u'Salário Base' , False],
            # #['employee_id.data_nascimento', 'D', 10, u'Nascimento' , False],
            # #['employee_id.cpf', 'C', 14, u'CPF', False],
        # #]

        # #self.monta_detalhe_automatico(self.colunas)

        # ##self.grupos = [
            # ##['lotacao_id.descricao', u'Tomador'],
        # ##]
        # ##self.monta_grupos(self.grupos)


# #def gera_listagem_seguro(self, cr, uid):

    # #contract_pool = self.pool.get('hr.contract')
    # #cr.execute('''
        # #select a.id
        # #from hr_contract a
        # #join res_company c on c.id = a.company_id
        # #join hr_employee e on e.id = a.employee_id
        # #order by e.nome;''')

    # #contract_ids = []
    # #for ret in cr.fetchall():
        # #contract_ids.append(ret[0])

    # #contract_objs = contract_pool.browse(cr, uid, contract_ids)

    # #impresso = ListagemSeguro()
    # ##impresso.title = u'Listagem de Férias Gozadas e Períodos Perdidos'

    # #retorno_pdf = StringIO()

    # #impresso.queryset = contract_objs
    # #impresso.generate_by(PDFGenerator, filename=retorno_pdf)

    # #pdf = retorno_pdf.getvalue()

    # #open('/home/ari/listagem_seguro.pdf', 'wb').write(pdf)
    # ##nome_os = 'os_' + ped_obj.name + '_' + ped_obj.date_order + '.pdf'

    # ##attachment_pool = self.pool.get('ir.attachment')
    # ##attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', ped_obj.id), ('name', '=', nome_os)])
    ####
    #### Apaga os boletos anteriores com o mesmo nome
    ####
    # ##attachment_pool.unlink(cr, uid, attachment_ids)

    # ##dados = {
        # ##'datas': base64.encodestring(pdf),
        # ##'name': nome_os,
        # ##'datas_fname': nome_os,
        # ##'res_model': 'sale.order',
        # ##'res_id': ped_obj.id,
        # ##'file_type': 'application/pdf',
    # ##}
    # ##attachment_pool.create(cr, uid, dados)

    # #retorno_pdf.close()

    # #return pdf
