# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import Report
from copy import deepcopy
from geraldo import FIELD_ACTION_VALUE
from reportlab.lib.units import cm

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

REL_MODELOS = (
              ('1', u'Padrão'),
              ('2', u'Personalizado'),

)


TIPO_REL_RATEIO = [
       ['PO', u'Projeto'],
       ['CC', u'Cento Custo'],

]


class finan_relatorio(osv.osv_memory):
    _name = 'finan.relatorio'
    _inherit = 'finan.relatorio'

    _columns = {
        'tipo_rel_rateio': fields.selection(TIPO_REL_RATEIO, u'Tipo Rateio'),
    }

    _defaults = {
        'tipo_rel_rateio': 'PO',
    }

    def gera_relatorio_contas_versao2(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            rel_obj.tipo = 'P'
            rel = FinanRelatorioAutomaticoPaisagem()

            rel.title = u'Contas a Pagar por Fornecedor'

            if rel_obj.situacao == '1':
                sql_situacao = u"('Vencido')"
            elif rel_obj.situacao == '2':
                sql_situacao = u"('Vencido', 'Vence hoje')"
            elif rel_obj.situacao == '3':
                sql_situacao = u"('A vencer')"
            elif rel_obj.situacao == '4':
                sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
            else:
                sql_situacao = u"('Quitado')"

            rel.colunas = [
                ['data_documento', 'D', 10, u'Data Doc.', False],
                ['unidade', 'C', 27, u'Unidade', True],
                #['banco', 'C', 38, u'Banco', False],
                ['cliente','C',35, u'Cliente' if rel_obj.tipo == 'R' else u'Fornecedor', False],
                ['numero_documento', 'C', 20, u'Nº doc.', False],
                ['valor_documento', 'F', 10, u'Valor orig.', True],
                ['valor_desconto', 'F', 10, u'Desc.', True],
                ['valor_multa', 'F', 10, u'Multa', True],
                ['valor_juros', 'F', 10, u'Juros', True],
                ['dias_atraso', 'I', 6, u'Atraso', True],
                ['valor', 'F', 10, u'Total', True],
                #['carteira_id.res_partner_bank_id.name', 'C', 10, u'Banco', False],
            ]

            rel.colunas += [
                ['provisionado', 'B', 5, u'Prov.', False],
                ['situacao', 'C', 10, u'Situação', False],
            ]

            if rel_obj.situacao == '5':
                rel.colunas += ['data_quitacao', 'D', 10, u'Data quit.', False],

            rel.colunas += ['historico', 'C', 30, u'Histórico.', False],

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                #['situacao', u'Situação', False],
                ['data_vencimento', u'Data venc..', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql_relatorio = """
                select
                   l.id,
                   coalesce(l.numero_documento, ''),
                   b.nome as banco,
                   l.data_documento,
                   l.data_vencimento,
                   l.data_quitacao,
                   coalesce(l.valor_documento, 0.00),
                   coalesce(l.valor_desconto, 0.00),
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) as valor_multa,

                   coalesce(l.valor_saldo, 0.00),
                   coalesce(p.name, '') || ' - ' || coalesce(p.cnpj_cpf, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   l.provisionado,
                   coalesce(l.historico,'') as historico

                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id
                   left join finan_conta cf on cf.id = l.conta_id

            """

            if rel_obj.situacao != '5':
                sql_relatorio += """
                    left join res_partner_bank b on b.id = l.sugestao_bank_id

                    where l.tipo = '""" + rel_obj.tipo + """'
                    and l.data_vencimento between '""" + rel_obj.data_inicial + """' and '""" + rel_obj.data_final + """'
                    and l.situacao in """ + sql_situacao
            else:
                sql_relatorio += """
                    left join res_partner_bank b on b.id = l.res_partner_bank_id

                    where l.tipo = '""" + rel_obj.tipo + """'
                    and l.data_quitacao between '""" + rel_obj.data_inicial + """' and '""" + rel_obj.data_final + """'"""

            if rel_obj.company_id:
                sql_relatorio += """
                    and (
                        c.id = """ + str(rel_obj.company_id.id) + """
                        or cc.id = """ + str(rel_obj.company_id.id) + """
                        or ccc.id = """ + str(rel_obj.company_id.id) + """
                    ) """

            if rel_obj.partner_id:
                sql_relatorio += """
                    and l.partner_id = """ + str(rel_obj.partner_id.id)


            if len(rel_obj.res_partner_bank_ids):
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)

                sql_relatorio += """
                    and b.id in """ +  str(tuple(bancos_ids)).replace(',)', ')')


            if rel_obj.ativo != rel_obj.provisionado:
                sql_relatorio += """
                    and l.provisionado = False """

            sql_relatorio += """
                    order by l.data_vencimento, c.name, l.situacao, p.name, p.cnpj_cpf ;"""

            print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for id, numero_documento, banco, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, cliente, contato, unidade, situacao, provisionado, historico  in dados:
                linha = DicionarioBrasil()
                linha['id'] = id
                linha['numero_documento'] = numero_documento
                linha['banco'] = banco
                linha['data_documento'] = formata_data(data_documento)
                linha['data_vencimento'] = formata_data(data_vencimento)
                linha['data_quitacao'] = formata_data(data_quitacao)
                linha['valor_documento'] = valor_documento
                linha['valor_desconto'] = valor_desconto
                linha['valor_juros'] = valor_juros
                linha['valor_multa'] = valor_multa

                linha['valor'] = valor
                #if data_quitacao:
                    #linha['valor'] = valor
                #else:
                    #linha['valor'] = valor_documento - valor_desconto + valor_juros + valor_multa
                linha['cliente'] = cliente + ' | ' + contato
                linha['unidade'] = unidade
                linha['situacao'] = situacao
                linha['provisionado'] = provisionado
                linha['historico'] = historico

                if situacao == 'Vencido':
                    atraso = hoje() - parse_datetime(data_vencimento).date()
                    linha['dias_atraso'] = atraso.days
                elif situacao == 'Quitado' and data_quitacao > data_vencimento:
                    atraso = parse_datetime(data_quitacao).date() - parse_datetime(data_vencimento).date()
                    linha['dias_atraso'] = atraso.days
                else:
                    linha['dias_atraso'] = 0

                linhas.append(linha)

            rel.band_page_header.elements[-1].text = u'Período ' + parse_datetime(rel_obj.data_inicial).strftime('%d/%m/%Y') + u' a ' + parse_datetime(rel_obj.data_final).strftime('%d/%m/%Y')

            if rel_obj.situacao != '5':
                rel.band_page_header.elements[-1].text += u', situação é ' + sql_situacao
            else:
                rel.band_page_header.elements[-1].text += u', situação Liquidados/Quitados'

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'contas_receber.pdf' if rel_obj.tipo == 'R' else 'contas_pagar.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'contas_receber.csv' if rel_obj.tipo == 'R' else 'contas_pagar.csv',
                'arquivo_csv': base64.encodestring(csv),
            }
            rel_obj.write(dados)

    def gera_relatorio_diario_rateio(self, cr, uid, ids, context={}, tipo='P'):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            company_id = rel_obj.company_id.id
            partner_id = rel_obj.partner_id.id
            res_partner_bank_id = rel_obj.res_partner_bank_id.id

            filtro = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'rateio': '* (coalesce(lr.porcentagem, 0) / 100.00)',
            'tipos': ''
            }

            if tipo == 'R':
                periodo = u'Diário de Clientes de ' + data_inicial.strftime('%d/%m/%Y') + ' a ' + data_final.strftime('%d/%m/%Y')
                rel = Report('Diário de Clientes', cr, uid)
                nome = periodo.lower().replace(' ', '_') + u'.' + rel_obj.formato
                rel.parametros['TIPOS'] = "('R', 'PR', 'E')"

            else:
                periodo = u'Diário de Fornecedores de ' + data_inicial.strftime('%d/%m/%Y') + ' a ' + data_final.strftime('%d/%m/%Y')
                rel = Report('Diário de Fornecedores', cr, uid)
                nome = periodo.lower().replace(' ', '_') + u'.' + rel_obj.formato
                rel.parametros['TIPOS'] = "('P', 'PP', 'S')"

            sql_relatorio = """
            select
                coalesce(e.name, '') as empresa,
                coalesce(p.cnpj_cpf, '') as cliente_cnpj_cpf,
                coalesce(p.name, '') as cliente_nome,
                cc.tipo,
                coalesce(d.nome, '') as documento,
                coalesce(lp.numero_documento, '') as numero_documento,
                lp.data_documento,
                cc.data,
                coalesce((
                    select
                        coalesce(sum(coalesce(cca.saldo_documento, 0.00)), 0.00)
                    from
                        finan_contacorrente cca
                    where
                        cca.data < '{data_inicial}'
                        and cca.partner_id = cc.partner_id
                        and cca.tipo in {tipos}
                        and cca.company_id = cc.company_id), 0.00) as saldo_anterior,
                cc.debito_documento as debito,
                cc.credito_documento as credito,
                cc.saldo_documento as saldo,
                coalesce(lp.complemento, '') as complemento,
                fcc.nome as centro_custo,
                a.name as projeto,
                ba.nome as banco
            """

            sql_relatorio += """
            from
                finan_contacorrente_rateio cc
                join res_partner p on p.id = cc.partner_id
                join finan_lancamento lp on lp.id = abs(cc.id)
                left join finan_documento d on d.id = lp.documento_id
                join res_company e on e.id = lp.company_id
                left join finan_centrocusto fcc on fcc.id = cc.centrocusto_id
                left join project_project pp on pp.id = cc.project_id
                left join account_analytic_account a on a.id = pp.analytic_account_id
                left join res_partner_bank ba on ba.id = cc.res_partner_bank_id
            """

            #if rel_obj.filtrar_rateio:
                #sql_relatorio += """
                    #join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = abs(cc.id)
                    #left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                    #left join project_project pp on pp.id = lr.project_id
                    #left join account_analytic_account a on a.id = pp.analytic_account_id
                    #left join res_partner_bank ba on ba.id = cc.res_partner_bank_id
                #"""
            #else:
                #sql_relatorio += """
                    #left join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = abs(cc.id)
                    #left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                    #left join project_project pp on pp.id = lr.project_id
                    #left join account_analytic_account a on a.id = pp.analytic_account_id
                    #left join res_partner_bank ba on ba.id = cc.res_partner_bank_id
                #"""

            sql_relatorio += """
            where
                cc.data between '{data_inicial}' and '{data_final}'
                and (cc.tipo != 'T' or upper(ba.state) = 'ADIANTAMENTO')
                and lp.situacao != 'Baixado'
                and cc.tipo in {tipos}
            """
                #and lp.tipo in {tipos}
            #"""

            if tipo == 'R':
                filtro['tipos'] = "('R', 'PR')"
            else:
                filtro['tipos'] = "('P', 'PP')"

            if rel_obj.company_id:
                company_ids = self.pool.get('res.company').search(cr, 1, ['|', ('id', '=', company_id), ('parent_id', '=', company_id)])

                sql_relatorio += """
                and e.id in """ + str(tuple(company_ids)).replace(',)', ')')

            if partner_id:
                sql_relatorio += """
                and cc.partner_id = """ +  str(partner_id)

            if res_partner_bank_id:
                sql_relatorio += """
                and cc.res_partner_bank_id = """ + str(res_partner_bank_id)

            if rel_obj.ativo != rel_obj.provisionado:
                sql_relatorio += """
                    and lp.provisionado = True """

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    sql_relatorio += """
                       and cc.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

                if rel_obj.project_id:
                    sql_relatorio += """
                       and cc.project_id = """ + str(rel_obj.project_id.id)

            sql_relatorio += """
            order by
                e.name, p.name, p.cnpj_cpf, cc.data, cc.debito desc, cc.credito desc, cc.id;
            """

            sql_relatorio = sql_relatorio.format(**filtro)

            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'construtora_diario_analitico.jrxml')
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['PERIODO'] = periodo
            rel.parametros['SQL_RELATORIO'] = sql_relatorio

            print(sql_relatorio)

            rel.outputFormat = rel_obj.formato

            pdf, formato = rel.execute()

            dados = {
                'nome': nome,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_diario_cliente_rateio(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario_rateio(cr, uid, ids, context=context, tipo='R')

    def gera_relatorio_diario_fornecedor_rateio(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario_rateio(cr, uid, ids, context=context, tipo='P')


    def gera_relatorio_contas_sintetico_jasper(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo[0],
            'rateio': '* (coalesce(lr.porcentagem, 0) / 100.00)',
        }

        if situacao == '1':
            sql_situacao = u"('Vencido')"
        elif situacao == '2':
            sql_situacao = u"('Vencido', 'Vence hoje')"
        elif situacao == '3':
            sql_situacao = u"('A vencer')"
        elif situacao == '4':
            sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
        else:
            sql_situacao = u"('Quitado','A vencer', 'Vencido', 'Vence hoje')"


        for rel_obj in self.browse(cr, uid, ids):

            if len(rel_obj.res_partner_bank_ids):
                texto_filtro = u''
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

            sql_relatorio = """
                select
                    c.name as unidade,
                    coalesce(a.name, 'Sem Projeto') as projeto,
                    coalesce(fcc.nome,'Sem Centro Custo') as centro_custo,
                    ba.nome as banco,

                    sum(coalesce(l.valor_documento, 0.00) {rateio} ) as valor_documento,
                    sum(coalesce(l.valor_desconto, 0.00) {rateio} ) as valor_desconto,
                    sum(coalesce(
                    case
                    when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                    l.valor_juros_previsto
                    else
                    l.valor_juros
                    end, 0.00) {rateio} ) as valor_juros,

                    sum(coalesce(
                    case
                    when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                    l.valor_multa_prevista
                    else
                    l.valor_multa
                    end, 0.00) {rateio} ) as valor_multa,

                    sum(coalesce(l.valor, 0.00) {rateio} ) as valor,
                    sum(coalesce(l.valor_saldo, 0.00) {rateio} ) as valor_saldo

                    from finan_lancamento l
                    join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id
                    join res_partner p on p.id = l.partner_id
                    join res_company c on c.id = l.company_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id
                    left join finan_conta cf on cf.id = l.conta_id
                    left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                    left join project_project pp on pp.id = lr.project_id
                    left join account_analytic_account a on a.id = pp.analytic_account_id
                    left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""


            if situacao != '5':
                sql_relatorio += """
                    where l.tipo = '{tipo}'
                    and l.data_vencimento between '{data_inicial}' and '{data_final}'
                    and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in ' + str(tuple(bancos_ids)).replace(',)', ')')


            else:
                sql_relatorio += """
                    where l.tipo = '{tipo}'
                    and exists(select lp.id from finan_lancamento lp where lp.lancamento_id = l.id and lp.tipo in ('PP', 'PR') and lp.data_quitacao between '{data_inicial}' and '{data_final}')"""

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in ' +  str(tuple(bancos_ids)).replace(',)', ')')

            if rel_obj.company_id:
                sql_relatorio += """
                    and (
                        c.id = {company_id}
                        or cc.id = {company_id}
                        or ccc.id = {company_id}
                    )"""

            if ativo != provisionado:
                sql_relatorio += """
                    and l.provisionado = """ + str(provisionado)

            if rel_obj.formapagamento_id:
                sql_relatorio += """
                    and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            if rel_obj.centrocusto_id:
                sql_relatorio += """
                    and lr.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

            if rel_obj.project_id:
                sql_relatorio += """
                    and lr.project_id = """ + str(rel_obj.project_id.id)

            sql_relatorio += """
                    group by
                        unidade,
                        projeto,
                        centro_custo,
                        banco"""

            if rel_obj.tipo_rel_rateio == 'PO':
                sql_relatorio += """
                    order by c.name, projeto, centro_custo, banco"""
            else:
                sql_relatorio += """
                    order by c.name,centro_custo, projeto, banco;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            if tipo == 'R-R':
                rel = Report('Relatório de Contas a Receber Sintético Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'construtora_conta_receber_sintetico_rateio.jrxml')
                nome_rel = u'contas_receber_sintetico_rateio.'


            if tipo == 'P-R':
                rel = Report('Relatório de Contas a Pagar Sintético Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'construtora_conta_pagar_sintetico_rateio.jrxml')
                nome_rel = u'contas_pagar_sintetico_rateio.'



            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['SQL_RELATORIO'] = sql_relatorio

            if rel_obj.tipo_rel_rateio == 'PO':
                rel.parametros['PROJETO'] = True

            if rel_obj.tipo_rel_rateio == 'CC':
                rel.parametros['CENTRO_CUSTO'] = True

            rel.outputFormat = rel_obj.formato

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_rel + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contas_receber_sintetico_rateio(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_sintetico_jasper(cr, uid, ids, context=context, tipo='R-R')

    def gera_relatorio_contas_pagar_sintetico_rateio(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_sintetico_jasper(cr, uid, ids, context=context, tipo='P-R')

    def movimentacao_diaria_financeira(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'rateio': '',
            }

            banco_nome = u''
            bancos_ids = []
            if len(rel_obj.res_partner_bank_ids):
                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    banco_nome += u', ' + banco_obj.nome or ''

                filtro['bank_ids'] = str(tuple(bancos_ids)).replace(',)', ')')

            if rel_obj.partner_id:
                filtro['partner_id'] = rel_obj.partner_id.id

            #sql = """
            #select
                #cast(fs.saldo_final as numeric(18,2)) as saldo_inicial,
                #fs.data as data_inicial

            #from
                #finan_saldo as fs
                #left join res_partner_bank rb on rb.id = fs.res_partner_bank_id

            #where
                #fs.data < '{data_inicial}'
                #and fs.res_partner_bank_id = {res_partner_bank_id}

            #order by
                #fs.data desc

            #limit 1
            #"""
            #sql = sql.format(res_partner_bank_id=res_partner_bank_id, data_inicial=data_inicial)
            #print(sql)
            #cr.execute(sql)
            #contrato_ids_listas = cr.fetchall()

            #saldo_anterior = D(0)
            #data_anterior = None
            #if len(contrato_ids_listas) > 0:
                #saldo_anterior = contrato_ids_listas[0][0]
                #data_anterior = contrato_ids_listas[0][1]

            #
            # Acumulamos o saldo entre o último fechamento de caixa e o início do período
            #
            sql_saldo = """
            select
                coalesce(sum(coalesce(e.valor_compensado_credito, 0) - coalesce(e.valor_compensado_debito, 0)), 0) as saldo_inicial

            from
                finan_extrato e
            where
                e.data_quitacao < '{data_inicial}'
                and e.res_partner_bank_id = {banco_id}
            """

            #if len(bancos_ids) > 0:
                #sql_saldo += """
                #and e.res_partner_bank_id in {bank_ids}
                #"""

            if rel_obj.partner_id:
                sql_saldo += """
                and e.partner_id = {partner_id}
                """

            #sql = sql.format(data_inicial=str(data_inicial))
            #cr.execute(sql)
            #dados = cr.fetchall()

            #saldo_anterior = D(0)
            #saldo_anterior_titulo = D(0)
            #if len(dados):
                #saldo_anterior = D(dados[0][0])
                #saldo_anterior_titulo = D(dados[0][0])

            sql =  """
                select
                    e.tipo as tipo,
                    e.id as numero,
                    e.data_quitacao,
                    e.data_documento,
                    b.id as banco_id,
                    b.nome as banco,
                    coalesce(c.codigo_completo, '') as codigo_conta_financeira,
                    coalesce(c.nome, '') as nome_conta_financeira,
                    coalesce(e.numero_documento, '') as numero_documento,
                    coalesce(p.name, '') as portador,
                    coalesce(p.cnpj_cpf, '') as portador_cnpj_cpf,
                    coalesce(e.valor_compensado_credito, 0) {rateio} as entrada,
                    coalesce(e.valor_compensado_debito, 0) {rateio} as saida,
                    coalesce(f.nome, '') as formapagamento,
                    case
                    when e.tipo in ('E', 'S', 'T') then coalesce(l.complemento, '')
                    else coalesce(le.complemento, '')
                    end as complemento,
                    case
                    when e.tipo in ('E', 'S', 'T') then coalesce(l.numero_documento, '')
                    else coalesce(le.numero_documento, '')
                    end as numero_cheque,
                    coalesce(d.nome, '') as documento

                from
                    finan_extrato e
                    join res_partner_bank b on b.id = e.res_partner_bank_id
                    left join res_partner p on p.id = e.partner_id
                    left join finan_conta c on c.id = e.conta_id
                    left join finan_lancamento l on l.id = e.lancamento_id
                    left join finan_formapagamento f on f.id = l.formapagamento_id
                    left join finan_lancamento le on le.id = e.id
                    left join finan_documento d on d.id = l.documento_id"""


            if rel_obj.filtrar_rateio:
                sql += """
                    left join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = e.lancamento_id
                    left join finan_conta cf on cf.id = lr.conta_id
                    left join finan_conta pfc on pfc.id = cf.parent_id
                    left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                    left join project_project pp on pp.id = lr.project_id
                    left join account_analytic_account a on a.id = pp.analytic_account_id
                    """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            sql += """
                where
                    e.data_quitacao between '{data_inicial}' and '{data_final}'
            """

            if len(bancos_ids) > 0:
                sql += """
                and e.res_partner_bank_id in {bank_ids}
                """

            if rel_obj.partner_id:
                sql += """
                and e.partner_id = {partner_id}
                """

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    filtro['centrocusto_id'] = rel_obj.centrocusto_id.id
                    sql += """
                    and fcc.id = {centrocusto_id}
                    """

                if rel_obj.project_id:
                    filtro['project_id'] = rel_obj.project_id.id
                    sql += """
                    and pp.id = {project_id}
                    """

                if rel_obj.conta_id:
                    filtro['conta_id'] = rel_obj.conta_id.id
                    sql += """
                    and (cf.id = {conta_id} or pfc.id = {conta_id})
                    """


            sql += """
                order by
                b.nome,
                e.data_quitacao,
                e.valor_compensado_credito desc,
                e.valor_compensado_debito desc;
            """

            sql = sql.format(**filtro)
            #print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []

            if not dados:
            #    raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')
                rel = FinanRelatorioAutomaticoPaisagem()
                linha = DicionarioBrasil()
                rel.title = u'Movimentação Financeira Diária'
                linha['vazio'] = u'SEM MOVIMENTO'
                rel.colunas = [
                    ['vazio', 'C', 20 , u'', False],
                ]
                linhas.append(linha)
                rel.monta_detalhe_automatico(rel.colunas)
            else:

                #saldo_atual = saldo_anterior
                banco_anterior_id = None
                for tipo, numero, data_quitacao, data_documento, banco_id, banco, codigo_conta_financeira, nome_conta_financeira, numero_documento, portador, portador_cnpj_cpf, entrada, saida, formapagamento, complemento, numero_cheque, documento  in dados:
                    if banco_id != banco_anterior_id:
                        cr.execute(sql_saldo.format(banco_id=banco_id, **filtro))
                        dados = cr.fetchall()

                        saldo_anterior = D(0)
                        if len(dados):
                            saldo_anterior = D(dados[0][0] or 0)

                        banco_anterior_id = banco_id
                        saldo_atual = saldo_anterior

                    linha = DicionarioBrasil()
                    linha['tipo'] = tipo
                    linha['numero'] = str(numero)
                    linha['data_quitacao'] = data_quitacao
                    linha['data_documento'] = data_documento
                    linha['banco_id'] = banco_id
                    linha['banco'] = banco + u'; saldo anterior R$ ' + formata_valor(saldo_anterior)
                    linha['codigo_conta_financeira'] = codigo_conta_financeira
                    linha['nome_conta_financeira'] = nome_conta_financeira
                    linha['numero_documento'] = numero_documento
                    linha['portador'] = portador
                    linha['portador_cnpj_cpf'] = portador_cnpj_cpf
                    linha['debito'] = saida
                    linha['credito'] = entrada
                    linha['formapagamento'] = formapagamento
                    linha['complemento'] = complemento
                    linha['numero_cheque'] = numero_cheque
                    linha['documento'] = documento
                    saldo_atual += entrada
                    saldo_atual -= saida
                    linha['saldo_anterior'] = saldo_anterior
                    linha['saldo'] = saldo_atual

                    linhas.append(linha)

                rel = FinanRelatorioAutomaticoPaisagem()
                rel.title = u'Movimentação Financeira Diária'

                rel.colunas = [
                    #['numero', 'C', 8,  u'Nº Doc.',False],
                    ['data_quitacao', 'D', 10, u'Data quit.', False],
                    ['numero_documento', 'C', 15, u'Nº doc.', False],
                    ['data_documento', 'D', 10, u'Data doc.', False],
                ]
                #if not res_partner_bank_id:
                #    rel.colunas += [
                #        ['banco', 'C', 40, u'Bancos', False],
                #    ]
                rel.colunas += [
                    #['codigo_conta_financeira', 'C', 10, u'Cod. Fin.', False],
                    #['nome_conta_financeira', 'C', 25, u'Conta Financeira.', False],
                    ['formapagamento', 'C', 15, u'Forma Pagto', False],
                    ['tipo', 'C', 2, u'T', False],
                    ['portador', 'C', 40, u'Portador', False],
                    ['documento', 'C', 25, u'Tipo doc.', False],
                    ['complemento', 'C', 25, u'Histórico', False],
                    #['portador_cnpj_cpf', 'C', 10, u'CNPJ', False],
                    ['numero_cheque', 'C', 7, u'CHQ.', False],
                    ['debito', 'F', 15, u'Débito', True],
                    ['credito', 'F', 15, u'Crédito', True],
                    #['saldo_anterior', 'F', 15, u'Anterior', lambda objeto, valor: unicode(formata_valor(valor))],
                    ['saldo', 'F', 15, u'Saldo', lambda objeto, valor: unicode(formata_valor(valor))],
                ]

                rel.monta_detalhe_automatico(rel.colunas)

                rel.grupos = [
                    ['banco', u'Banco', True],
                ]
                rel.monta_grupos(rel.grupos)

                rel.band_page_header.elements[-1].text =  u'DATA: ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)

                rel.band_summary.elements[0].text = u'BANCOS SELECIONADOS: ' + banco_nome
                del rel.band_summary.elements[1]
                del rel.band_summary.elements[1]
                del rel.band_summary.elements[1]

                rel.band_page_header.elements[0].style = ESTILO['CABECALHO_FILTRO']

                rel.band_summary.elements[0].width = rel.largura_maxima * cm
                rel.band_summary.borders['bottom'] = False

                rodape_grupo = rel.groups[0].band_footer
                rodape_grupo.elements[-1].action = FIELD_ACTION_VALUE

                cabecalho_grupo = rel.groups[0].band_header

                ultima_coluna = rel.band_detail.elements[-1].clone()
                ultima_coluna.attribute_name = 'saldo_anterior'
                ultima_coluna.top = cabecalho_grupo.elements[0].top

                cabecalho_grupo.elements.append(ultima_coluna)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'mov_financeira_periodo_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

            return True


finan_relatorio()
