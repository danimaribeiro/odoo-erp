# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, mes_passado, primeiro_dia_mes, ultimo_dia_mes, hoje, agora, formata_data
from finan.wizard.relatorio import *
from datetime import date
import csv
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from pybrasil.data.grafico_gantt import tempo_tarefa
from dateutil.relativedelta import relativedelta


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

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
    # ('13', 'décimo terceiro'),
)

MESES_DIC = dict(MESES)


FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

def primeiro_ultimo_dia_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = primeiro_dia + relativedelta(months=+1, days=-1)
    return str(primeiro_dia)[:10], str(ultimo_dia)[:10]


PERIODO_MESES = (
    ('12', '12 meses'),
    ('24', '24 meses'),
    ('36', '36 meses'),
)


class projeto_relatorio(osv.osv_memory):
    _name = 'projeto.relatorio'
    _description = u'Relatório do Projeto'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'task_id': fields.many2one('project.task', u'Tarefa'),
        'user_id': fields.many2one('res.users', u'Atribuída para'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento'),
        'project_id': fields.many2one('project.project', u'Projeto'),
        'porcentagem': fields.float(u'Porcentagem',  digits=(12,2)),
        'periodo_meses': fields.selection(PERIODO_MESES, u'Período em meses'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'projeto.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'formato': 'pdf',
        'porcentagem': 100,
        'ano': lambda *args, **kwargs: mes_passado().year,
        'mes': lambda *args, **kwargs: str(mes_passado().month).zfill(2),
        'periodo_meses': '12',
    }

    def gera_relatorio_projeto_task(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if rel_obj.task_id:
            task_id = str(rel_obj.task_id.id)
        else:
            task_id = '%'

        if rel_obj.user_id:
            user_id = str(rel_obj.user_id.id)
        else:
            user_id = '%'

        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Saldos Bancários', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_projeto_tarefa.jrxml')
        rel.parametros['PROJECT_ID'] = rel_obj.project_id.id
        rel.parametros['TASK_ID'] = str(task_id)
        rel.parametros['USER_ID'] = str(user_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'tarefas_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_projeto_orcamento(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report(u'Orçamento do Projeto', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_orcamento_projeto.jrxml')


        if rel_obj.task_id:
            task_id = str(rel_obj.task_id.id)
        else:
            task_id = '%'

        if rel_obj.orcamento_id:
            orcamento_id = str(rel_obj.orcamento_id.id)
        else:
            orcamento_id = '%'

        rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
        rel.parametros['ORCAMENTO_ID'] = orcamento_id
        rel.parametros['TASK_ID'] = task_id
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome':  u'orcamento_projeto_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_orcamento_prefeitura(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report(u'Orçamento Prefeitura', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_orcamento_prefeitura.jrxml')


        if rel_obj.task_id:
            task_id = str(rel_obj.task_id.id)
        else:
            task_id = '%'

        if rel_obj.orcamento_id:
            orcamento_id = str(rel_obj.orcamento_id.id)
        else:
            orcamento_id = '%'

        if rel_obj.porcentagem:
            porcentagem = (rel_obj.porcentagem + 100) / 100
        else:
            porcentagem = float(1)

        rel.parametros['COMPANY_ID'] = rel_obj.company_id.id
        rel.parametros['ORCAMENTO_ID'] = orcamento_id
        rel.parametros['TASK_ID'] = task_id
        rel.parametros['PORCENTAGEM'] = porcentagem
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome':  u'orcamento_prefeitura_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_cronograma_desembolso(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            orcamento_id = rel_obj.orcamento_id.id

            if rel_obj.task_id:
                task_id = rel_obj.task_id.id
            else:
                task_id = None


            if rel_obj.company_id:
                company_id = rel_obj.company_id.id
            else:
                company_id = 1
            gera = True
            mes = 0
            csvs = ''

            while gera:
                mes_01 = str(1 + mes).zfill(2)
                mes_02 = str(2 + mes).zfill(2)
                mes_03 = str(3 + mes).zfill(2)
                mes_04 = str(4 + mes).zfill(2)
                mes_05 = str(5 + mes).zfill(2)
                mes_06 = str(6 + mes).zfill(2)
                csv, valor , datas , valor_total  = self.sql_relatorio(cr, uid, company_id, orcamento_id, task_id, mes_01, mes_02, mes_03, mes_04, mes_05, mes_06)
                csvs += 'Etapa; Subetapa; Item.; Valor;'
                csvs += str(datas[0]) + ';'
                csvs += str(datas[1]) + ';'
                csvs += str(datas[2]) + ';'
                csvs += str(datas[3]) + ';'
                csvs += str(datas[4]) + ';'
                csvs += str(datas[5]) + ';\n'
                mes += 6

                csvs += csv
                csvs += ';;;;;;Valor Total;' + str(valor_total) + ';\n'[-1]
                if valor == 0:
                    gera = False

            dados = {
                'nome': u'Cronogram_desembolso.csv',
                'arquivo': base64.encodestring(csvs),
            }
            rel_obj.write(dados)

        return True

    def sql_relatorio(self, cr, uid, company_id, orcamento_id, task_id, mes_01, mes_02, mes_03, mes_04, mes_05, mes_06):
        sql = """
            select
            rp.name as empresa,
            a.name as projeto,
            pe.nome_completo as etapa,
            coalesce(ep.nome_completo,'') as etapa_pai,
            '[' || coalesce(pd.default_code,'') || ']' || coalesce(pd.name_template,'') as produto,
            coalesce(pi.vr_produto,0) vr_produto,


            pm.mes_{mes_01} as data01,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_01} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_01}
            group by
            poc.data_vencimento ),0) as valor_01,

            pm.mes_{mes_02} as data_02,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_02} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_02}

            group by
            poc.data_vencimento),0) as valor_02,

             pm.mes_{mes_03} as data_03,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_03} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_03}
            group by
            poc.data_vencimento),0) as valor_03,

            pm.mes_{mes_04} as data_04,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_04} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_04}
            group by
            poc.data_vencimento),0) as valor_04,

            pm.mes_{mes_05} as data_05,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_05} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_05}
            group by
            poc.data_vencimento),0) as valor_05,

            pm.mes_{mes_06} as data_12,

            coalesce((select
              case
              when to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_06} then
                sum(poc.valor)
              else 0
              end as valor
            from project_orcamento_item_planejamento_parcela poc
            where
            poc.planejamento_id = ip.id
            and to_char(poc.data_vencimento, 'YYYY-MM') = pm.mes_{mes_06}
            group by
            poc.data_vencimento ), 0) as valor_06


            from project_orcamento po
            join project_orcamento_item pi on pi.orcamento_id = po.id
            join project_orcamento_etapa pe on pe.id = pi.etapa_id
            join project_orcamento_item_planejamento ip on ip.item_id = pi.id
            left join project_orcamento_etapa ep on ep.id = pe.parent_id
            join project_orcamento_meses_desembolso_colunas pm on pm.orcamento_id = po.id
            join product_product pd on pd.id = pi.product_id
            join product_template pt on pt.id = pd.product_tmpl_id
            left join project_project pp on pp.id = po.project_id
            left join account_analytic_account a on a.id = pp.analytic_account_id

            left join res_company c on c.id = pp.company_id
            left join res_partner rp on rp.id = c.partner_id

            where
            po.id = {orcamento}
            """
        if task_id:
            sql += """
                and pe.id =  """ + str(task_id)

        sql += """
               order by
               rp.name, ep.codigo_completo, pe.codigo_completo
               ;"""


        sql = sql.format(orcamento=str(orcamento_id), mes_01=mes_01, mes_02=mes_02, mes_03=mes_03, mes_04=mes_04, mes_05=mes_05, mes_06=mes_06)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        valor = 0
        valor_total = 0
        for empresa, projeto, etapa, etapa_pai , produto, vr_produto, data_01, valor_01, data_02, valor_02,  data_03, valor_03,  data_04, valor_04, data_05, valor_05, data_06, valor_06 in dados:
            linha = DicionarioBrasil()
            linha['empresa'] = empresa
            linha['projeto'] = projeto
            linha['etapa_pai'] = etapa_pai
            linha['etapa'] = etapa
            linha['produto'] = produto
            linha['vr_produto'] = vr_produto
            linha['data_01'] = data_01
            linha['valor_01'] = valor_01
            linha['data_02'] = data_02
            linha['valor_02'] = valor_02
            linha['data_03'] = data_03
            linha['valor_03'] = valor_03
            linha['data_04'] = data_04
            linha['valor_04'] = valor_04
            linha['data_05'] = data_05
            linha['valor_05'] = valor_05
            linha['data_06'] = data_06
            linha['valor_06'] = valor_06
            valor_total += valor_01 + valor_02 + valor_03 + valor_04 + valor_05 + valor_06
            valor +=  valor_06
            linhas.append(linha)


        rel = RHRelatorioAutomaticoRetrato()
        rel.title = u'Clientes por Estado'
        rel.colunas = [
            ['etapa_pai' , 'C', 40, u'Etapa', False],
            ['etapa','C', 40, u'Subetapa', False],
            ['produto' , 'C', 40, u'Item', False],
            ['vr_produto', 'F', 15, u'Valor', False],
            ['valor_01' , 'F', 15, str(data_01), False],
            ['valor_02' , 'F', 15, str(data_02), False],
            ['valor_03' , 'F', 15, str(data_03), False],
            ['valor_04' , 'F', 15, str(data_04), False],
            ['valor_05' , 'F', 15, str(data_05), False],
            ['valor_06' , 'F', 15, str(data_06), False],
        ]
        datas = (
                 str(data_01),
                 str(data_02),
                 str(data_03),
                 str(data_04),
                 str(data_05),
                 str(data_06),
        )

        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['projeto', u'Projeto', False],
        ]

        rel.monta_grupos(rel.grupos)


        if company_id:
            company_id = company_id
        else:
            company_id = 1

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        rel.band_page_header.elements[-1].text = u'Empresa: ' + company_obj.partner_id.name

        csv = gera_relatorio_csv(rel, linhas)

        return csv, valor , datas , valor_total

    def gera_relatorio_fisico_gantt(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            orcamento_id = rel_obj.orcamento_id.id

            if rel_obj.task_id:
                task_id = rel_obj.task_id.id
            else:
                task_id = None


            if rel_obj.company_id:
                company_id = rel_obj.company_id.id
            else:
                company_id = 1
            gera = True
            mes = 0
            csvs = u''

            while gera:
                mes_01 = unicode(1 + mes).zfill(2)
                mes_02 = unicode(2 + mes).zfill(2)
                mes_03 = unicode(3 + mes).zfill(2)
                mes_04 = unicode(4 + mes).zfill(2)
                mes_05 = unicode(5 + mes).zfill(2)
                mes_06 = unicode(6 + mes).zfill(2)
                csv, rel_maior , datas  = self.sql_relatorio_gantt(cr, uid, company_id, orcamento_id, task_id, mes_01, mes_02, mes_03, mes_04, mes_05, mes_06)

                csvs += u'Etapa; Subetapa; Produto; Inicio; Termino;'
                csvs += unicode(datas[0]) + u';'
                csvs += unicode(datas[1]) + u';'
                csvs += unicode(datas[2]) + u';'
                csvs += unicode(datas[3]) + u';'
                csvs += unicode(datas[4]) + u';'
                csvs += unicode(datas[5]) + u';\n'
                mes += 6
                csvs += csv.decode('iso-8859-1')

                if rel_maior == False:
                    gera = False

            csvs = csvs.encode('utf-8')

            dados = {
                'nome': u'Cronograma_fisico_gantt.csv',
                'arquivo': base64.encodestring(csvs),
            }
            rel_obj.write(dados)

        return True

    def sql_relatorio_gantt(self, cr, uid, company_id, orcamento_id, task_id, mes_01, mes_02, mes_03, mes_04, mes_05, mes_06):
        sql = """
            select
            rp.name as empresa,
            a.name as projeto,
            pe.nome_completo as etapa,
            coalesce(ep.nome_completo,'') as etapa_pai,
            '[' || coalesce(pd.default_code,'') || ']' || coalesce(pd.name_template,'') as produto,

            ip.data_inicial_execucao as data_inicial,

            ip.data_final_execucao as data_final,

            coalesce(pm.mes_{mes_01},'') as data01,

            coalesce(pm.mes_{mes_02},'') as data_02,

            coalesce(pm.mes_{mes_03},'') as data_03,

            coalesce(pm.mes_{mes_04},'') as data_04,

            coalesce(pm.mes_{mes_05},'') as data_05,

            coalesce(pm.mes_{mes_06},'') as data_06


            from project_orcamento po
            join project_orcamento_item pi on pi.orcamento_id = po.id
            join project_orcamento_etapa pe on pe.id = pi.etapa_id
            join project_orcamento_item_planejamento ip on ip.item_id = pi.id
            left join project_orcamento_etapa ep on ep.id = pe.parent_id
            join project_orcamento_meses_planejamento_colunas pm on pm.orcamento_id = po.id
            join product_product pd on pd.id = pi.product_id
            join product_template pt on pt.id = pd.product_tmpl_id
            left join project_project pp on pp.id = po.project_id
            left join account_analytic_account a on a.id = pp.analytic_account_id

            left join res_company c on c.id = pp.company_id
            left join res_partner rp on rp.id = c.partner_id

            where
            po.id = {orcamento}
            and ip.data_inicial_execucao is not null or false
            and ip.data_final_execucao is not null or false

            """
        if task_id:
            sql += """
                and pe.id =  """ + str(task_id)

        sql += """
               order by
               rp.name, ep.codigo_completo, pe.codigo_completo
               ;"""


        sql = sql.format(orcamento=str(orcamento_id), mes_01=mes_01, mes_02=mes_02, mes_03=mes_03, mes_04=mes_04, mes_05=mes_05, mes_06=mes_06)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []

        rel_maior = False
        for empresa, projeto, etapa, etapa_pai , produto, data_inicial, data_final, data_01, data_02, data_03, data_04, data_05, data_06, in dados:
            linha = DicionarioBrasil()
            linha['empresa'] = empresa
            linha['projeto'] = projeto
            linha['etapa_pai'] = etapa_pai
            linha['etapa'] = etapa
            linha['produto'] = produto

            data_inicial = formata_data(data_inicial)
            data_final = formata_data(data_final)
            linha['data_inicial'] = data_inicial
            linha['data_final'] = data_final

            linha['data_01'] = data_01

            if data_01:
                data_inicial_01, data_final_01 = primeiro_ultimo_dia_mes(int(data_01[:4]), int(data_01[5:]))
                linha['texto_01'] = tempo_tarefa(formata_data(data_inicial_01),formata_data(data_final_01),data_inicial,data_final)
            else:
                linha['texto_01'] = ''

            linha['data_02'] = data_02

            if data_02:
                data_inicial_02, data_final_02 = primeiro_ultimo_dia_mes(int(data_02[:4]), int(data_02[5:]))
                linha['texto_02'] = tempo_tarefa(formata_data(data_inicial_02),formata_data(data_final_02),data_inicial,data_final)
            else:
                linha['texto_02'] = ''

            linha['data_03'] = data_03

            if data_03:
                data_inicial_03, data_final_03 = primeiro_ultimo_dia_mes(int(data_03[:4]), int(data_03[5:]))
                linha['texto_03'] = tempo_tarefa(formata_data(data_inicial_03),formata_data(data_final_03),data_inicial,data_final)
            else:
                linha['texto_03'] = ''

            linha['data_04'] = data_04

            if data_04:
                data_inicial_04, data_final_04 = primeiro_ultimo_dia_mes(int(data_04[:4]), int(data_04[5:]))
                linha['texto_04'] = tempo_tarefa(formata_data(data_inicial_04),formata_data(data_final_04),data_inicial,data_final)
            else:
                linha['texto_04'] = ''

            linha['data_05'] = data_05

            if data_05:
                data_inicial_05, data_final_05 = primeiro_ultimo_dia_mes(int(data_05[:4]), int(data_05[5:]))
                linha['texto_05'] = tempo_tarefa(formata_data(data_inicial_05),formata_data(data_final_05),data_inicial,data_final)
            else:
                linha['texto_05'] = ''

            linha['data_06'] = data_06

            if data_06:
                data_inicial_06, data_final_06 = primeiro_ultimo_dia_mes(int(data_06[:4]), int(data_06[5:]))
                linha['texto_06'] = tempo_tarefa(formata_data(data_inicial_06),formata_data(data_final_06),data_inicial,data_final)
                if data_final > data_final_06:
                    rel_maior = True
            else:
                linha['texto_06'] = ''

            linhas.append(linha)


        rel = RHRelatorioAutomaticoRetrato()
        rel.title = u'Clientes por Estado'
        rel.colunas = [
            ['etapa_pai' , 'C', 40, u'Etapa', False],
            ['etapa','C', 40, u'Subetapa', False],
            ['produto' , 'C', 40, u'Item', False],
            ['data_inicial', 'D', 10, u'Inicio', False],
            ['data_final', 'D', 10, u'Término', False],
            ['texto_01' , 'C', 15, str(data_01), False],
            ['texto_02' , 'C', 15, str(data_02), False],
            ['texto_03' , 'C', 15, str(data_03), False],
            ['texto_04' , 'C', 15, str(data_04), False],
            ['texto_05' , 'C', 15, str(data_05), False],
            ['texto_06' , 'C', 15, str(data_06), False],
        ]
        datas = (
                 str(data_01),
                 str(data_02),
                 str(data_03),
                 str(data_04),
                 str(data_05),
                 str(data_06),
        )

        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['projeto', u'Projeto', False],
        ]

        rel.monta_grupos(rel.grupos)


        if company_id:
            company_id = company_id
        else:
            company_id = 1

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        rel.band_page_header.elements[-1].text = u'Empresa: ' + company_obj.partner_id.name

        csv = gera_relatorio_csv(rel, linhas)

        return csv, rel_maior , datas

    def gera_relatorio_projeto_orcamento_compras(self, cr, uid, ids, context={}):
        SQL_COLUNAS = u"""
    ,
    '{titulo}' as titulo_{coluna},
    case
        when tipo = 'E' then 0
        else coalesce((
            select
                sum(coalesce(poc.quantidade_realizada, 0))
            from
                project_orcamento_compras poc
                join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
            where
                poc.orcamento_id = po.orcamento_id
                and to_char(poc.data, 'YYYY-MM') = '{mes}'
                    and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
                and (po.tipo = 'I' or poa.codigo like po.codigo ||  '%')
        ), 0)
    end as quantidade_{coluna},
    coalesce((
        select
            sum(coalesce(poc.vr_produto_realizado, 0))
        from
            project_orcamento_compras poc
            join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
        where
            poc.orcamento_id = po.orcamento_id
            and to_char(poc.data, 'YYYY-MM') = '{mes}'
            and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
            and (po.tipo = 'I' or (po.tipo = 'E' and poa.codigo like po.codigo ||  '%'))
    ), 0) as vr_produto_{coluna}
        """

        SQL_COLUNAS_TOTAL = u"""
    ,
    '{titulo}' as titulo_{coluna},
    case
        when tipo = 'E' then 0
        else coalesce((
            select
                sum(coalesce(poc.quantidade_realizada, 0))
            from
                project_orcamento_compras poc
                join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
            where
                poc.orcamento_id = po.orcamento_id
                and to_char(poc.data, 'YYYY-MM') between '{mes_inicial}' and '{mes_final}'
                    and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
                and (po.tipo = 'I' or poa.codigo like po.codigo ||  '%')
        ), 0)
    end as quantidade_{coluna},
    coalesce((
        select
            sum(coalesce(poc.vr_produto_realizado, 0))
        from
            project_orcamento_compras poc
            join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
        where
            poc.orcamento_id = po.orcamento_id
            and to_char(poc.data, 'YYYY-MM') between '{mes_inicial}' and '{mes_final}'
            and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
            and (po.tipo = 'I' or (po.tipo = 'E' and poa.codigo like po.codigo ||  '%'))
    ), 0) as vr_produto_{coluna}
        """

        SQL_COLUNAS_DIFERENCA = u"""
    ,
    '{titulo}' as titulo_{coluna},
    case
        when tipo = 'E' then 0
        else po.quantidade - coalesce((
            select
                sum(coalesce(poc.quantidade_realizada, 0))
            from
                project_orcamento_compras poc
                join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
            where
                poc.orcamento_id = po.orcamento_id
                and to_char(poc.data, 'YYYY-MM') between '{mes_inicial}' and '{mes_final}'
                    and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
                and (po.tipo = 'I' or poa.codigo like po.codigo ||  '%')
        ), 0)
    end as quantidade_{coluna},
    po.vr_produto - coalesce((
        select
            sum(coalesce(poc.vr_produto_realizado, 0))
        from
            project_orcamento_compras poc
            join project_orcamento_arvore poa on poa.orcamento_item_id = poc.orcamento_item_id
        where
            poc.orcamento_id = po.orcamento_id
            and to_char(poc.data, 'YYYY-MM') between '{mes_inicial}' and '{mes_final}'
            and (po.tipo = 'E' or (po.tipo = 'I' and poc.orcamento_item_id = po.orcamento_item_id))
            and (po.tipo = 'I' or (po.tipo = 'E' and poa.codigo like po.codigo ||  '%'))
    ), 0) as vr_produto_{coluna}
        """

        SQL_RELATORIO = u"""
select
    po.projeto,
    po.orcamento,
    po.codigo,
    po.descricao,
    po.tipo,
    po.orcamento_id,
    po.orcamento_item_id,
    po.quantidade,
    po.vr_produto
    {colunas}

from
    project_orcamento_arvore po

where
    po.orcamento_id = {orcamento_id}

order by
    po.codigo;
        """

        rel_obj = self.browse(cr, uid, ids[0])
        colunas = u''

        mes_inicial = None
        mes_final = None
        periodo_meses = int(rel_obj.periodo_meses)
        for i in range(36):
            data = parse_datetime(str(rel_obj.ano).zfill(4) + '-' + rel_obj.mes + '-01').date()
            data = data + relativedelta(months=i)
            filtro = {
                'coluna': str(i + 1).zfill(2),
                'titulo': formata_data(data, '%B-%Y'),
                'mes': formata_data(data, '%Y-%m'),
            }
            colunas += SQL_COLUNAS.format(**filtro)

            if mes_inicial is None:
                mes_inicial = formata_data(data, '%Y-%m')

            if mes_final is None:
                if periodo_meses > 1:
                    periodo_meses -= 1
                else:
                    mes_final = formata_data(data, '%Y-%m')

        filtro = {
            'titulo': 'Total',
            'coluna': 'total',
            'mes_inicial': mes_inicial,
            'mes_final': mes_final,
        }
        colunas += SQL_COLUNAS_TOTAL.format(**filtro)

        filtro = {
            'titulo': u'Diferença',
            'coluna': 'diferenca',
            'mes_inicial': mes_inicial,
            'mes_final': mes_final,
        }
        colunas += SQL_COLUNAS_DIFERENCA.format(**filtro)

        filtro = {
            'orcamento_id': rel_obj.orcamento_id.id,
            'colunas': colunas,
        }

        sql = SQL_RELATORIO.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        valor = 0
        valor_total = 0
        for (projeto,orcamento,codigo,descricao,tipo,orcamento_id,orcamento_item_id,quantidade,vr_produto,
            titulo_01,quantidade_01,vr_produto_01,
            titulo_02,quantidade_02,vr_produto_02,
            titulo_03,quantidade_03,vr_produto_03,
            titulo_04,quantidade_04,vr_produto_04,
            titulo_05,quantidade_05,vr_produto_05,
            titulo_06,quantidade_06,vr_produto_06,
            titulo_07,quantidade_07,vr_produto_07,
            titulo_08,quantidade_08,vr_produto_08,
            titulo_09,quantidade_09,vr_produto_09,
            titulo_10,quantidade_10,vr_produto_10,
            titulo_11,quantidade_11,vr_produto_11,
            titulo_12,quantidade_12,vr_produto_12,
            titulo_13,quantidade_13,vr_produto_13,
            titulo_14,quantidade_14,vr_produto_14,
            titulo_15,quantidade_15,vr_produto_15,
            titulo_16,quantidade_16,vr_produto_16,
            titulo_17,quantidade_17,vr_produto_17,
            titulo_18,quantidade_18,vr_produto_18,
            titulo_19,quantidade_19,vr_produto_19,
            titulo_20,quantidade_20,vr_produto_20,
            titulo_21,quantidade_21,vr_produto_21,
            titulo_22,quantidade_22,vr_produto_22,
            titulo_23,quantidade_23,vr_produto_23,
            titulo_24,quantidade_24,vr_produto_24,
            titulo_25,quantidade_25,vr_produto_25,
            titulo_26,quantidade_26,vr_produto_26,
            titulo_27,quantidade_27,vr_produto_27,
            titulo_28,quantidade_28,vr_produto_28,
            titulo_29,quantidade_29,vr_produto_29,
            titulo_30,quantidade_30,vr_produto_30,
            titulo_31,quantidade_31,vr_produto_31,
            titulo_32,quantidade_32,vr_produto_32,
            titulo_33,quantidade_33,vr_produto_33,
            titulo_34,quantidade_34,vr_produto_34,
            titulo_35,quantidade_35,vr_produto_35,
            titulo_36,quantidade_36,vr_produto_36,
            titulo_total,quantidade_total,vr_produto_total,
            titulo_diferenca,quantidade_diferenca,vr_produto_diferenca,
            ) in dados:

            linha = DicionarioBrasil()
            #linha['projeto'] = projeto
            linha['orcamento'] = rel_obj.orcamento_id.descricao
            linha['codigo'] = codigo
            linha['descricao'] = descricao
            linha['tipo'] = tipo
            #linha['orcamento_id'] = orcamento_id
            #linha['orcamento_item_id'] = orcamento_item_id
            linha['quantidade'] = formata_valor(D(quantidade or 0))
            linha['vr_produto'] = formata_valor(D(vr_produto or 0))

            linha['titulo_01'], linha['quantidade_01'], linha['vr_produto_01'] = titulo_01.decode('utf-8'), formata_valor(D(quantidade_01 or 0)), formata_valor(D(vr_produto_01 or 0))
            linha['titulo_02'], linha['quantidade_02'], linha['vr_produto_02'] = titulo_02.decode('utf-8'), formata_valor(D(quantidade_02 or 0)), formata_valor(D(vr_produto_02 or 0))
            linha['titulo_03'], linha['quantidade_03'], linha['vr_produto_03'] = titulo_03.decode('utf-8'), formata_valor(D(quantidade_03 or 0)), formata_valor(D(vr_produto_03 or 0))
            linha['titulo_04'], linha['quantidade_04'], linha['vr_produto_04'] = titulo_04.decode('utf-8'), formata_valor(D(quantidade_04 or 0)), formata_valor(D(vr_produto_04 or 0))
            linha['titulo_05'], linha['quantidade_05'], linha['vr_produto_05'] = titulo_05.decode('utf-8'), formata_valor(D(quantidade_05 or 0)), formata_valor(D(vr_produto_05 or 0))
            linha['titulo_06'], linha['quantidade_06'], linha['vr_produto_06'] = titulo_06.decode('utf-8'), formata_valor(D(quantidade_06 or 0)), formata_valor(D(vr_produto_06 or 0))
            linha['titulo_07'], linha['quantidade_07'], linha['vr_produto_07'] = titulo_07.decode('utf-8'), formata_valor(D(quantidade_07 or 0)), formata_valor(D(vr_produto_07 or 0))
            linha['titulo_08'], linha['quantidade_08'], linha['vr_produto_08'] = titulo_08.decode('utf-8'), formata_valor(D(quantidade_08 or 0)), formata_valor(D(vr_produto_08 or 0))
            linha['titulo_09'], linha['quantidade_09'], linha['vr_produto_09'] = titulo_09.decode('utf-8'), formata_valor(D(quantidade_09 or 0)), formata_valor(D(vr_produto_09 or 0))
            linha['titulo_10'], linha['quantidade_10'], linha['vr_produto_10'] = titulo_10.decode('utf-8'), formata_valor(D(quantidade_10 or 0)), formata_valor(D(vr_produto_10 or 0))
            linha['titulo_11'], linha['quantidade_11'], linha['vr_produto_11'] = titulo_11.decode('utf-8'), formata_valor(D(quantidade_11 or 0)), formata_valor(D(vr_produto_11 or 0))
            linha['titulo_12'], linha['quantidade_12'], linha['vr_produto_12'] = titulo_12.decode('utf-8'), formata_valor(D(quantidade_12 or 0)), formata_valor(D(vr_produto_12 or 0))
            linha['titulo_13'], linha['quantidade_13'], linha['vr_produto_13'] = titulo_13.decode('utf-8'), formata_valor(D(quantidade_13 or 0)), formata_valor(D(vr_produto_13 or 0))
            linha['titulo_14'], linha['quantidade_14'], linha['vr_produto_14'] = titulo_14.decode('utf-8'), formata_valor(D(quantidade_14 or 0)), formata_valor(D(vr_produto_14 or 0))
            linha['titulo_15'], linha['quantidade_15'], linha['vr_produto_15'] = titulo_15.decode('utf-8'), formata_valor(D(quantidade_15 or 0)), formata_valor(D(vr_produto_15 or 0))
            linha['titulo_16'], linha['quantidade_16'], linha['vr_produto_16'] = titulo_16.decode('utf-8'), formata_valor(D(quantidade_16 or 0)), formata_valor(D(vr_produto_16 or 0))
            linha['titulo_17'], linha['quantidade_17'], linha['vr_produto_17'] = titulo_17.decode('utf-8'), formata_valor(D(quantidade_17 or 0)), formata_valor(D(vr_produto_17 or 0))
            linha['titulo_18'], linha['quantidade_18'], linha['vr_produto_18'] = titulo_18.decode('utf-8'), formata_valor(D(quantidade_18 or 0)), formata_valor(D(vr_produto_18 or 0))
            linha['titulo_19'], linha['quantidade_19'], linha['vr_produto_19'] = titulo_19.decode('utf-8'), formata_valor(D(quantidade_19 or 0)), formata_valor(D(vr_produto_19 or 0))
            linha['titulo_20'], linha['quantidade_20'], linha['vr_produto_20'] = titulo_20.decode('utf-8'), formata_valor(D(quantidade_20 or 0)), formata_valor(D(vr_produto_20 or 0))
            linha['titulo_21'], linha['quantidade_21'], linha['vr_produto_21'] = titulo_21.decode('utf-8'), formata_valor(D(quantidade_21 or 0)), formata_valor(D(vr_produto_21 or 0))
            linha['titulo_22'], linha['quantidade_22'], linha['vr_produto_22'] = titulo_22.decode('utf-8'), formata_valor(D(quantidade_22 or 0)), formata_valor(D(vr_produto_22 or 0))
            linha['titulo_23'], linha['quantidade_23'], linha['vr_produto_23'] = titulo_23.decode('utf-8'), formata_valor(D(quantidade_23 or 0)), formata_valor(D(vr_produto_23 or 0))
            linha['titulo_24'], linha['quantidade_24'], linha['vr_produto_24'] = titulo_24.decode('utf-8'), formata_valor(D(quantidade_24 or 0)), formata_valor(D(vr_produto_24 or 0))
            linha['titulo_25'], linha['quantidade_25'], linha['vr_produto_25'] = titulo_25.decode('utf-8'), formata_valor(D(quantidade_25 or 0)), formata_valor(D(vr_produto_25 or 0))
            linha['titulo_26'], linha['quantidade_26'], linha['vr_produto_26'] = titulo_26.decode('utf-8'), formata_valor(D(quantidade_26 or 0)), formata_valor(D(vr_produto_26 or 0))
            linha['titulo_27'], linha['quantidade_27'], linha['vr_produto_27'] = titulo_27.decode('utf-8'), formata_valor(D(quantidade_27 or 0)), formata_valor(D(vr_produto_27 or 0))
            linha['titulo_28'], linha['quantidade_28'], linha['vr_produto_28'] = titulo_28.decode('utf-8'), formata_valor(D(quantidade_28 or 0)), formata_valor(D(vr_produto_28 or 0))
            linha['titulo_29'], linha['quantidade_29'], linha['vr_produto_29'] = titulo_29.decode('utf-8'), formata_valor(D(quantidade_29 or 0)), formata_valor(D(vr_produto_29 or 0))
            linha['titulo_30'], linha['quantidade_30'], linha['vr_produto_30'] = titulo_30.decode('utf-8'), formata_valor(D(quantidade_30 or 0)), formata_valor(D(vr_produto_30 or 0))
            linha['titulo_31'], linha['quantidade_31'], linha['vr_produto_31'] = titulo_31.decode('utf-8'), formata_valor(D(quantidade_31 or 0)), formata_valor(D(vr_produto_31 or 0))
            linha['titulo_32'], linha['quantidade_32'], linha['vr_produto_32'] = titulo_32.decode('utf-8'), formata_valor(D(quantidade_32 or 0)), formata_valor(D(vr_produto_32 or 0))
            linha['titulo_33'], linha['quantidade_33'], linha['vr_produto_33'] = titulo_33.decode('utf-8'), formata_valor(D(quantidade_33 or 0)), formata_valor(D(vr_produto_33 or 0))
            linha['titulo_34'], linha['quantidade_34'], linha['vr_produto_34'] = titulo_34.decode('utf-8'), formata_valor(D(quantidade_34 or 0)), formata_valor(D(vr_produto_34 or 0))
            linha['titulo_35'], linha['quantidade_35'], linha['vr_produto_35'] = titulo_35.decode('utf-8'), formata_valor(D(quantidade_35 or 0)), formata_valor(D(vr_produto_35 or 0))
            linha['titulo_36'], linha['quantidade_36'], linha['vr_produto_36'] = titulo_36.decode('utf-8'), formata_valor(D(quantidade_36 or 0)), formata_valor(D(vr_produto_36 or 0))
            linha['titulo_total'], linha['quantidade_total'], linha['vr_produto_total'] = titulo_total.decode('utf-8'), formata_valor(D(quantidade_total or 0)), formata_valor(D(vr_produto_total or 0))
            linha['titulo_diferenca'], linha['quantidade_diferenca'], linha['vr_produto_diferenca'] = titulo_diferenca.decode('utf-8'), formata_valor(D(quantidade_diferenca or 0)), formata_valor(D(vr_produto_diferenca or 0))

            linhas.append(linha)


        ###rel = FinanRelatorioAutomaticoPaisagem()
        ###rel.title = u'Orçado x Realizado (compras)'
        ###rel.colunas = [
            ###['orcamento' , 'C', 60, u'Orçamento', False],
            ###['codigo'    , 'C', 20, u'Código', False],
            ###['descricao' , 'C', 60, u'Descrição', False],
            ###['quantidade', 'F', 15, u'Qtd. orçada', False],
            ###['vr_produto', 'F', 15, u'Valor orçado', False],
        ###]

        ###linha_titulo = u'Orçamento;Código;Descrição;Qtd. orçada;Valor orçado'

        ###for i in range(12):
            ###rel.colunas.append(['quantidade_' + str(i + 1).zfill(2), 'F', 15, u'Qtd. ' + linha['titulo_' + str(i + 1).zfill(2)], False])
            ###rel.colunas.append(['vr_produto_' + str(i + 1).zfill(2), 'F', 15, u'Vr. ' + linha['titulo_' + str(i + 1).zfill(2)], False])

            ###linha_titulo += u';Qtd. ' + linha['titulo_' + str(i + 1).zfill(2)]
            ###linha_titulo += u';Vr. ' + linha['titulo_' + str(i + 1).zfill(2)]

        ###rel.monta_detalhe_automatico(rel.colunas)

        ####rel.grupos = [
            ####['projeto', u'Projeto', False],
        ####]

        ####rel.monta_grupos(rel.grupos)

        ###rel.band_page_header.elements[-1].text = u'Orçamento: ' + rel_obj.orcamento_id.descricao

        ####pdf = gera_relatorio(rel, linhas)
        ###csv = gera_relatorio_csv(rel, linhas)
        ###csv = linha_titulo.encode('iso-8859-1') + '\n\r' + csv

        dados = {
            'titulo': u'Orçado × Realizado (compras)',
            'orcamento': rel_obj.orcamento_id,
            'linha_titulo': linhas[0],
            'linhas': linhas,
            'hoje': formata_data(hoje(), '%d/%m/%Y'),
            'agora': formata_data(agora(), '%d/%m/%Y %H:%M:%S'),
        }

        if rel_obj.periodo_meses == '12':
            nome_arquivo = JASPER_BASE_DIR + 'project_orcamento_orcado_realizado.ods'
        elif rel_obj.periodo_meses == '24':
            nome_arquivo = JASPER_BASE_DIR + 'project_orcamento_orcado_realizado_24.ods'
        elif rel_obj.periodo_meses == '36':
            nome_arquivo = JASPER_BASE_DIR + 'project_orcamento_orcado_realizado_36.ods'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados, formato='xlsx')

        dados = {
            'nome': 'orcado_realizado_compras.xlsx',
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True


projeto_relatorio()
