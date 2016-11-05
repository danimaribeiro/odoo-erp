# -*- encoding: utf-8 -*-

import os
import csv
import base64
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
from gdata.health import Ccr
from pybrasil.base import DicionarioBrasil, tira_acentos
from pybrasil.inscricao import limpa_formatacao


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

def limpa_texto(texto):
    probibidos = u'.,-_;:?!=+*/&#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto

class hr_relatorio(osv.osv_memory):
    _inherit = 'hr.relatorio'
    _name = 'hr.relatorio'
    
    def gera_relatorio_sindical_versao(self, cr, uid, ids, context={}):
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
                        cbo.codigo,                        
                        co.wage as salario
                    from
                        hr_contract co
                        join hr_employee e on e.id = co.employee_id
                        join res_company c on c.id = co.company_id
                        join res_partner rp on rp.id = c.partner_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                        join hr_job f on f.id = co.job_id
                        join hr_cbo cbo on cbo.id = f.cbo_id
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
                        cbo.codigo,
                        co.wage as salario
                    from
                        hr_contract co
                        join hr_employee e on e.id = co.employee_id
                        join res_company c on c.id = co.company_id
                        join res_partner rp on rp.id = c.partner_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                        join hr_job f on f.id = co.job_id
                        join hr_cbo cbo on cbo.id = f.cbo_id
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

            for empresa, sindicato, data_inicial, nome, cpf, rg_numero, ctps, nis, tipo, rubrica, valor, cargo, cbo, salario in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = tira_acentos(empresa)
                linha['sindicato'] = tira_acentos(sindicato)
                linha['data_inicial'] = data_inicial
                linha['nome'] = tira_acentos(nome)
                linha['tipo'] = tipo
                linha['cpf'] = limpa_formatacao(cpf)
                linha['rg_numero'] = limpa_texto(rg_numero)
                linha['ctps'] = limpa_texto(ctps or '')
                linha['nis'] = limpa_texto(nis)
                linha['rubrica'] = tira_acentos(rubrica)
                linha['valor'] = valor
                linha['cargo'] = limpa_texto(cargo)
                linha['cbo'] = cbo
                linha['salario'] = salario or 0
                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Relação para Sindicatos'
            rel.colunas = [
                ['empresa' , 'C', 40, u'Empresa', False],
                ['nome' , 'C', 50, u'Nome', False],
                ['data_inicial' , 'D', 10, u'Admissão', False],
                ['tipo' , 'C', 5, u'Tipo', False],
                ['cpf' , 'C', 15, u'CPF', False],
                ['rg_numero' , 'C', 15, u'RG', False],
                ['ctps' , 'C', 15, u'CTPS', False],
                ['nis' , 'C', 15, u'PIS', False],
                ['cargo' , 'C', 25, u'Cargo', False],
                ['cbo' , 'C', 10, u'CBO', False],
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
    
    


hr_relatorio()


