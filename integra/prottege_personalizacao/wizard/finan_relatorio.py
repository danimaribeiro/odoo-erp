# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from collections import OrderedDict

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {
        'nao_provisionado': fields.boolean(u'Não provisionado'),
    }
    
    _defaults = {
        'provisionado': False,
        'nao_provisionado': True,
        'company_id': False,     
    }
    
    def gera_relatorio_contas(self, cr, uid, ids, context={}, tipo='R'):
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
            'rateio': '',
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
            sql_situacao = u"('Quitado', 'Conciliado')"


        for rel_obj in self.browse(cr, uid, ids):
            rel = FinanRelatorioAutomaticoPaisagem()

            if tipo == 'R':
                rel.title = u'Contas a Receber por Cliente'
            else:
                rel.title = u'Contas a Pagar por Fornecedor'

            rel.colunas = [                
                ['cliente', 'C', 50,  u'Cliente' if tipo == 'R' else u'Fornecedor', False],
                ['conta_codigo', 'C', 10, u'Cod.Conta', False],
                ['conta_nome', 'C', 25, u'Conta', False],
            ]

            if tipo == 'P-R':
                rel.colunas += [
                    ['projeto', 'C', 30, u'Projeto', False],
                    ['centro_custo', 'C', 30, u'Centro Custo', False],
                    ['banco', 'C', 30, u'Conta Bancária', False],
            ]

            rel.colunas += [
                ['numero_documento', 'C', 20, u'Nº doc.', False],
                ['data_documento', 'D', 10, u'Data doc.', False],
                ['data_vencimento', 'D', 10, u'Data venc.', False],
                #['carteira_id.res_partner_bank_id.name', 'C', 10, u'Banco', False],
            ]

            if tipo == 'R':
                rel.colunas += [['nosso_numero', 'C', 10, u'Nosso nº', False]]


            rel.colunas += [
                #['provisionado', 'B', 5, u'Prov.', False],
                ['valor_documento', 'F', 10, u'Valor orig.', True],
                ['valor_desconto', 'F', 10, u'Desc.', True],
                ['valor_multa', 'F', 10, u'Multa', True],
                ['valor_juros', 'F', 10, u'Juros', True],
                ['valor', 'F', 10, u'Total', True],
                ['valor_saldo', 'F', 10, u'Parc.', True],
                ['dias_atraso', 'I', 6, u'Atraso', True],
                #['situacao', 'C', 10, u'Situação', False],
            ]

            if situacao == '5':
                rel.colunas += ['data_quitacao', 'D', 10, u'Data quit.', False],

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['unidade', u'Unidade', True],
                ['situacao', u'Situação', False],
                #['cliente', u'Cliente' if tipo == 'R' else u'Fornecedor', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(l.valor_documento, 0.00) {rateio} as valor_documento,
                   coalesce(l.valor_desconto, 0.00) {rateio} as valor_desconto,
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) {rateio} as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) {rateio} as valor_multa,

                   coalesce(l.valor, 0.00) {rateio} as valor,
                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.name, '') || ' - ' || coalesce(p.cnpj_cpf, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   coalesce(cf.nome, '') as conta_nome,
                   l.provisionado"""

            if tipo == 'P-R':
                sql_relatorio += """,
                   fcc.nome as centro_custo,
                   a.name as projeto,
                   ba.nome as banco
                """

            sql_relatorio += """
                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id
                   left join finan_conta cf on cf.id = l.conta_id """

            if rel_obj.filtrar_rateio or tipo == 'P-R':
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            if tipo == 'P-R':
                sql_relatorio += """
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""

            if situacao != '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if rel_obj.res_partner_bank_id:
                    sql_relatorio += 'and l.sugestao_bank_id = ' + str(rel_obj.res_partner_bank_id.id)

            else:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_quitacao between '{data_inicial}' and '{data_final}'"""

                if rel_obj.res_partner_bank_id:
                    sql_relatorio += 'and l.res_partner_bank_id = ' + str(rel_obj.res_partner_bank_id.id)

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """

            if partner_id:
                sql_relatorio += """
                   and l.partner_id = """ + str(partner_id)

            if provisionado == True and ativo == False:
                sql_relatorio += """
                   and l.provisionado = """ + str(provisionado)

            if ativo == True and provisionado == False:
                sql_relatorio += """
                   and l.provisionado = False """

            if rel_obj.formapagamento_id:
                sql_relatorio += """
                   and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    sql_relatorio += """
                       and lr.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

                if rel_obj.project_id:
                    sql_relatorio += """
                       and lr.project_id = """ + str(rel_obj.project_id.id)

            sql_relatorio += """
                    order by c.name, l.situacao, l.data_vencimento, p.name, p.cnpj_cpf;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            if tipo == 'P-R':
                for id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, valor_saldo, nosso_numero, cliente, contato, unidade, situacao, conta_codigo, conta_nome, provisionado, centro_custo, projeto, banco  in dados:
                    linha = DicionarioBrasil()
                    linha['id'] = id
                    linha['numero_documento'] = numero_documento
                    linha['data_documento'] = parse_datetime(data_documento)
                    linha['data_vencimento'] = parse_datetime(data_vencimento)
                    linha['data_quitacao'] = parse_datetime(data_quitacao)
                    linha['valor_documento'] = valor_documento
                    linha['valor_desconto'] = valor_desconto
                    linha['valor_juros'] = valor_juros
                    linha['valor_multa'] = valor_multa

                    if data_quitacao:
                        linha['valor'] = valor
                    else:
                        linha['valor'] = valor_documento - valor_desconto + valor_juros + valor_multa

                    if tipo == 'P-R':
                        linha['projeto'] = projeto
                        linha['centro_custo'] = centro_custo
                        linha['banco'] = banco

                    linha['valor_saldo'] = valor_saldo
                    linha['nosso_numero'] = nosso_numero
                    linha['cliente'] = cliente + ' | ' + contato
                    linha['unidade'] = unidade
                    linha['situacao'] = situacao
                    linha['conta_codigo'] = conta_codigo
                    linha['conta_nome'] = conta_nome
                    linha['provisionado'] = provisionado

                    if situacao == 'Vencido':
                        atraso = hoje() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    elif situacao in ('Quitado', 'Conciliado') and data_quitacao > data_vencimento:
                        atraso = parse_datetime(data_quitacao).date() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    else:
                        linha['dias_atraso'] = 0

                    linhas.append(linha)

            else:
                for id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, valor_saldo, nosso_numero, cliente, contato, unidade, situacao, conta_codigo, conta_nome, provisionado  in dados:
                    linha = DicionarioBrasil()
                    linha['id'] = id
                    linha['numero_documento'] = numero_documento
                    linha['data_documento'] = parse_datetime(data_documento)
                    linha['data_vencimento'] = parse_datetime(data_vencimento)
                    linha['data_quitacao'] = parse_datetime(data_quitacao)
                    linha['valor_documento'] = valor_documento
                    linha['valor_desconto'] = valor_desconto
                    linha['valor_juros'] = valor_juros
                    linha['valor_multa'] = valor_multa

                    if data_quitacao:
                        linha['valor'] = valor
                    else:
                        linha['valor'] = valor_documento - valor_desconto + valor_juros + valor_multa

                    linha['valor_saldo'] = valor_saldo
                    linha['nosso_numero'] = nosso_numero
                    linha['cliente'] = cliente + ' | ' + contato
                    linha['unidade'] = unidade
                    linha['situacao'] = situacao
                    linha['conta_codigo'] = conta_codigo
                    linha['conta_nome'] = conta_nome
                    linha['provisionado'] = provisionado

                    if situacao == 'Vencido':
                        atraso = hoje() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    elif situacao in ('Quitado', 'Conciliado') and data_quitacao > data_vencimento:
                        atraso = parse_datetime(data_quitacao).date() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    else:
                        linha['dias_atraso'] = 0

                    linhas.append(linha)

            rel.band_page_header.elements[-1].text = u'Período ' + parse_datetime(data_inicial).strftime('%d/%m/%Y') + u' a ' + parse_datetime(data_final).strftime('%d/%m/%Y')

            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u', empresa/unidade '
                rel.band_page_header.elements[-1].text += rel_obj.company_id.name

            if situacao != '5':
                rel.band_page_header.elements[-1].text += u', situação é ' + sql_situacao

                if rel_obj.res_partner_bank_id:
                    rel.band_page_header.elements[-1].text += u', com previsão para a conta '
                    rel.band_page_header.elements[-1].text += rel_obj.res_partner_bank_id.descricao
                    rel.band_page_header.height += 14
                    rel.band_page_header.elements[-1].text += '<br/>'

            else:
                rel.band_page_header.elements[-1].text += u', situação Liquidados/Quitados'

                if rel_obj.res_partner_bank_id:
                    rel.band_page_header.elements[-1].text += u', na conta '
                    rel.band_page_header.elements[-1].text += rel_obj.res_partner_bank_id.descricao
                    rel.band_page_header.height += 14
                    rel.band_page_header.elements[-1].text += '<br/>'

            if rel_obj.partner_id:
                if tipo == 'R':
                    rel.band_page_header.elements[-1].text += u', do cliente '
                else:
                    rel.band_page_header.elements[-1].text += u', do fornecedor '

                rel.band_page_header.elements[-1].text += rel_obj.partner_id.name

            if rel_obj.formapagamento_id:
                rel.band_page_header.elements[-1].text += u', forma de pagamento '
                rel.band_page_header.elements[-1].text += rel_obj.formapagamento_id.nome

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    rel.band_page_header.elements[-1].text += u', centro de custo '
                    rel.band_page_header.elements[-1].text += rel_obj.centrocusto_id.nome_completo

                if rel_obj.project_id:
                    rel.band_page_header.elements[-1].text += u', projeto '
                    rel.band_page_header.elements[-1].text += rel_obj.project_id.name

            #pdf = gera_relatorio(rel, lancamento_objs)
            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'contas_receber.pdf' if tipo == 'R' else 'contas_pagar.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'contas_receber.csv' if tipo == 'R' else 'contas_pagar.csv',
                'arquivo_csv': base64.encodestring(csv),
            }
            rel_obj.write(dados)

        return True
    
    def gera_relatorio_contas_receber(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_contas(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_contas_pagar(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas(cr, uid, ids, context=context, tipo='P')


finan_relatorio()
