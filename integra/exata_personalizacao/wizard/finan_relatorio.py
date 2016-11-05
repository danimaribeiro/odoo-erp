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
        'contrato_id': fields.many2one('finan.contrato', u'Contrato'),
        'parcela_id': fields.many2one('finan.contrato.condicao.parcela', u'Parcela'),
        'agrupa_cliente': fields.boolean(u'Somente Cliente?'),
        'imovel_id': fields.many2one('const.imovel', u'Imóvel'),
    }

    _defaults = {
        'provisionado': False,
        'nao_provisionado': True,
        'company_id': False,
        'agrupa_cliente': False,
    }

    def gera_relatorio_fluxo_caixa_analitico_exata(self, cr, uid, ids, context={}):
        if not ids:
            return False

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        provisionado = context.get('provisionado')
        nao_provisionado = context.get('nao_provisionado')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if rel_obj.formato == 'pdf':
            formato = 'pdf'
        else:
            formato = 'xlsx'

        if rel_obj.opcoes_caixa == '1':
            tipo_analise = u'REALIZADO'
            selecao = u'DATA DE QUITAÇÃO'
        elif rel_obj.opcoes_caixa == '2':
            tipo_analise = u'COMPROMETIDO'
            selecao = u'DATA VENCIMENTO'
        else:
            tipo_analise = u'A REALIZAR'
            selecao = u'QUITAÇÃO E VENCIMENTO'

        sql, sql_relatorio_SUB, saldo_anterior, filtro, filtro_banco = self.sql_fluxo_caixa_analitico(cr, uid, ids, context=context)

        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        grupos_empresa = {}
        empresas = []
        empresa_anterior = None
        linhas = []

        bancos = []
        banco_anterior = None

        grupo_totais_mes_datas = {}
        totais_mes_datas = []
        mes_data = None

        if len(rel_obj.res_partner_bank_ids) > 0:
            for banco_obj in rel_obj.res_partner_bank_ids:
                if banco_obj.id != banco_anterior:
                    banco = DicionarioBrasil()
                    banco['tipo'] = banco_obj.state
                    banco['nome'] = banco_obj.descricao
                    bancos.append(banco)
                    banco_anterior = banco_obj.id


        if rel_obj.periodo in ['1','2']:
            saldo = D(saldo_anterior)

            print('dados', dados)

            for company_id, cnpj_cpf, raiz_cnpj, empresa, mes, mes_formatado, valor_entrada, valor_saida, diferenca in dados:
                linha = DicionarioBrasil()
                linha['mes'] = mes_formatado
                linha['valor_entrada'] = D(valor_entrada or 0)
                linha['valor_saida'] = D(valor_saida or 0)
                linha['diferenca'] = D(diferenca or 0)
                saldo += D(valor_entrada or 0) - D(valor_saida or 0)
                linha['saldo'] = saldo

                linhas.append(linha)

                if empresa != empresa_anterior:
                    grupo_empresa = DicionarioBrasil()
                    grupo_empresa['nome'] = empresa
                    grupo_empresa['cnpj_cpf'] = cnpj_cpf
                    grupo_empresa['linhas'] = [linha]
                    empresas.append(grupo_empresa)
                    grupos_empresa[empresa] = grupo_empresa
                    empresa_anterior = empresa
                else:
                    grupo_empresa = grupos_empresa[empresa]
                    grupo_empresa.linhas.append(linha)

                if mes_data != mes:
                    if mes in grupo_totais_mes_datas:
                        total_mes_data = grupo_totais_mes_datas[mes]
                        total_mes_data['valor_entrada'] +=  D(valor_entrada or 0)
                        total_mes_data['valor_saida'] += D(valor_saida or 0)
                        total_mes_data['diferenca'] += D(diferenca or 0)
                        total_mes_data['saldo'] += D(saldo or 0)

                    else:
                        total_mes_data = DicionarioBrasil()
                        total_mes_data['mes_data'] = mes_formatado
                        total_mes_data['valor_entrada'] = D(valor_entrada or 0)
                        total_mes_data['valor_saida'] = D(valor_saida or 0)
                        total_mes_data['diferenca'] = D(diferenca or 0)
                        total_mes_data['saldo'] = D(saldo or 0)
                        totais_mes_datas.append(total_mes_data)
                        grupo_totais_mes_datas[mes] = total_mes_data
                        mes_data = mes
                else:
                    total_mes_data = grupo_totais_mes_datas[mes]
                    total_mes_data['valor_entrada'] +=  D(valor_entrada or 0)
                    total_mes_data['valor_saida'] += D(valor_saida or 0)
                    total_mes_data['diferenca'] += linha.diferenca
                    total_mes_data['saldo'] += saldo


            for empresa in empresas:
                empresa['total'] = DicionarioBrasil()
                empresa.total['valor_entrada'] = D(0)
                empresa.total['valor_saida'] = D(0)
                empresa.total['diferenca'] = D(0)
                empresa.total['saldo'] = D(0)
                empresa.total['saldo_anterior'] = formata_valor(D(saldo_anterior))

                for linha in empresa.linhas:
                    empresa.total.valor_entrada += linha.valor_entrada
                    empresa.total.valor_saida += linha.valor_saida
                    empresa.total.diferenca += linha.diferenca
                    empresa.total.saldo += linha.saldo

                    linha.valor_entrada = formata_valor(linha.valor_entrada)
                    linha.valor_saida  = formata_valor(linha.valor_saida)
                    linha.diferenca     = formata_valor(linha.diferenca)
                    linha.saldo     = formata_valor(linha.saldo)

                empresa.total.valor_entrada = formata_valor(empresa.total.valor_entrada)
                empresa.total.valor_saida  = formata_valor(empresa.total.valor_saida)
                empresa.total.diferenca     = formata_valor(empresa.total.diferenca)
                empresa.total.saldo     = formata_valor(empresa.total.saldo)

            total_geral = DicionarioBrasil()
            total_geral['valor_entrada'] = D(0)
            total_geral['valor_saida'] = D(0)
            total_geral['diferenca'] = D(0)
            total_geral['saldo'] = D(0)
            total_geral['saldo_anterior'] = formata_valor(D(saldo_anterior))
            for total_mes_data in totais_mes_datas:
                total_geral.valor_entrada += total_mes_data.valor_entrada
                total_geral.valor_saida += total_mes_data.valor_saida
                total_geral.diferenca += total_mes_data.diferenca
                total_geral.saldo += total_mes_data.saldo

                total_mes_data.valor_entrada = formata_valor(total_mes_data.valor_entrada)
                total_mes_data.valor_saida = formata_valor(total_mes_data.valor_saida)
                total_mes_data.diferenca = formata_valor(total_mes_data.diferenca)
                total_mes_data.saldo = formata_valor(total_mes_data.saldo)

            total_geral.valor_entrada = formata_valor(total_geral.valor_entrada)
            total_geral.valor_saida = formata_valor(total_geral.valor_saida)
            total_geral.diferenca = formata_valor(total_geral.diferenca)
            total_geral.saldo = formata_valor(total_geral.saldo)

            dados = {
                'data_inicial': formata_data(rel_obj.data_inicial),
                'data_final': formata_data(rel_obj.data_inicial),
                'empresas': empresas,
                'tipo_analise': tipo_analise,
                'selecao': selecao,
                'bancos': bancos,
                'totais_mes_datas': totais_mes_datas,
                'total_geral': total_geral,
            }
            if rel_obj.periodo  == '1':
                dados['titulo'] = u'RELATÓRIO DE FLUXO DE CAIXA MENSAL',
                nome_arquivo = JASPER_BASE_DIR + 'finan_fluxo_caixa_mensal_exata.ods'
                relatorio = u'fluxo_caixa_mensal.'
            else:
                nome_arquivo = JASPER_BASE_DIR + 'finan_fluxo_caixa_diario_exata.ods'
                dados['titulo'] = u'RELATÓRIO DE FLUXO DE CAIXA DIÁRIO'
            relatorio = u'fluxo_caixa_diario.'
        else:

            saldo = D(saldo_anterior)
            for company_id, cnpj_cpf, raiz_cnpj, empresa, data, valor_entrada, valor_saida, diferenca, numero_documento, tipo_documento, tipo, cliente in dados:
                linha = DicionarioBrasil()
                linha['data'] = formata_data(data)
                linha['numero_documento'] = numero_documento
                linha['tipo_documento'] = tipo_documento
                linha['tipo'] = tipo
                linha['cliente'] = cliente
                linha['valor_entrada'] = D(valor_entrada or 0)
                linha['valor_saida'] = D(valor_saida or 0)
                linha['diferenca'] = D(diferenca or 0)
                saldo += D(valor_entrada or 0) - D(valor_saida or 0)
                linha['saldo'] = saldo

                linhas.append(linha)

                if empresa != empresa_anterior:
                    grupo_empresa = DicionarioBrasil()
                    grupo_empresa['nome'] = empresa
                    grupo_empresa['cnpj_cpf'] = cnpj_cpf
                    grupo_empresa['linhas'] = [linha]
                    empresas.append(grupo_empresa)
                    grupos_empresa[empresa] = grupo_empresa
                    empresa_anterior = empresa
                else:
                    grupo_empresa = grupos_empresa[empresa]
                    grupo_empresa.linhas.append(linha)

            for empresa in empresas:
                empresa['total'] = DicionarioBrasil()
                empresa.total['valor_entrada'] = D(0)
                empresa.total['valor_saida'] = D(0)
                empresa.total['diferenca'] = D(0)
                empresa.total['saldo'] = D(0)
                empresa.total['saldo_anterior'] = formata_valor(D(saldo_anterior))

                for linha in empresa.linhas:
                    empresa.total.valor_entrada += linha.valor_entrada
                    empresa.total.valor_saida += linha.valor_saida
                    empresa.total.diferenca += linha.diferenca
                    empresa.total.saldo += linha.saldo

                    linha.valor_entrada = formata_valor(linha.valor_entrada)
                    linha.valor_saida  = formata_valor(linha.valor_saida)
                    linha.diferenca     = formata_valor(linha.diferenca)
                    linha.saldo     = formata_valor(linha.saldo)

                empresa.total.valor_entrada = formata_valor(empresa.total.valor_entrada)
                empresa.total.valor_saida  = formata_valor(empresa.total.valor_saida)
                empresa.total.diferenca     = formata_valor(empresa.total.diferenca)
                empresa.total.saldo     = formata_valor(empresa.total.saldo)


            dados = {
                'data_inicial': formata_data(rel_obj.data_inicial),
                'data_final': formata_data(rel_obj.data_inicial),
                'empresas': empresas,
                'tipo_analise': tipo_analise,
                'selecao': selecao,
                'bancos': bancos,
            }

            nome_arquivo = JASPER_BASE_DIR + 'finan_fluxo_caixa_analitico_exata.ods'
            dados['titulo']= u'RELATÓRIO DE FLUXO DE CAIXA ANALITICO'
            relatorio = u'fluxo_caixa_analitico.'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados, formato=formato)

        dados = {
            'nome': relatorio + formato,
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_segurado(self, cr, uid, ids, context={}):
        product_pool = self.pool.get('product.product')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            sv.cliente,
            sv.cnpj_cpf,
            sv.data_nascimento,
            sv.sexo,
            sv.lote,
            sv.quadra,
            sv.contrato_id,
            sv.numero_contrato,
            sv.numero_parcelas,
            sv.saldo_devedor
        from finan_segurado_view sv

        where
            sv.project_id = """ + str(rel_obj.project_id.id)
        sql += """
        order by
            sv.numero_contrato,
            sv.cliente;"""

        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        contratos = {}
        saldo_total = D(0)
        for cliente, cnpj_cpf, data_nascimento, sexo, lote, quadra, contrato_id, numero_contrato, numero_parcelas, saldo_devedor  in dados:
            linha = DicionarioBrasil()

            linha['cliente'] = cliente
            linha['cnpj_cpf'] = cnpj_cpf
            linha['data_nascimento'] = data_nascimento
            linha['sexo'] = sexo
            linha['lote'] = lote
            linha['quadra'] = quadra
            linha['contrato_id'] = contrato_id
            linha['numero_contrato'] = numero_contrato
            linha['numero_parcelas'] = numero_parcelas
            linha['saldo_devedor'] = D(saldo_devedor)
            linhas.append(linha)

            if not contrato_id in contratos:
                contratos[contrato_id] = 1
            else:
                contratos[contrato_id] += 1


        for linha in linhas:
            linha.saldo_devedor /= contratos[linha.contrato_id]

            saldo_total += linha.saldo_devedor
            linha.saldo_devedor = formata_valor(linha.saldo_devedor)

        if rel_obj.project_id.indice_segurado:
            indice_segurado = saldo_total * D(rel_obj.project_id.indice_segurado) / 100
        else:
            indice_segurado = 0

        dados = {
            'empresa': rel_obj.project_id.company_id.partner_id.name,
            'projeto': rel_obj.project_id.name,
            'saldo_total': formata_valor(saldo_total),
            'total_contratos': len(linhas),
            'indice_segurado': formata_valor(indice_segurado),
            'linhas': linhas,
        }

        nome_arquivo = JASPER_BASE_DIR + 'finan_contrato_segurado.ods'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)

        dados = {
            'nome': 'finan_contrato_segurado.xlsx',
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True

    def gera_demonstrativo_parcela(self, cr, uid, ids, context={}):
        sql_relatorio = """
            select
                p.id as parcela_id,
                p.parcela,
                p.data_vencimento,
                p.condicao_id,
                p.contrato_id,
                l.valor_documento,
                coalesce(l.valor_saldo, 0) as valor_saldo,
                coalesce(l.valor_multa_prevista, 0) as valor_multa_prevista,
                coalesce(l.valor_juros_previsto, 0) as valor_juros_previsto,
                coalesce(l.valor_previsto, 0) as valor_previsto,
                current_date - l.data_vencimento as atraso

            from
                finan_contrato_condicao_parcela p
                join finan_contrato_condicao c on c.id = p.condicao_id
                join finan_lancamento l on l.finan_contrato_condicao_parcela_id = p.id
                left join finan_carteira ct on ct.id = l.carteira_id

            where
                p.contrato_id = {contrato_id}
                -- and l.situacao in ('Vencido', 'Vence hoje')
                {filtro_parcela}

            order by
                p.data_vencimento
        """

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        filtro = {
            'contrato_id': rel_obj.contrato_id.id,
            'filtro_parcela': ''
        }

        if rel_obj.parcela_id:
            filtro['filtro_parcela'] = 'and p.id = {parcela_id}'.format(parcela_id=rel_obj.parcela_id.id)

        rel = Report('Demonstrativo de Parcelas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_demonstrativo_parcela_contrato.jrxml')
        rel.parametros['CONTRATO'] = rel_obj.contrato_id.nome or ''
        rel.parametros['CLIENTE'] = rel_obj.partner_id.descricao or ''
        rel.parametros['SQL'] = sql_relatorio.format(**filtro)
        rel.outputFormat = rel_obj.formato

        print(sql_relatorio.format(**filtro))

        pdf, formato = rel.execute()

        dados = {
            'nome': 'demonstrativo_parcelas_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_contas_exata(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')
        formato = context.get('formato')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo[0],
            'rateio': '',
        }

        if situacao == '1':
            sql_situacao = u"('Vencido')"
            SITUACAO = u'Vencido'

        elif situacao == '2':
            sql_situacao = u"('Vencido', 'Vence hoje')"
            SITUACAO = u'Vencido + Hoje'

        elif situacao == '3':
            sql_situacao = u"('A vencer')"
            SITUACAO = u'A Vencer'

        elif situacao == '4':
            sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Todos em aberto'

        elif situacao == '5':
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Liquidadas'

        else:
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Registrados'

        for rel_obj in self.browse(cr, uid, ids):
            texto_filtro = u''
            if len(rel_obj.res_partner_bank_ids):
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    #banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(fcp.valor_capital, coalesce(l.valor_documento, 0.00)) {rateio} as valor_documento,
                   coalesce(l.valor_desconto, 0.00) {rateio} as valor_desconto,
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) {rateio} as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) {rateio} as valor_multa,

                   coalesce(l.valor, 0.00) {rateio} as valor,
                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,
                   case
                        when fcp.valor_capital is not null then coalesce(l.valor_saldo, 0) - coalesce(fcp.valor_capital, 0)
                        else 0
                    end {rateio} as valor_contrato_correcao,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.razao_social, '') || ' | ' || coalesce(p.name, '') || ' | ' || coalesce(p.cnpj_cpf, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   coalesce(p.email_nfe, '') as email_nfe,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   cf.nome as conta_nome,
                   l.provisionado,
                   case
                   when l.data_vencimento < current_date then
                   current_date - l.data_vencimento
                   else
                   0 end as data_atraso"""
            if rel_obj.filtrar_rateio:
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
                   left join finan_contrato_condicao_parcela fcp on fcp.id = l.finan_contrato_condicao_parcela_id"""

            if rel_obj.filtrar_rateio:
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            if rel_obj.filtrar_rateio:
                sql_relatorio += """
                   left join finan_conta cf on cf.id = lr.conta_id"""
                   #left join finan_conta pfc on pfc.id = cf.parent_id"""
            else:
                sql_relatorio += """
                   left join finan_conta cf on cf.id = l.conta_id"""
                   #left join finan_conta pfc on pfc.id = cf.parent_id"""

            if rel_obj.filtrar_rateio:
                sql_relatorio += """
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""

            elif rel_obj.imovel_id:
                sql_relatorio += """
                    left join finan_contrato ci on (ci.id = l.contrato_id or ci.id = l.contrato_imovel_id)
                """

            if situacao < '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in '  +  str(tuple(bancos_ids)).replace(',)', ')')

            elif situacao == '5' and not rel_obj.agrupa_cliente:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and exists(select lp.id from finan_lancamento lp where lp.lancamento_id = l.id and lp.tipo in ('PP', 'PR') and lp.data_quitacao between '{data_inicial}' and '{data_final}')"""

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in'   +  str(tuple(bancos_ids)).replace(',)', ')')
            else:
                if rel_obj.agrupa_cliente:
                    sql_relatorio += """
                       where l.tipo = '{tipo}'
                       and l.data_documento between '{data_inicial}' and '{data_final}'"""
                else:
                    sql_relatorio += """
                       where l.tipo = '{tipo}'
                       and l.data_documento between '{data_inicial}' and '{data_final}'
                       and l.situacao in """ + sql_situacao

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """

            if rel_obj.dias_atraso:
                sql_relatorio +="""
                    and current_date - l.data_vencimento = """ + str(rel_obj.dias_atraso)

            if rel_obj.sem_nf:
                sql_relatorio +="""
                    and sped_documento_id is null"""

            if partner_id:
                sql_relatorio += """
                   and l.partner_id = """ + str(partner_id)

            if ativo != provisionado:
                sql_relatorio += """
                   and l.provisionado = """ + str(provisionado)

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

                if rel_obj.conta_id:
                    sql_relatorio += """
                       and cf.codigo_completo like '""" + rel_obj.conta_id.codigo_completo + """%'"""

            elif rel_obj.imovel_id:
                sql_relatorio += """
                    and ci.imovel_id = {imovel_id}
                """.format(imovel_id=rel_obj.imovel_id.id)

            if rel_obj.agrupa_data_vencimento:
                sql_relatorio += """
                        order by c.name, l.situacao,l.data_vencimento, p.razao_social, p.name, p.cnpj_cpf, cf.codigo_completo desc;"""

            elif rel_obj.agrupa_cliente:
                sql_relatorio += """
                        order by c.name, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento, cf.codigo_completo desc;"""

            else:
                sql_relatorio += """
                        order by c.name, l.situacao, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento, cf.codigo_completo desc;"""


            sql_relatorio = sql_relatorio.format(**filtro)
            print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            dados_relatorio = {
                'data_inicial': formata_data(rel_obj.data_inicial),
                'data_final': formata_data(rel_obj.data_final),
                'banco': texto_filtro,
                'empresas': [],
                'total_geral': [],
                'imprime_rel': True,
                'empresa_nome': 'Todas',
            }

            if len(dados) == 0:
                dados_relatorio['imprime_rel'] = False
                if rel_obj.company_id:
                    dados_relatorio['empresa_nome'] = rel_obj.company_id.partner_id.name

            else:
                grupos_empresa = {}
                empresas = []
                empresa_anterior = None
                situacao_anterior = None
                cliente_anterior = None
                linhas = []

                if not rel_obj.filtrar_rateio:
                    for lancamento_id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor , valor_saldo, valor_contrato_correcao, nosso_numero, cliente, contato, email_nfe, empresa, situacao, codigo_conta, conta_nome, provisionado, data_atraso  in dados:
                        linha = DicionarioBrasil()
                        linha['numero_documento'] = numero_documento
                        linha['data_documento'] = formata_data(data_documento)
                        linha['data_vencimento'] = formata_data(data_vencimento)
                        linha['data_quitacao'] = formata_data(data_quitacao)
                        linha['valor_documento'] = D(valor_documento or 0)
                        linha['valor_desconto'] = D(valor_desconto or 0)
                        linha['valor_juros'] = D(valor_juros or 0)
                        linha['valor_multa'] = D(valor_multa or 0)
                        linha['valor'] = D(valor or 0)
                        linha['valor_saldo'] = D(valor_saldo or 0)
                        linha['valor_contrato_correcao'] = D(valor_contrato_correcao or 0)
                        linha['valor_saldo_correcao'] = D(valor_saldo or 0) + D(valor_juros or 0) + D(valor_multa or 0)
                        linha['nosso_numero'] = nosso_numero
                        linha['cliente'] = cliente + u' / ' + email_nfe
                        linha['situacao'] = situacao
                        linha['codigo_conta'] = codigo_conta
                        linha['conta_nome'] = conta_nome
                        linha['provisionado'] = 'X' if provisionado else ''
                        linha['data_atraso'] = data_atraso

                        linhas.append(linha)

                        if empresa != empresa_anterior:
                            grupo_empresa = DicionarioBrasil()
                            grupo_empresa['nome'] = empresa
                            grupo_empresa['situacoes'] = []
                            grupo_empresa['grupos_situacao'] = {}
                            empresas.append(grupo_empresa)
                            grupos_empresa[empresa] = grupo_empresa
                            empresa_anterior = empresa
                            situacao_anterior = None
                            cliente_anterior = None

                        else:
                            grupo_empres = grupos_empresa[empresa]

                        if situacao != situacao_anterior:
                            grupo_situacao = DicionarioBrasil()
                            grupo_situacao['nome'] = situacao
                            grupo_situacao['clientes'] = []
                            grupo_situacao['grupos_cliente'] = {}
                            grupo_empresa['situacoes'].append(grupo_situacao)
                            grupo_empresa['grupos_situacao'][situacao] = grupo_situacao
                            situacao_anterior = situacao
                            cliente_anterior = None
                        else:
                            grupo_situacao = grupo_empresa['grupos_situacao'][situacao]

                        if cliente != cliente_anterior:
                            grupo_cliente = DicionarioBrasil()
                            grupo_cliente['nome'] = cliente + u' / ' + email_nfe
                            grupo_cliente['linhas'] = [linha]
                            grupo_situacao['clientes'].append(grupo_cliente)
                            grupo_situacao['grupos_cliente'][cliente] = grupo_cliente
                            cliente_anterior = cliente
                        else:
                            grupo_cliente = grupo_situacao['grupos_cliente'][cliente]
                            grupo_cliente.linhas.append(linha)

                else:
                    for lancamento_id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor , valor_saldo, valor_contrato_correcao, nosso_numero, cliente, contato, email_nfe, empresa, situacao, codigo_conta, conta_nome, provisionado, data_atraso, centro_custo, projeto, banco  in dados:
                        linha = DicionarioBrasil()
                        linha['numero_documento'] = numero_documento
                        linha['data_documento'] = formata_data(data_documento)
                        linha['data_vencimento'] = formata_data(data_vencimento)
                        linha['data_quitacao'] = formata_data(data_quitacao)
                        linha['valor_documento'] = D(valor_documento or 0)
                        linha['valor_desconto'] = D(valor_desconto or 0)
                        linha['valor_juros'] = D(valor_juros or 0)
                        linha['valor_multa'] = D(valor_multa or 0)
                        linha['valor'] = D(valor or 0)
                        linha['valor_saldo'] = D(valor_saldo or 0)
                        linha['valor_contrato_correcao'] = D(valor_contrato_correcao or 0)
                        linha['valor_saldo_correcao'] = D(valor_saldo or 0) + D(valor_juros or 0) + D(valor_multa or 0)
                        linha['nosso_numero'] = nosso_numero
                        linha['cliente'] = cliente + u' / ' + email_nfe
                        linha['situacao'] = situacao
                        linha['codigo_conta'] = codigo_conta
                        linha['conta_nome'] = conta_nome
                        linha['provisionado'] = provisionado
                        linha['data_atraso'] = data_atraso
                        linha['centro_custo'] = centro_custo
                        linha['projeto'] = projeto
                        linha['banco'] = banco

                        linhas.append(linha)

                        if empresa != empresa_anterior:
                            grupo_empresa = DicionarioBrasil()
                            grupo_empresa['nome'] = empresa
                            grupo_empresa['situacoes'] = []
                            grupo_empresa['grupos_situacao'] = {}
                            empresas.append(grupo_empresa)
                            grupos_empresa[empresa] = grupo_empresa
                            empresa_anterior = empresa
                            situacao_anterior = None
                            cliente_anterior = None

                        else:
                            grupo_empresa = grupos_empresa[empresa]

                        if situacao != situacao_anterior:
                            grupo_situacao = DicionarioBrasil()
                            grupo_situacao['nome'] = situacao
                            grupo_situacao['clientes'] = []
                            grupo_situacao['grupos_cliente'] = {}
                            grupo_empresa['situacoes'].append(grupo_situacao)
                            grupo_empresa['grupos_situacao'][situacao] = grupo_situacao
                            situacao_anterior = situacao
                            cliente_anterior = None
                        else:
                            grupo_situacao = grupo_empresa['grupos_situacao'][situacao]

                        if cliente != cliente_anterior:
                            grupo_cliente = DicionarioBrasil()
                            grupo_cliente['nome'] = cliente + u' / ' + email_nfe
                            grupo_cliente['linhas'] = [linha]
                            grupo_situacao['clientes'].append(grupo_cliente)
                            grupo_situacao['grupos_cliente'][cliente] = grupo_cliente
                            cliente_anterior = cliente
                        else:
                            grupo_cliente = grupo_situacao['grupos_cliente'][cliente]
                            grupo_cliente.linhas.append(linha)

                #
                # soma subtotais aqui
                #

                total_geral = DicionarioBrasil()
                total_geral['valor_documento'] = D(0)
                total_geral['valor_desconto'] = D(0)
                total_geral['valor_juros'] = D(0)
                total_geral['valor_multa'] = D(0)
                total_geral['valor'] = D(0)
                total_geral['valor_saldo'] = D(0)
                total_geral['valor_saldo_correcao'] = D(0)
                total_geral['valor_contrato_correcao'] = D(0)

                for empresa in empresas:
                    empresa['total'] = DicionarioBrasil()
                    empresa.total['valor_documento'] = D(0)
                    empresa.total['valor_desconto'] = D(0)
                    empresa.total['valor_juros'] = D(0)
                    empresa.total['valor_multa'] = D(0)
                    empresa.total['valor'] = D(0)
                    empresa.total['valor_saldo'] = D(0)
                    empresa.total['valor_saldo_correcao'] = D(0)
                    empresa.total['valor_contrato_correcao'] = D(0)

                    for situacao in empresa.situacoes:
                        situacao['total'] = DicionarioBrasil()
                        situacao.total['valor_documento'] = D(0)
                        situacao.total['valor_desconto'] = D(0)
                        situacao.total['valor_juros'] = D(0)
                        situacao.total['valor_multa'] = D(0)
                        situacao.total['valor'] = D(0)
                        situacao.total['valor_saldo'] = D(0)
                        situacao.total['valor_saldo_correcao'] = D(0)
                        situacao.total['valor_contrato_correcao'] = D(0)

                        for cliente in situacao.clientes:
                            cliente['total'] = DicionarioBrasil()
                            cliente.total['valor_documento'] = D(0)
                            cliente.total['valor_desconto'] = D(0)
                            cliente.total['valor_juros'] = D(0)
                            cliente.total['valor_multa'] = D(0)
                            cliente.total['valor'] = D(0)
                            cliente.total['valor_saldo'] = D(0)
                            cliente.total['valor_saldo_correcao'] = D(0)
                            cliente.total['valor_contrato_correcao'] = D(0)

                            for linha in cliente.linhas:
                                cliente.total.valor_documento += linha.valor_documento
                                cliente.total.valor_desconto += linha.valor_desconto
                                cliente.total.valor_juros += linha.valor_juros
                                cliente.total.valor_multa += linha.valor_multa
                                cliente.total.valor += linha.valor
                                cliente.total.valor_saldo += linha.valor_saldo
                                cliente.total.valor_saldo_correcao += linha.valor_saldo_correcao
                                cliente.total.valor_contrato_correcao += linha.valor_contrato_correcao

                                #
                                # Deixamos agora os valores formatados
                                #
                                linha.valor_documento = formata_valor(linha.valor_documento)
                                linha.valor_desconto  = formata_valor(linha.valor_desconto)
                                linha.valor_juros     = formata_valor(linha.valor_juros)
                                linha.valor_multa     = formata_valor(linha.valor_multa)
                                linha.valor           = formata_valor(linha.valor)
                                linha.valor_saldo     = formata_valor(linha.valor_saldo)
                                linha.valor_saldo_correcao     = formata_valor(linha.valor_saldo_correcao)
                                linha.valor_contrato_correcao     = formata_valor(linha.valor_contrato_correcao)

                            situacao.total.valor_documento += cliente.total.valor_documento
                            situacao.total.valor_desconto  += cliente.total.valor_desconto
                            situacao.total.valor_juros     += cliente.total.valor_juros
                            situacao.total.valor_multa     += cliente.total.valor_multa
                            situacao.total.valor           += cliente.total.valor
                            situacao.total.valor_saldo     += cliente.total.valor_saldo
                            situacao.total.valor_saldo_correcao     += cliente.total.valor_saldo_correcao
                            situacao.total.valor_contrato_correcao     += cliente.total.valor_contrato_correcao

                            cliente.total.valor_documento = formata_valor(cliente.total.valor_documento)
                            cliente.total.valor_desconto  = formata_valor(cliente.total.valor_desconto)
                            cliente.total.valor_juros     = formata_valor(cliente.total.valor_juros)
                            cliente.total.valor_multa     = formata_valor(cliente.total.valor_multa)
                            cliente.total.valor           = formata_valor(cliente.total.valor)
                            cliente.total.valor_saldo     = formata_valor(cliente.total.valor_saldo)
                            cliente.total.valor_saldo_correcao     = formata_valor(cliente.total.valor_saldo_correcao)
                            cliente.total.valor_contrato_correcao     = formata_valor(cliente.total.valor_contrato_correcao)


                        empresa.total.valor_documento += situacao.total.valor_documento
                        empresa.total.valor_desconto  += situacao.total.valor_desconto
                        empresa.total.valor_juros     += situacao.total.valor_juros
                        empresa.total.valor_multa     += situacao.total.valor_multa
                        empresa.total.valor           += situacao.total.valor
                        empresa.total.valor_saldo     += situacao.total.valor_saldo
                        empresa.total.valor_saldo_correcao     += situacao.total.valor_saldo_correcao
                        empresa.total.valor_contrato_correcao     += situacao.total.valor_contrato_correcao

                        situacao.total.valor_documento = formata_valor(situacao.total.valor_documento)
                        situacao.total.valor_desconto  = formata_valor(situacao.total.valor_desconto)
                        situacao.total.valor_juros     = formata_valor(situacao.total.valor_juros)
                        situacao.total.valor_multa     = formata_valor(situacao.total.valor_multa)
                        situacao.total.valor           = formata_valor(situacao.total.valor)
                        situacao.total.valor_saldo     = formata_valor(situacao.total.valor_saldo)
                        situacao.total.valor_saldo_correcao     = formata_valor(situacao.total.valor_saldo_correcao)
                        situacao.total.valor_contrato_correcao     = formata_valor(situacao.total.valor_contrato_correcao)

                    total_geral.valor_documento += empresa.total.valor_documento
                    total_geral.valor_desconto  += empresa.total.valor_desconto
                    total_geral.valor_juros     += empresa.total.valor_juros
                    total_geral.valor_multa     += empresa.total.valor_multa
                    total_geral.valor           += empresa.total.valor
                    total_geral.valor_saldo     += empresa.total.valor_saldo
                    total_geral.valor_saldo_correcao     += empresa.total.valor_saldo_correcao
                    total_geral.valor_contrato_correcao     += empresa.total.valor_contrato_correcao

                    empresa.total.valor_documento = formata_valor(empresa.total.valor_documento)
                    empresa.total.valor_desconto  = formata_valor(empresa.total.valor_desconto)
                    empresa.total.valor_juros     = formata_valor(empresa.total.valor_juros)
                    empresa.total.valor_multa     = formata_valor(empresa.total.valor_multa)
                    empresa.total.valor           = formata_valor(empresa.total.valor)
                    empresa.total.valor_saldo     = formata_valor(empresa.total.valor_saldo)
                    empresa.total.valor_saldo_correcao     = formata_valor(empresa.total.valor_saldo_correcao)
                    empresa.total.valor_contrato_correcao     = formata_valor(empresa.total.valor_contrato_correcao)

                total_geral.valor_documento = formata_valor(total_geral.valor_documento)
                total_geral.valor_desconto  = formata_valor(total_geral.valor_desconto)
                total_geral.valor_juros     = formata_valor(total_geral.valor_juros)
                total_geral.valor_multa     = formata_valor(total_geral.valor_multa)
                total_geral.valor           = formata_valor(total_geral.valor)
                total_geral.valor_saldo     = formata_valor(total_geral.valor_saldo)
                total_geral.valor_saldo_correcao     = formata_valor(total_geral.valor_saldo_correcao)
                total_geral.valor_contrato_correcao     = formata_valor(total_geral.valor_contrato_correcao)

                dados_relatorio['empresas'] = empresas
                dados_relatorio['total_geral'] = total_geral

            if rel_obj.filtrar_rateio and not rel_obj.agrupa_cliente:
                nome_arquivo = JASPER_BASE_DIR + 'finan_relatorio_contas_exata_rateio.ods'
                if tipo == 'R':
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS POR CLIENTE RATEIO'
                    nome = 'contas_receber_rateio.' + formato
                else:
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS POR FORNECEDOR RATEIO'
                    nome = 'contas_pagar_rateio.' + formato

            elif rel_obj.agrupa_cliente :
                nome_arquivo = JASPER_BASE_DIR + 'finan_relatorio_contas_cliente_exata.ods'
                if tipo == 'R':
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS POR CLIENTE'
                    nome = 'contas_receber_cliente.' + formato
                else:
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS POR FORNECEDOR'
                    nome = 'contas_receber_fornecedor.' + formato

            else:
                nome_arquivo = JASPER_BASE_DIR + 'finan_relatorio_contas_exata.ods'
                if tipo == 'R':
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS A RECEBER'
                    nome = 'contas_receber.' + formato
                else:
                    dados_relatorio['titulo']= u'RELATÓRIO DE CONTAS A PAGAR'
                    nome = 'contas_pagar.' + formato

            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados_relatorio, formato=formato)

            dados = {
                'nome': nome,
                'arquivo': planilha
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contas_receber(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_contas_exata(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_contas_pagar(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_exata(cr, uid, ids, context=context, tipo='P')

finan_relatorio()
