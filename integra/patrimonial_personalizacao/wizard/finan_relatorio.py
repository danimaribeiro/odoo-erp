# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data, tempo
from dateutil.relativedelta import relativedelta
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D


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


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {
        'partner_ids': fields.many2many('res.partner', 'finan_relatorio_partner', 'relatorio_id', 'partner_id', u'Cliente'),
        'comercial_meta_id': fields.many2one('comercial.meta', u'Meta comercial/acumulado'),
        'equipe_id': fields.many2one('instalacao.equipe', u'Equipe de instalação'),
        'municipio_id': fields.many2one('sped.municipio', u'Cidade'),
        'somente_totais': fields.boolean(u'Imprimir Somente os Totais'),
        'user_id': fields.many2one('res.users', u'Setor'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato'),
    }

    _defaults = {
        'por_data': True,
        'conf_contabilidade': False,
    }

    def gera_relatorio_curva_abc_cliente(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Curva ABC Clientes', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_curva_abc_cliente.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = 'xls'


        pdf, formato = rel.execute()

        dados = {
            'nome': u'Curva_abc_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.xls',
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


    def gera_cobranca_juridica(self, cr, uid, ids, context={}):
        for rel_obj in self.browse(cr, uid, ids):
            sql = """
                select
                    p.id as partner_id,
                    coalesce(p.razao_social, p.name) as cliente_nome,
                    coalesce(p.cnpj_cpf, '') as cnpj_cpf,
                    coalesce(p.endereco, '') || ', ' || coalesce(p.numero, '') || ' - ' || coalesce(p.complemento, '') as endereco,
                    coalesce(p.bairro, '') as bairro,
                    coalesce(p.cidade, '') as cidade,
                    coalesce(p.estado, '') as estado,
                    coalesce(p.cep, '') as cep,
                    coalesce(p.fone, '') as fone,
                    coalesce(p.celular, '') as celular,
                    coalesce(p.email_nfe, '') as email,
                    l.numero_documento,
                    l.data_vencimento,
                    l.valor_documento

                from
                    finan_lancamento l
                    join res_partner p on p.id = l.partner_id
                    join res_company c on c.id = l.company_id

                where
                    l.tipo = 'R'
                    and (
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                    )
                    and l.situacao in ('Vencido', 'Vence hoje')
                    and l.formapagamento_id = {formapagamento_id}
                    {filtro_adicional}

                order by
                    p.razao_social,
                    p.name,
                    p.cnpj_cpf;
            """

            filtro = {
                'company_id': rel_obj.company_id.id,
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'formapagamento_id': rel_obj.formapagamento_id.id,
                'filtro_adicional': '',
            }

            if rel_obj.data_inicial and rel_obj.data_final:
                filtro['filtro_adicional'] += "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(data_inicial=rel_obj.data_inicial, data_final=rel_obj.data_final)

            if len(rel_obj.partner_ids):
                partner_ids = []

                for partner_obj in rel_obj.partner_ids:
                    partner_ids.append(partner_obj.id)

                filtro['filtro_adicional'] = 'and l.partner_id in (' + str(partner_ids).replace('[', '').replace(']', '') + ')'

            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            if not len(dados):
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            titulo = u'"CLIENTE_DEVEDOR";"CNPJ_CPF";"NUMERO_DOCUMENTO";"DATA_VENCIMENTO";"VALOR_PENDENTE";"ENDEREÇO";"BAIRRO";"CIDADE";"ESTADO";"CEP";"FONE";"CELULAR";"EMAIL";"OBS"\r\n'
            linhas.append(titulo)
            linha_modelo = u'"{cliente_devedor}";"{cnpj_cpf}";"{numero_documento}";{data_vencimento};{valor_pendente};"{endereco}";"{bairro}";"{cidade}";"{estado}";"{cep}";"{fone}";"{celular}";"{email}";""\r\n'
            linha_vazia = u';;;;;;;;;;;;;\r\n'
            partner_id_antigo = None
            for partner_id, cliente_nome, cnpj_cpf, endereco, bairro, cidade, estado, cep, fone, celular, email, numero_documento, data_vencimento, valor_documento in dados:
                linha = {}
                linha['cliente_devedor'] = cliente_nome or ''
                linha['cnpj_cpf'] = cnpj_cpf or ''
                linha['endereco'] = endereco or ''
                linha['bairro'] = bairro or ''
                linha['cidade'] = cidade or ''
                linha['estado'] = estado or ''
                linha['cep'] = cep or ''
                linha['fone'] = fone or ''
                linha['celular'] = celular or ''
                linha['email'] = email or ''
                linha['numero_documento'] = numero_documento or ''
                linha['data_vencimento'] = parse_datetime(data_vencimento).date()
                linha['valor_pendente'] = str(D(valor_documento or 0)).replace('.', ',')

                if partner_id_antigo is None:
                    partner_id_antigo = partner_id
                elif partner_id != partner_id_antigo:
                    partner_id_antigo = partner_id
                    linhas.append(linha_vazia)

                linha_texto = linha_modelo.format(**linha)
                linhas.append(linha_texto)

            csv = u''.join(linhas)
            csv = csv.encode('iso-8859-1')

            dados = {
                'nome_csv': 'cobranca_juridica.csv',
                'arquivo_csv': base64.encodestring(csv),
            }
            rel_obj.write(dados)

        return True


    def gera_analise_mercado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        rel = Report(u'Análise de Mercado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_analise_mercado.jrxml')
        rel.parametros['META_ID'] = rel_obj.comercial_meta_id.id
        rel.outputFormat = 'pdf'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'analise_mercado_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_acompanhamento_instalacao(self, cr, uid, ids, context={}):
        for rel_obj in self.browse(cr, uid, ids):
            sql = """
            select
                sm.nome || ' - ' || sm.estado as cidade,
                ie.codigo as equipe,
                p.name as cliente,
                cast(cm.data_inicial_prevista at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_inicial_prevista,
                cast(cm.data_final_prevista at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_final_prevista,
                cast(cm.data_confirmacao at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_confirmacao,
                cast(cm.data_conclusao at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_conclusao,
                cm.description as obs

            from
                crm_meeting cm
                join res_partner p on p.id = cm.partner_id
                join sped_municipio sm on sm.id = p.municipio_id
                join instalacao_equipe ie on ie.id = cm.equipe_id

            where
                (cast(cm.data_inicial_prevista at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                or cast(cm.data_final_prevista at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                or cast(cm.data_confirmacao at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                or cast(cm.data_conclusao at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                )
                and sm.id = {municipio_id}

            order by
                1,
                cm.data_inicial_prevista,
                cm.data_final_prevista;
            """

            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'municipio_id': rel_obj.municipio_id.id,
                'filtro_adicional': '',
            }

            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            if not len(dados):
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for cidade, equipe, cliente, data_inicial_prevista, data_final_prevista, data_confirmacao, data_conclusao, obs in dados:
                linha = DicionarioBrasil()
                linha['cidade'] = cidade or ''
                linha['equipe'] = equipe or ''
                linha['cliente'] = cliente or ''
                linha['data_inicial_prevista'] = parse_datetime(data_inicial_prevista) if data_inicial_prevista else None
                linha['data_final_prevista'] = parse_datetime(data_final_prevista) if data_final_prevista else None
                linha['data_confirmacao'] = parse_datetime(data_confirmacao) if data_confirmacao else None
                linha['data_conclusao'] = parse_datetime(data_conclusao) if data_conclusao else None
                linha['obs'] = obs
                linha['iniciado_no_prazo'] = 1 if data_inicial_prevista == data_confirmacao else 0
                linha['concluido_no_prazo'] = 1 if data_final_prevista == data_conclusao else 0
                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.cpc_minimo_detalhe = 4
            rel.monta_contagem = True
            rel.title = u'Acompanhamento de Instalações - ' + cidade

            rel.colunas = [
                ['equipe', 'C', 20, u'Equipe', False],
                ['cliente', 'C', 60, u'Cliente', False],
                ['data_inicial_prevista', 'D', 10, u'Iní. prev.', False],
                ['data_confirmacao', 'D', 10, u'Início', False],
                ['iniciado_no_prazo', 'B', 8, u'No prazo', True],
                ['data_final_prevista', 'D', 10, u'Tér. prev.', False],
                ['data_conclusao', 'D', 10, u'Término', False],
                ['concluido_no_prazo', 'B', 8, u'No prazo', True],
                ['obs', 'C', 60, u'Obs.', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['cidade', u'Cidade', False],
            #]
            #rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'acompanhamento_instalacoes.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'acompanhamento_instalacoes.csv',
                'arquivo_csv': base64.encodestring(csv),
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contas_jasper(self, cr, uid, ids, context={}, tipo='R'):
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

            if len(rel_obj.res_partner_bank_ids):
                texto_filtro = u''
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

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

                   case
                   when l.valor = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   coalesce(l.valor_documento, 0) {rateio} + coalesce(l.valor, 0) {rateio}
                   else
                   coalesce(l.valor, 0.00) {rateio} end as valor,

                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   case 
                   when fc.contrato_atualizado = true then 
                   'CT.ATT. ' || coalesce(p.razao_social, '') || ' | ' || coalesce(p.name, '') || ' | ' || coalesce(p.cnpj_cpf, '')
                   else
                   coalesce(p.razao_social, '') || ' | ' || coalesce(p.name, '') || ' | ' || coalesce(p.cnpj_cpf, '')
                   end as cliente,                   
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   coalesce(p.email_nfe, '') as email_nfe,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   pfc.nome || '/' || cf.nome as conta_nome,
                   l.provisionado,
                   case
                   when l.data_vencimento < current_date then
                   current_date - l.data_vencimento
                   else
                   0 end as data_atraso"""

            if tipo == 'P-R' or tipo == 'R-R':
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
                   left join finan_contrato fc on fc.id = l.contrato_id"""

            if rel_obj.filtrar_rateio or tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            if rel_obj.filtrar_rateio or tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   left join finan_conta cf on cf.id = lr.conta_id
                   left join finan_conta pfc on pfc.id = cf.parent_id"""
            else:
                sql_relatorio += """
                   left join finan_conta cf on cf.id = l.conta_id
                   left join finan_conta pfc on pfc.id = cf.parent_id"""

            if tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""

            if rel_obj.vendedor_id:
                sql_relatorio += """
                    left join finan_contrato contrato on contrato.id = l.contrato_id
                    left join sped_documento nf on nf.id = l.sped_documento_id
                    left join sale_order_sped_documento sosd on sosd.sped_documento_id = nf.id
                    left join sale_order pedido on pedido.id = sosd.sale_order_id
                """

            if situacao < '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in '  +  str(tuple(bancos_ids)).replace(',)', ')')
            elif situacao == '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and exists(
                        select
                            lp.id
                        from
                            finan_lancamento lp
                            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = lp.id
                        where
                            lp.tipo in ('PP', 'PR')
                            and ((ldp.divida_id is null and lp.lancamento_id = l.id) or (ldp.divida_id is not null and ldp.divida_id = l.id))
                            and lp.data_quitacao between '{data_inicial}' and '{data_final}')
                    """

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in'   +  str(tuple(bancos_ids)).replace(',)', ')')
            else:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_documento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

            if rel_obj.dias_atraso:
                sql_relatorio +="""
                    and current_date - l.data_vencimento = """ + str(rel_obj.dias_atraso)

            if rel_obj.vendedor_id:
                sql_relatorio += """
                    and (contrato.vendedor_id = {vendedor_id} or pedido.user_id = {vendedor_id})
                """
                filtro['vendedor_id'] = rel_obj.vendedor_id.id

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """
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

            if rel_obj.agrupa_data_vencimento:
                sql_relatorio += """
                        and l.situacao = 'Vencido'
                        order by c.name, l.situacao, l.data_vencimento desc, p.razao_social, p.name, p.cnpj_cpf, cf.codigo_completo desc;"""
            else:
                sql_relatorio += """
                        order by c.name, l.situacao, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento, cf.codigo_completo desc;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            if tipo == 'R':
                rel = Report('Relatório de Contas a Receber', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_receber.jrxml')
                nome_rel = u'contas_receber.'

                if rel_obj.agrupa_data_vencimento:
                    rel.parametros['AGRUPA_DATA_VENC'] = True

                if rel_obj.formapagamento_id:
                    rel.parametros['FORMA_PAGAMENTO'] = rel_obj.formapagamento_id.nome

            if tipo == 'P':
                rel = Report('Relatório de Contas a Pagar', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_pagar.jrxml')
                nome_rel = u'contas_pagar.'

                if len(rel_obj.res_partner_bank_ids):
                        rel.parametros['BANCO'] = texto_filtro

            if tipo == 'R-R':
                rel = Report('Relatório de Contas a Receber Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_receber_rateio.jrxml')
                nome_rel = u'contas_receber_rateio.'

                if rel_obj.filtrar_rateio:
                    if rel_obj.centrocusto_id:
                        rel.parametros['CENTRO_CUSTO'] = rel_obj.centrocusto_id.nome_completo

                    if rel_obj.project_id:
                        rel.parametros['PROJETO'] = rel_obj.project_id.name

            if tipo == 'P-R':
                rel = Report('Relatório de Contas a Pagar Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_pagar_rateio.jrxml')
                nome_rel = u'contas_pagar_rateio.'

                if len(rel_obj.res_partner_bank_ids):
                        rel.parametros['BANCO'] = texto_filtro

                if rel_obj.filtrar_rateio:
                    if rel_obj.centrocusto_id:
                        rel.parametros['CENTRO_CUSTO'] = rel_obj.centrocusto_id.nome_completo

                    if rel_obj.project_id:
                        rel.parametros['PROJETO'] = rel_obj.project_id.name

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['SQL_RELATORIO'] = sql_relatorio
            rel.parametros['SITUACAO'] = SITUACAO
            if rel_obj.total_empresa:
                rel.parametros['TOTAIS'] = True

            rel.outputFormat = rel_obj.formato

            if rel_obj.partner_id:
                rel.parametros['PARTNER'] = rel_obj.partner_id.name

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_rel + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True
    
    def gera_relatorio_cliente_duvidosos(self, cr, uid, ids, context={}, tipo='R'):
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
            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Clientes Duvidosos'
            
            rel.colunas = [
                ['data_vencimento', 'D', 10, u'Data venc.', False],
                ['data_documento', 'D', 10, u'Data doc.', False],                            
                ['numero_documento', 'C', 15, u'Nº doc.', False],
                ['cliente', 'C', 50, u'Cliente', False],
                ['valor_documento', 'F', 10, u'Valor orig.', True],
                ['dias_atraso', 'I', 6, u'Atraso', True],
            ]   
            rel.monta_detalhe_automatico(rel.colunas)
    
            rel.grupos = [
                ['unidade', u'Unidade', True],
                ['situacao', u'Situação', False],
            ]
            rel.monta_grupos(rel.grupos)          
            
            if len(rel_obj.res_partner_bank_ids):
                texto_filtro = u''
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(l.valor_documento, 0.00) as valor_documento,
                   coalesce(l.valor_desconto, 0.00) as valor_desconto,
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

                   case
                   when l.valor = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado') then
                   coalesce(l.valor_documento, 0) + coalesce(l.valor, 0) 
                   else
                   coalesce(l.valor, 0.00) end as valor,

                   coalesce(l.valor_saldo, 0.00) as valor_saldo,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.name, '') as cliente,
                  
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   pfc.nome || '/' || cf.nome as conta_nome,
                   l.provisionado,
                   case
                   when l.data_vencimento < current_date then
                   current_date - l.data_vencimento
                   else
                   0 end as data_atraso"""          

            sql_relatorio += """
                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id
                   left join finan_conta cf on cf.id = l.conta_id
                   left join finan_conta pfc on pfc.id = cf.parent_id"""
            
            if situacao < '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in '  +  str(tuple(bancos_ids)).replace(',)', ')')
                    
            elif situacao == '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and exists(
                        select
                            lp.id
                        from
                            finan_lancamento lp
                            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = lp.id
                        where
                            lp.tipo in ('PP', 'PR')
                            and ((ldp.divida_id is null and lp.lancamento_id = l.id) or (ldp.divida_id is not null and ldp.divida_id = l.id))
                            and lp.data_quitacao between '{data_inicial}' and '{data_final}')
                    """

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in'   +  str(tuple(bancos_ids)).replace(',)', ')')
                    
            else:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_documento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

            if rel_obj.dias_atraso:
                sql_relatorio +="""
                    and current_date - l.data_vencimento = """ + str(rel_obj.dias_atraso)
           
            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """
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

            sql_relatorio += """
                order by c.name, l.situacao, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento desc, cf.codigo_completo desc, b;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            
            print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            
            for id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, valor_saldo, nosso_numero, cliente,  unidade, situacao, conta_codigo, conta_nome, provisionado, data_atraso in dados:            
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
                linha['cliente'] = cliente
                linha['unidade'] = unidade
                linha['situacao'] = situacao
                linha['conta_codigo'] = conta_codigo
                linha['conta_nome'] = conta_nome
                linha['provisionado'] = provisionado
                linha['dias_atraso'] = data_atraso

                linhas.append(linha)
            rel.band_page_header.elements[-1].text = u'Período ' + parse_datetime(data_inicial).strftime('%d/%m/%Y') + u' a ' + parse_datetime(data_final).strftime('%d/%m/%Y')

            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u', empresa/unidade '
                rel.band_page_header.elements[-1].text += rel_obj.company_id.name
           
            if rel_obj.partner_id:
                if tipo == 'R':
                    rel.band_page_header.elements[-1].text += u', do cliente '
                else:
                    rel.band_page_header.elements[-1].text += u', do fornecedor '

                rel.band_page_header.elements[-1].text += rel_obj.partner_id.name

            if rel_obj.formapagamento_id:
                rel.band_page_header.elements[-1].text += u', forma de pagamento '
                rel.band_page_header.elements[-1].text += rel_obj.formapagamento_id.nome

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'Cliente_Duvidosos.pdf.pdf',
                'arquivo': base64.encodestring(pdf),                
            }
            rel_obj.write(dados)

    def gera_relatorio_contrato_suspenso(self, cr, uid, ids, context={}):
        
        for rel_obj in self.browse(cr, uid, ids):
            sql = """
            select 
                rp.name as empresa,
                cli.numero,
                coalesce(cli.razao_social, cli.name) as nome_cliente,
                cli.cnpj_cpf,
                case when cli.endereco is null then '' else coalesce(cli.endereco,'') || ', ' || coalesce(cli.numero,'') || ', '|| coalesce(cli.bairro,'') || ' - '|| coalesce(cli.cidade,'') || '/' || coalesce(cli.estado,'') end as endereco_cliente,
                case when rpa.endereco is null then '' else coalesce(rpa.endereco,'') || ', ' || coalesce(rpa.numero,'') || ', '|| coalesce(rpa.bairro,'') || ' - '|| coalesce(rpa.cidade,'') || '/' || coalesce(rpa.estado,'') end as endereco_fato,
                cp.data_suspensao,
                cp.data_liberacao
            from finan_contrato cf
                join res_company c on c.id = cf.company_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                join res_partner rp on rp.id = c.partner_id
                join res_partner cli on cli.id = cf.partner_id
                left join res_partner_address rpa on rpa.id = cf.endereco_prestacao_id
                join finan_contrato_suspensao cp on cp.contrato_id = cf.id                
            where
                (cp.data_suspensao between '{data_inicial}' and '{data_final}' 
                  or 
                  cp.data_liberacao between '{data_inicial}' and '{data_final}')
                and (
                    c.id = {company_id}
                    or cc.id = {company_id}
                    or ccc.id = {company_id}
                )
            order by
                 rp.name, cli.name, cp.data_suspensao , cp.data_liberacao
                    """

            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
                'company_id': rel_obj.company_id.id,                
            }

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if not len(dados):
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for empresa, numero, nome_cliente, cnpj_cpf, endereco_cliente, endereco_fato, data_suspensao, data_liberacao in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['numero'] = numero
                linha['nome_cliente'] = nome_cliente
                linha['cnpj_cpf'] = cnpj_cpf
                linha['endereco_cliente'] = endereco_cliente
                linha['endereco_fato'] = endereco_fato
                linha['data_suspensao'] = data_suspensao
                linha['data_liberacao'] = data_liberacao                
                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()            
            rel.title = u'Relatório Contrato Suspensos'
            
            rel.colunas = [
                ['numero', 'C', 10, u'Número', False],
                ['nome_cliente', 'C', 40, u'Clientes', False],
                ['cnpj_cpf', 'C', 15, u'CNPJ/CPF', False],
                ['endereco_cliente', 'C', 60, u'Endereço do Cliente', False],
                ['endereco_fato', 'C', 60, u'Endereço de prestação ', False],
                ['data_suspensao', 'D', 12, u'Data Suspensão', False],
                ['data_liberacao', 'D', 12, u'Data Liberação', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'Contratos_suspensos.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True


    ###def gera_relatorio_fluxo_caixa_analitico(self, cr, uid, ids, context={}):
        ###if not ids:
            ###return False

        ###data_inicial = context['data_inicial']
        ###data_final = context['data_final']
        ###provisionado = context.get('provisionado')

        ###id = ids[0]
        ###rel_obj = self.browse(cr, uid, id)
        ###data_inicial = parse_datetime(rel_obj.data_inicial).date()
        ###data_final = parse_datetime(rel_obj.data_final).date()

        ###filtro = {
            ###'data_inicial': data_inicial,
            ###'data_final': data_final,
        ###}

        ###rel = Report('Fluxo de Caixa', cr, uid)
        ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa

        ####if rel_obj.saldo_inicial:
        ###rel.parametros['SALDO_INICIAL'] = float(rel_obj.saldo_inicial or 0)

        ###rel.outputFormat = rel_obj.formato

        ###if rel_obj.opcoes_caixa == '1':
            ###filtro['tipo'] = "('Q')"
            ###rel.parametros['TIPO'] = "('Q')"
        ###elif rel_obj.opcoes_caixa == '2':
            ###filtro['tipo'] = "('Q','V')"
            ###rel.parametros['TIPO'] = "('Q','V')"
        ###else:
            ###filtro['tipo'] = "('V')"
            ###rel.parametros['TIPO'] = "('V')"

        ###if rel_obj.periodo == '1':
            ###sql_relatorio = """
                ###select
                    ###c.id,
                    ###c.cnpj_cpf,
                    ###c.raiz_cnpj,
                    ###rpc.name as empresa,
                    ###f.mes,
            ###"""

            ###sql_relatorio_SUB = """
                ###select
                    ###f.mes,
            ###"""
        ###else:
            ###sql_relatorio = """
                ###select
                    ###c.id,
                    ###c.cnpj_cpf,
                    ###c.raiz_cnpj,
                    ###rpc.name as empresa,
                    ###f.data,
            ###"""

            ###sql_relatorio_SUB = """
                ###select
                    ###f.data,
            ###"""

        ###sql_relatorio += """
                    ###sum(coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1))  as valor_entrada,
                    ###sum(coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1))  as valor_saida,
                    ###sum(coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1)) - sum(coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1)) as diferenca"""

        ###sql_relatorio_SUB += """
                    ###sum(coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1))  as valor_entrada,
                    ###sum(coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1))  as valor_saida,
                    ###sum(coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1)) - sum(coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1)) as diferenca"""

        ###if rel_obj.periodo == '3':
            ###sql_relatorio += """,
                    ###fd.nome,
                    ###fl.tipo,
                    ###rp.name"""

        ###sql_relatorio += """
                ###from
                    ###finan_fluxo_mensal_diario f

                    ###left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = f.id
                    ###join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = f.lancamento_id)
                    ###left join res_partner rp on rp.id = fl.partner_id
                    ###left join finan_documento fd on fd.id = fl.documento_id
                    ###join finan_conta fc on (fl.tipo != 'T' and fc.id = fl.conta_id) or (fl.tipo = 'T' and fc.id = f.id)

                    ###join res_company c on c.id = fl.company_id
                    ###join res_partner rpc on rpc.id = c.partner_id
        ###"""

        ###sql_relatorio_SUB += """
                ###from
                    ###finan_fluxo_mensal_diario f

                    ###left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = f.id
                    ###join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = f.lancamento_id)
                    ###left join res_partner rp on rp.id = fl.partner_id
                    ###left join finan_documento fd on fd.id = fl.documento_id
                    ###join finan_conta fc on (fl.tipo != 'T' and fc.id = fl.conta_id) or (fl.tipo = 'T' and fc.id = f.id)

                    ###join res_company c on c.id = fl.company_id
                    ###join res_partner rpc on rpc.id = c.partner_id
        ###"""

        ####if rel_obj.periodo == '3' and rel_obj.conta_id:
            ####sql_relatorio += """
            ####"""
            ####sql_relatorio_SUB += """
                    ####left join finan_lancamento_lote_divida_pagamento ldp on ldp.lote_id = fl.id
                    ####left join finan_lancamento divida on divida.id = ldp.divida_id
                    ####left join finan_conta fc on (fc.id = fl.conta_id or fc.id = divida.conta_id)
            ####"""

        ###sql_relatorio += """
                ###where
                    ###f.data between '{data_inicial}' and '{data_final}'
                    ###and f.tipo in {tipo}
        ###"""

        ###sql_relatorio_SUB += """
                ###where
                    ###f.data between '{data_inicial}' and '{data_final}'
                    ###and f.tipo in {tipo}
        ###"""

        ###if len(rel_obj.company_ids) == 1:
            ###filtro['company_id'] = rel_obj.company_ids[0].id
            ###sql_relatorio += """
                     ###and (
                       ###c.id = {company_id}
                       ###or c.parent_id = {company_id}
                    ###)"""
            ###sql_relatorio_SUB += """
                     ###and (
                       ###c.id = {company_id}
                       ###or c.parent_id = {company_id}
                    ###)"""

        ###elif len(rel_obj.company_ids) > 1:
            ###company_ids = []
            ###for company_obj in rel_obj.company_ids:
                ###company_ids.append(company_obj.id)

            ###filtro['company_ids'] = str(tuple(company_ids)).replace(',)', ')')
            ###sql_relatorio += """
                     ###and (
                       ###c.id in {company_ids}
                       ###or c.parent_id in {company_ids}
                    ###)"""
            ###sql_relatorio_SUB += """
                     ###and (
                       ###c.id in {company_ids}
                       ###or c.parent_id in {company_ids}
                    ###)"""
        ###else:
            ###raise osv.except_osv(u'Atenção', u'É preciso selecionar pelo menos uma empresa!')

        ###if len(rel_obj.res_partner_bank_ids) == 1:
            ###filtro['bank_id'] = rel_obj.res_partner_bank_ids[0].id
            ###sql_relatorio += """
                     ###and f.res_partner_bank_id = {bank_id}
            ###"""
            ###sql_relatorio_SUB += """
                     ###and f.res_partner_bank_id = {bank_id}
            ###"""

        ###elif len(rel_obj.res_partner_bank_ids) > 1:
            ###bancos_ids = []
            ###for banco_obj in rel_obj.res_partner_bank_ids:
                ###bancos_ids.append(banco_obj.id)

            ###filtro['bank_ids'] = str(tuple(bancos_ids)).replace(',)', ')')
            ###sql_relatorio += """
                     ###and f.res_partner_bank_id in {bank_ids}
            ###"""
            ###sql_relatorio_SUB += """
                     ###and f.res_partner_bank_id in {bank_ids}
            ###"""

        ###if rel_obj.nao_provisionado != rel_obj.provisionado:
            ###sql_relatorio += """
                    ###and f.provisionado = """ + str(provisionado)

            ###sql_relatorio_SUB += """
                    ###and f.provisionado = """ + str(provisionado)

        ###if rel_obj.conta_id:
            ###sql_relatorio += """
                    ###and fl.conta_id = {conta_id}
            ###"""
            ###sql_relatorio_SUB += """
                    ###and fl.conta_id = {conta_id}
            ###"""
            ###filtro['conta_id'] = rel_obj.conta_id.id

        ###if rel_obj.hr_department_id:
            ###sql_relatorio += """
                    ###and fc.hr_department_id = {hr_department_id}
            ###"""
            ###sql_relatorio_SUB += """
                    ###and fc.hr_department_id = {hr_department_id}
            ###"""
            ###filtro['hr_department_id'] = rel_obj.hr_department_id.id

        ###if rel_obj.periodo == '1':
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###rpc.name,
                    ###f.mes

                ###order by
                    ###c.id,
                    ###f.mes;"""

            ###sql_relatorio_SUB += """
                ###group by
                    ###f.mes

                ###order by
                    ###f.mes;"""

        ###elif rel_obj.periodo == '2':
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###rpc.name,
                    ###f.data

                ###order by
                    ###c.id,
                    ###f.data;"""

            ###sql_relatorio_SUB += """
                ###group by
                    ###f.data

                ###order by
                    ###f.data;"""

        ###else:
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###rpc.name,
                    ###f.data,
                    ###fd.nome,
                    ###fl.tipo,
                    ###rp.name

                ###order by
                    ###c.id,
                    ###f.data,
                    ###valor_entrada desc,
                    ###valor_saida desc;"""

            ###sql_relatorio_SUB += """
                ###group by
                    ###f.data

                ###order by
                    ###f.data,
                    ###valor_entrada desc,
                    ###valor_saida desc;"""


        ###sql = sql_relatorio.format(**filtro)
        ###print(sql)
        ###sql_relatorio_SUB = sql_relatorio_SUB.format(**filtro)

        ###if rel_obj.periodo == '1':
            ###rel.parametros['PERIODO'] = 'MENSAL'
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_mensal_patrimonial.jrxml')
            ###rel.parametros['SQL_RELATORIO'] = sql
            ###rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            ###relatorio = u'fluxo_caixa_mensal_'

        ###elif rel_obj.periodo == '2':
            ###rel.parametros['PERIODO'] = 'DIARIO'
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_diario_patrimonial.jrxml')
            ###rel.parametros['SQL_RELATORIO'] = sql
            ###rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            ###relatorio = u'fluxo_caixa_diario_'

        ###else:
            ###rel.parametros['PERIODO'] = 'ANALITICO'
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_analitico_patrimonial.jrxml')
            ###rel.parametros['SQL_RELATORIO'] = sql
            ###rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            ###relatorio = u'fluxo_caixa_analitico_'

        ###if rel_obj.saldo_bancario:
            ###rel.parametros['SALDO_BANCO'] = True
        ###else:
            ###rel.parametros['SALDO_BANCO'] = False

        ###if rel_obj.zera_saldo:
            ###rel.parametros['ZERA_SALDO'] = True
        ###else:
            ###rel.parametros['ZERA_SALDO'] = False

        ###if rel_obj.somente_totais:
            ###rel.parametros['SOMENTE_TOTAIS'] = True
        ###else:
            ###rel.parametros['SOMENTE_TOTAIS'] = False

        ###pdf, formato = rel.execute()

        ###dados = {
            ###'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            ###'arquivo': base64.encodestring(pdf)
        ###}
        ###rel_obj.write(dados)

        ###return True

    ###def gera_relatorio_fluxo_caixa_sintetico(self, cr, uid, ids, context={}):

        ###if not ids:
            ###return False

        ###provisionado = context.get('provisionado')

        ###id = ids[0]
        ###rel_obj = self.browse(cr, uid, id)
        ####company_id = rel_obj.company_id.id
        ###data_inicial = parse_datetime(rel_obj.data_inicial).date()
        ###data_final = parse_datetime(rel_obj.data_final).date()

        ###meses = tempo(data_inicial,data_final)
        ###print(meses)

        ###if meses.years == 1 and meses.days > 0:
            ###raise osv.except_osv(u'Atenção', u'Limite entre datas é 12 meses!')

        ###if rel_obj.filtrar_rateio:
            ###rel = Report('Fluxo de Caixa', cr, uid)
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico_rateio.jrxml')
            ###rel.parametros['PERIODO'] = 'SINTETICO RATEIO'
            ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico_rateio.jasper'
            ####rel.parametros['COMPANY_ID'] = int(company_id)
            ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            ###relatorio = u'fluxo_caixa_sintetico_conta_rateio_'
            ###rel.outputFormat = rel_obj.formato
        ###else:
            ###rel = Report('Fluxo de Caixa', cr, uid)
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico.jrxml')
            ###rel.parametros['PERIODO'] = 'SINTETICO'
            ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico.jasper'

            ####rel.parametros['COMPANY_ID'] = int(company_id)
            ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            ###relatorio = u'fluxo_caixa_sintetico_conta_'
            ###rel.outputFormat = rel_obj.formato

        ###filtro = {
            ###'data_inicial': str(data_inicial)[:10],
            ###'data_final': str(data_final)[:10],
            ###'filtro_company': '',
            ###'filtro_res_partner_bank': '',
            ####'company_id': int(company_id),
            ####'zera_saldo': str(rel_obj.zera_saldo or False),
            ###'filtro_adicional': """''""",
            ###'titulo_01': '',
            ###'titulo_02': '',
            ###'titulo_03': '',
            ###'titulo_04': '',
            ###'titulo_05': '',
            ###'titulo_06': '',
            ###'titulo_07': '',
            ###'titulo_08': '',
            ###'titulo_09': '',
            ###'titulo_10': '',
            ###'titulo_11': '',
            ###'titulo_12': '',
            ###'ordem_01': '01',
            ###'ordem_02': '02',
            ###'ordem_03': '03',
            ###'ordem_04': '04',
            ###'ordem_05': '05',
            ###'ordem_06': '06',
            ###'ordem_07': '07',
            ###'ordem_08': '08',
            ###'ordem_09': '09',
            ###'ordem_10': '10',
            ###'ordem_11': '11',
            ###'ordem_12': '12',
            ###'setor': '',
        ###}

        ###if rel_obj.opcoes_caixa == '1':
            ###rel.parametros['TIPO'] = 'Q'
            ###filtro['tipo'] = "and fcs.tipo = 'Q'"
        ###elif rel_obj.opcoes_caixa == '2':
            ###rel.parametros['TIPO'] = 'X'
            ###filtro['tipo'] = ""
        ###else:
            ###rel.parametros['TIPO'] = 'V'
            ###filtro['tipo'] = "and fcs.tipo = 'V'"

        ###if len(rel_obj.company_ids) == 1:
            ###rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            ###filtro['filtro_company'] = """
            ###(
                ###fcs.company_id = {company_id}
                ###or c.parent_id = {company_id}
            ###)
            ###""".format(company_id=rel_obj.company_ids[0].id)
            ###filtro['filtro_company_anterior'] = """
            ###and (
                ###pr.company_id = {company_id}
                ###or cc.parent_id = {company_id}
            ###)
            ###""".format(company_id=rel_obj.company_ids[0].id)


        ###elif len(rel_obj.company_ids) > 1:
            ###rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            ###company_ids = []
            ###for company_obj in rel_obj.company_ids:
                ###company_ids.append(company_obj.id)

            ###filtro['filtro_company'] = """
            ###(
                ###fcs.company_id in {company_ids}
                ###or c.parent_id in {company_ids}
            ###)
            ###""".format(company_ids=str(tuple(company_ids)).replace(',)', ')'))
            ###filtro['filtro_company_anterior'] = """
            ###and (
                ###pr.company_id in {company_ids}
                ###or cc.parent_id in {company_ids}
            ###)
            ###""".format(company_ids=str(tuple(company_ids)).replace(',)', ')'))

        ###else:
            ###raise osv.except_osv(u'Atenção', u'É preciso selecionar pelo menos uma empresa!')

        ###if len(rel_obj.res_partner_bank_ids) == 1:
            ###filtro['filtro_res_partner_bank'] = """
                ###and fcs.res_partner_bank_id = {res_partner_bank_id}
            ###""".format(res_partner_bank_id=rel_obj.res_partner_bank_ids[0].id)
            ###filtro['filtro_res_partner_bank_anterior'] = """
                ###and pr.res_partner_bank_id = {res_partner_bank_id}
            ###""".format(res_partner_bank_id=rel_obj.res_partner_bank_ids[0].id)


        ###elif len(rel_obj.res_partner_bank_ids) > 1:
            ###res_partner_bank_ids = []
            ###for res_partner_bank_obj in rel_obj.res_partner_bank_ids:
                ###res_partner_bank_ids.append(res_partner_bank_obj.id)

            ###filtro['filtro_res_partner_bank'] = """
                ###and fcs.res_partner_bank_id in {res_partner_bank_ids}
            ###""".format(res_partner_bank_ids=str(tuple(res_partner_bank_ids)).replace(',)', ')'))
            ###filtro['filtro_res_partner_bank_anterior'] = """
                ###and pr.res_partner_bank_id in {res_partner_bank_ids}
            ###""".format(res_partner_bank_ids=str(tuple(res_partner_bank_ids)).replace(',)', ')'))

        ####if rel_obj.filtrar_rateio:

            ####sql = """
                ####select
                    ####*
                ####from
                    ####finan_analitico_rateio('{data_inicial}', '{data_final}', {company_id}, {zera_saldo}, {filtro_adicional})
            ####"""
            ####if rel_obj.project_id:
                ####filtro['filtro_adicional'] = """' and lr.project_id = """ + str(rel_obj.project_id.id) + """'"""
                ####rel.parametros['PROJETO'] = rel_obj.project_id.name

        ####else:
            ####sql = """
                ####select
                    ####*
                ####from
                    ####finan_analitico('{data_inicial}', '{data_final}', {company_id}, {zera_saldo})
            ####"""


        ####if rel_obj.ativo:
            ####if rel_obj.opcoes_caixa == '1':
                ####sql += """
                    ####where
                        ####(id < 0 or quitado_total > 0)
                ####"""
            ####elif rel_obj.opcoes_caixa == '2':
                ####sql += """
                    ####where
                        ####(id < 0 or ((quitado_total > 0)
                        ####or (vencido_total > 0)))
                ####"""
            ####else:
                ####sql += """
                    ####where
                        ####(id < 0 or vencido_total > 0)
                ####"""
        ###if rel_obj.hr_department_id:
            ###filtro['setor'] = """
            ###and fc.hr_department_id = {hr_department_id}
            ###""".format(hr_department_id=rel_obj.hr_department_id.id)

        ####
        #### Monta os títulos das colunas
        ####
        ###dif = tempo(data_final, data_inicial)
        ###data = data_inicial
        ###i = 1
        ###lista_meses = []
        ###while i <= 12:
            #####
            ##### Relatório por dia
            #####
            ####if (dif.years == 0 and dif.months == 0) and dif.days <= 7:
                ####filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%a %d/%m/%Y')
                ####data += relativedelta(days=+1)
            ####else:
            ###filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%B de %Y')
            ###filtro['ordem_' + formata_data(data, '%m')] = str(i).zfill(2)
            ###data += relativedelta(months=+1)

            ###i += 1

        ###sql = u"""
###drop table if exists finan_relatorio_fluxo_sintetico;
###create table finan_relatorio_fluxo_sintetico as
###select
    ###row_number() over() as id,
    ###fc.codigo_completo as codigo_ordem,
    ###fc.codigo_completo as codigo,
    ###fc.nome as descricao,
    ###cast(case
        ###when fc.tipo = 'R' then 1
        ###when fc.tipo = 'D' then -1
        ###when fc.tipo = 'C' then -1
        ###when fc.tipo = 'A' then -1
        ###when fc.tipo = 'P' then -1
        ###else -1
    ###end as integer) as tipo,
    ###coalesce(fcs.sintetica, False) as sintetica,
###"""
        ####if rel_obj.zera_saldo:
        ###if True:
            ###sql += """
    ###cast(0 as numeric) as quitado_anterior,
    ###cast(0 as numeric) as vencido_anterior,
###"""
        ###else:
            ###sql += """
    ###cast((
        ###select
            ###coalesce(sum(pr.valor), 0.00) as quitado
        ###from finan_pagamento_rateio pr
            ###join finan_conta_arvore ca on ca.conta_id = pr.conta_id
            ###join res_company cc on cc.id = pr.company_id

        ###where
            ###pr.tipo in ('R', 'P', 'E', 'S')
            ###and ca.conta_pai_id = fc.id
            ###and pr.data_quitacao < '{data_inicial}'
            ###{filtro_company_anterior}
            ###{filtro_res_partner_bank_anterior}
    ###) as numeric) as quitado_anterior,
    ###cast(0 as numeric) as vencido_anterior,
###"""

        ###sql += """
    ###cast('{titulo_01}' as varchar) as titulo_01,
    ###cast('{titulo_02}' as varchar) as titulo_02,
    ###cast('{titulo_03}' as varchar) as titulo_03,
    ###cast('{titulo_04}' as varchar) as titulo_04,
    ###cast('{titulo_05}' as varchar) as titulo_05,
    ###cast('{titulo_06}' as varchar) as titulo_06,
    ###cast('{titulo_07}' as varchar) as titulo_07,
    ###cast('{titulo_08}' as varchar) as titulo_08,
    ###cast('{titulo_09}' as varchar) as titulo_09,
    ###cast('{titulo_10}' as varchar) as titulo_10,
    ###cast('{titulo_11}' as varchar) as titulo_11,
    ###cast('{titulo_12}' as varchar) as titulo_12,
    ###cast(sum(coalesce(fcs.quitado_01, 0)) as numeric) as quitado_{ordem_01},
    ###cast(sum(coalesce(fcs.quitado_02, 0)) as numeric) as quitado_{ordem_02},
    ###cast(sum(coalesce(fcs.quitado_03, 0)) as numeric) as quitado_{ordem_03},
    ###cast(sum(coalesce(fcs.quitado_04, 0)) as numeric) as quitado_{ordem_04},
    ###cast(sum(coalesce(fcs.quitado_05, 0)) as numeric) as quitado_{ordem_05},
    ###cast(sum(coalesce(fcs.quitado_06, 0)) as numeric) as quitado_{ordem_06},
    ###cast(sum(coalesce(fcs.quitado_07, 0)) as numeric) as quitado_{ordem_07},
    ###cast(sum(coalesce(fcs.quitado_08, 0)) as numeric) as quitado_{ordem_08},
    ###cast(sum(coalesce(fcs.quitado_09, 0)) as numeric) as quitado_{ordem_09},
    ###cast(sum(coalesce(fcs.quitado_10, 0)) as numeric) as quitado_{ordem_10},
    ###cast(sum(coalesce(fcs.quitado_11, 0)) as numeric) as quitado_{ordem_11},
    ###cast(sum(coalesce(fcs.quitado_12, 0)) as numeric) as quitado_{ordem_12},

    ###cast(sum(
        ###coalesce(fcs.quitado_01, 0)
        ###+ coalesce(fcs.quitado_02, 0)
        ###+ coalesce(fcs.quitado_03, 0)
        ###+ coalesce(fcs.quitado_04, 0)
        ###+ coalesce(fcs.quitado_05, 0)
        ###+ coalesce(fcs.quitado_06, 0)
        ###+ coalesce(fcs.quitado_07, 0)
        ###+ coalesce(fcs.quitado_08, 0)
        ###+ coalesce(fcs.quitado_09, 0)
        ###+ coalesce(fcs.quitado_10, 0)
        ###+ coalesce(fcs.quitado_11, 0)
        ###+ coalesce(fcs.quitado_12, 0)
    ###) as numeric) as quitado_total,
    ###cast(0 as numeric) as percentual_quitado,

    ###cast(sum(coalesce(fcs.vencido_01, 0)) as numeric) as vencido_{ordem_01},
    ###cast(sum(coalesce(fcs.vencido_02, 0)) as numeric) as vencido_{ordem_02},
    ###cast(sum(coalesce(fcs.vencido_03, 0)) as numeric) as vencido_{ordem_03},
    ###cast(sum(coalesce(fcs.vencido_04, 0)) as numeric) as vencido_{ordem_04},
    ###cast(sum(coalesce(fcs.vencido_05, 0)) as numeric) as vencido_{ordem_05},
    ###cast(sum(coalesce(fcs.vencido_06, 0)) as numeric) as vencido_{ordem_06},
    ###cast(sum(coalesce(fcs.vencido_07, 0)) as numeric) as vencido_{ordem_07},
    ###cast(sum(coalesce(fcs.vencido_08, 0)) as numeric) as vencido_{ordem_08},
    ###cast(sum(coalesce(fcs.vencido_09, 0)) as numeric) as vencido_{ordem_09},
    ###cast(sum(coalesce(fcs.vencido_10, 0)) as numeric) as vencido_{ordem_10},
    ###cast(sum(coalesce(fcs.vencido_11, 0)) as numeric) as vencido_{ordem_11},
    ###cast(sum(coalesce(fcs.vencido_12, 0)) as numeric) as vencido_{ordem_12},

    ###cast(sum(
        ###coalesce(fcs.vencido_01, 0)
        ###+ coalesce(fcs.vencido_02, 0)
        ###+ coalesce(fcs.vencido_03, 0)
        ###+ coalesce(fcs.vencido_04, 0)
        ###+ coalesce(fcs.vencido_05, 0)
        ###+ coalesce(fcs.vencido_06, 0)
        ###+ coalesce(fcs.vencido_07, 0)
        ###+ coalesce(fcs.vencido_08, 0)
        ###+ coalesce(fcs.vencido_09, 0)
        ###+ coalesce(fcs.vencido_10, 0)
        ###+ coalesce(fcs.vencido_11, 0)
        ###+ coalesce(fcs.vencido_12, 0)
    ###) as numeric) as vencido_total,
    ###cast(0 as numeric) as percentual_vencido

###from
    ###finan_conta fc
    ###left outer join finan_fluxo_caixa_sintetico fcs on fcs.id = fc.id
    ###left outer join res_company c on c.id = fcs.company_id

###where
    ###{filtro_company}
    ###{filtro_res_partner_bank}
    ###and fcs.data between '{data_inicial}' and '{data_final}'
    ###-- and fc.tipo in ('R', 'D', 'C')
    ###{tipo}
    ###{provisionado}
    ###{setor}

###group by
    ###fc.id,
    ###fc.codigo_completo,
    ###fc.nome,
    ###fcs.sintetica

###order by
    ###fc.codigo_completo,
    ###fc.nome;
        ###"""

        ###if rel_obj.nao_provisionado != rel_obj.provisionado:
            ###if rel_obj.nao_provisionado:
                ###filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = False)'
            ###else:
                ###filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = True)'
        ###else:
            ###filtro['provisionado'] = ''

        ####if rel_obj.nao_provisionado != rel_obj.provisionado:
            ####rel.parametros['PROV'] = True
        ####else:
            ####rel.parametros['PROV'] = False

        ####if rel_obj.saldo_bancario:
            ####rel.parametros['SALDO_BANCO'] = True
        ####else:
            ####rel.parametros['SALDO_BANCO'] = False

        ####if rel_obj.zera_saldo:
            ####rel.parametros['ZERA_SALDO'] = True
        ####else:
            ####rel.parametros['ZERA_SALDO'] = False

        ###sql = sql.format(**filtro)
        ###print(sql)
        ###cr.execute(sql)
        ###cr.commit()

        ###sql_receitas = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###1000000 as id,
    ###'9999999901' as codigo_ordem,
    ###'' as codigo,
    ###'RECEITAS' as descricao,
    ###fc.tipo,
    ###True as sintetica,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.tipo = 1
    ###and fc.sintetica = False

###group by
    ###fc.tipo,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12;
        ###"""
        ###cr.execute(sql_receitas)
        ###cr.commit()

        ###sql_despesas = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###2000000 as id,
    ###'9999999902' as codigo_ordem,
    ###'' as codigo,
    ###'DESPESAS E CUSTOS' as descricao,
    ###fc.tipo,
    ###True as sintetica,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.tipo = -1
    ###and fc.sintetica = False

###group by
    ###fc.tipo,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12;
        ###"""
        ###cr.execute(sql_despesas)
        ###cr.commit()

        ###sql_saldo = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###3000000 as id,
    ###'9999999903' as codigo_ordem,
    ###'' as codigo,
    ###'SALDO FINAL' as descricao,
    ###0,
    ###True as sintetica,
    ###'' as titulo_01,
    ###'' as titulo_02,
    ###'' as titulo_03,
    ###'' as titulo_04,
    ###'' as titulo_05,
    ###'' as titulo_06,
    ###'' as titulo_07,
    ###'' as titulo_08,
    ###'' as titulo_09,
    ###'' as titulo_10,
    ###'' as titulo_11,
    ###'' as titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.id >= 1000000;
        ###"""
        ###cr.execute(sql_saldo)
        ###cr.commit()

        ###sql_acumulado = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###4000000 as id,
    ###'9999999904' as codigo_ordem,
    ###'' as codigo,
    ###'ACUMULADO' as descricao,
    ###0,
    ###True as sintetica,
    ###'' as titulo_01,
    ###'' as titulo_02,
    ###'' as titulo_03,
    ###'' as titulo_04,
    ###'' as titulo_05,
    ###'' as titulo_06,
    ###'' as titulo_07,
    ###'' as titulo_08,
    ###'' as titulo_09,
    ###'' as titulo_10,
    ###'' as titulo_11,
    ###'' as titulo_12,
    ###{saldo_inicial} as quitado_anterior,
    ###fc.vencido_anterior as vencido_anterior,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
    ###) as quitado_01,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
    ###) as quitado_02,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
    ###) as quitado_03,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
    ###) as quitado_04,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
    ###) as quitado_05,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
    ###) as quitado_06,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
    ###) as quitado_07,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
    ###) as quitado_08,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
    ###) as quitado_09,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
    ###) as quitado_10,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
    ###) as quitado_11,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
        ###+ fc.quitado_12
    ###) as quitado_12,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
        ###+ fc.quitado_12
    ###) as quitado_total,
    ###100 as percentual_quitado,

    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
    ###) as vencido_01,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
    ###) as vencido_02,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
    ###) as vencido_03,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
    ###) as vencido_04,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
    ###) as vencido_05,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
    ###) as vencido_06,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
    ###) as vencido_07,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
    ###) as vencido_08,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
    ###) as vencido_09,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
    ###) as vencido_10,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
    ###) as vencido_11,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
        ###+ fc.vencido_12
    ###) as vencido_12,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
        ###+ fc.vencido_12
    ###) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.id = 3000000;
        ###"""

        ###if getattr(rel_obj, 'saldo_inicial', False):
            ###cr.execute(sql_acumulado.format(saldo_inicial=D(rel_obj.saldo_inicial or 0)))

        ###else:
            ###cr.execute(sql_acumulado.format(saldo_inicial='fc.quitado_anterior'))

        ###cr.commit()

        ###if rel_obj.opcoes_caixa != '2':
            ###sql_percentual = """
                ###update finan_relatorio_fluxo_sintetico fc set
                ###percentual_quitado =
                    ###case
                        ###when (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else quitado_total / (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end,

                ###percentual_vencido =
                    ###case
                        ###when (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else vencido_total / (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end

                ###where
                ###fc.id < 1000000;
            ###"""
        ###else:
            ###sql_percentual = """
                ###update finan_relatorio_fluxo_sintetico fc set
                ###percentual_quitado =
                    ###case
                        ###when (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else (quitado_total + vencido_total) / (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end,

                ###percentual_vencido =
                    ###case
                        ###when (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else (vencido_total + vencido_total) / (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end

                ###where
                ###fc.id < 1000000;
            ###"""

        ###cr.execute(sql_percentual)
        ###cr.commit()

        ###sql = """
        ###select
            ###*
        ###from
            ###finan_relatorio_fluxo_sintetico fc

        ###order by
            ###fc.codigo_ordem
        ###"""
        ####print(filtro)
        ###rel.parametros['SQL'] = sql.replace('\n', ' ')

        ###pdf, formato = rel.execute()

        ###dados = {
            ###'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            ###'arquivo': base64.encodestring(pdf)
        ###}
        ###rel_obj.write(dados)

        ###return True


finan_relatorio()
