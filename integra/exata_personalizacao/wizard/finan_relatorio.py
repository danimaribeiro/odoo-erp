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
    }

    _defaults = {
        'provisionado': False,
        'nao_provisionado': True,
        'company_id': False,
    }

    def gera_relatorio_fluxo_caixa_analitico_exata(self, cr, uid, ids, context={}):
        if not ids:
            return False

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        provisionado = context.get('provisionado')
        nao_provisionado = context.get('nao_provisionado')

        print(provisionado)
        print(nao_provisionado)

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
        }

        rel = Report('Fluxo de Caixa', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_mensal_diario.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        rel.parametros['DETALHE_SALDO_BANCO'] = 'saldo_financeiro_fluxo_caixa_exata.jasper'
        rel.outputFormat = rel_obj.formato

        if company_id:
            rel.parametros['COMPANY_ID'] = str(company_id)
        else:
            company_id_default = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')
            rel.parametros['COMPANY_ID'] = '%'

        if rel_obj.opcoes_caixa == '1':
            filtro['tipo'] = "('Q')"
            rel.parametros['TIPO'] = "('Q')"
        elif rel_obj.opcoes_caixa == '2':
            filtro['tipo'] = "('Q','V')"
            rel.parametros['TIPO'] = "('Q','V')"
        else:
            filtro['tipo'] = "('V')"
            rel.parametros['TIPO'] = "('V')"

        #
        # SALDO ANTERIOR
        #

        sql_saldo = """
                select
                    coalesce(sum(f.valor_entrada) - sum(f.valor_saida), 0) as diferenca
                from
                    finan_fluxo_mensal_diario f
                where
                    f.data  < '{data_inicial}'
                    and f.tipo in {tipo} """
        if company_id:
            sql_saldo += """
                and
                    f.company_id = {company_id} """

        if nao_provisionado != provisionado:
            sql_saldo += """
                and f.provisionado = """ + str(provisionado)

        sql_saldo = sql_saldo.format(**filtro)
        saldo_anterior = 0
        cr.execute(sql_saldo)
        dados = cr.fetchall()

        if len(dados):
            saldo_anterior += dados[0][0]

        rel.parametros['SALDO_ANTERIOR'] = saldo_anterior

        #
        # FLUXO CAIXA
        #

        if rel_obj.periodo == '1':
            sql_relatorio = """
                select
                    f.mes,"""
        else:
            sql_relatorio = """
                select
                    f.data,"""

        sql_relatorio += """
                    sum(f.valor_entrada) as valor_entrada,
                    sum(f.valor_saida) as valor_saida,
                    sum(f.valor_entrada) - sum(f.valor_saida) as diferenca"""

        if rel_obj.periodo == '3':
            sql_relatorio += """,
                    fd.nome,
                    fl.tipo,
                    case
                    when fl.tipo = 'T' and f.id < 0 then bad.nome
                    when fl.tipo = 'T' and f.id > 0 then bac.nome
                    when fl.tipo not in ('P','R') or fl.situacao = 'Quitado' then bad.nome
                    else
                    ba.nome end as banco,
                    case
                    when rp.name is not NUll then
                    rp.name
                    else
                    coalesce(fl.complemento,'') end as parceiro"""

        sql_relatorio += """
                from
                    finan_fluxo_mensal_diario f
                    join res_company c on c.id = f.company_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id
                    join finan_lancamento fl on fl.id = f.lancamento_id
                    left join res_partner rp on rp.id = fl.partner_id
                    left join finan_documento fd on fd.id = fl.documento_id
                    left join res_partner_bank bad on bad.id = fl.res_partner_bank_id
                    left join res_partner_bank bac on bac.id = fl.res_partner_bank_creditar_id"""

        if rel_obj.periodo not in ['1','2']:

            if rel_obj.opcoes_caixa == '1':
                    sql_relatorio += """
                        left join res_partner_bank ba on ba.id = fl.res_partner_bank_id"""
            else:
                sql_relatorio += """
                    left join res_partner_bank ba on ba.id = fl.sugestao_bank_id"""

        sql_relatorio += """
                where
                    f.data between '{data_inicial}' and '{data_final}'
                    and f.tipo in {tipo} """

        if company_id:
            sql_relatorio += """
                    and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                    )"""

        if nao_provisionado != provisionado:
            sql_relatorio += """
               and fl.provisionado = """ + str(provisionado)

        if rel_obj.opcoes_caixa == '2':
            if rel_obj.res_partner_bank_id:
                sql_relatorio += 'and fl.sugestao_bank_id = ' + str(rel_obj.res_partner_bank_id.id)
        else:
            if rel_obj.res_partner_bank_id:
                sql_relatorio += 'and (fl.res_partner_bank_id = ' + str(rel_obj.res_partner_bank_id.id)
                sql_relatorio += ' or fl.res_partner_bank_creditar_id = ' + str(rel_obj.res_partner_bank_id.id)
                sql_relatorio += ')'

        if rel_obj.periodo == '1':
            sql_relatorio += """
                group by
                    c.id,
                    f.mes

                order by
                    f.mes"""
        elif rel_obj.periodo == '2':
            sql_relatorio += """
                group by
                    c.id,
                    f.data

                order by
                    f.data;
            """
        else:
            sql_relatorio += """
                group by
                    c.id,
                    f.data,
                    fd.nome,
                    fl.tipo,
                    banco,
                    parceiro

                order by
                    f.data,
                    valor_entrada desc,
                    valor_saida desc;
            """

        sql = sql_relatorio.format(**filtro)

        if rel_obj.periodo == '1':
            rel.parametros['PERIODO'] = 'MENSAL'
            rel.parametros['DETALHE'] = 'fluxo_mensal_lancamento.jasper'
            rel.parametros['SQL_RELATORIO'] = sql
            relatorio = u'fluxo_caixa_mensal_'

        elif rel_obj.periodo == '2':
            rel.parametros['PERIODO'] = 'DIARIO'
            rel.parametros['DETALHE'] = 'fluxo_diario_lancamento.jasper'
            rel.parametros['SQL_RELATORIO'] = sql
            relatorio = u'fluxo_caixa_diario_'

        else:
            rel.parametros['PERIODO'] = 'ANALITICO'
            rel.parametros['DETALHE'] = 'fluxo_caixa_analitico_exata.jasper'
            rel.parametros['SQL_RELATORIO'] = sql
            relatorio = u'fluxo_caixa_analitico_'

        if rel_obj.saldo_bancario:
            rel.parametros['SALDO_BANCO'] = True
        else:
            rel.parametros['SALDO_BANCO'] = False

        if rel_obj.zera_saldo:
            rel.parametros['ZERA_SALDO'] = True
        else:
            rel.parametros['ZERA_SALDO'] = False

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
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
                and l.situacao in ('Vencido', 'Vence hoje')
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

        pdf, formato = rel.execute()

        dados = {
            'nome': 'demonstrativo_parcelas_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


finan_relatorio()
