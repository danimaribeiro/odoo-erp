# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data, primeiro_dia_mes, ultimo_dia_mes
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import *
from finan_contrato.models.sql_contratos import *


class finan_relatorio(osv.osv_memory):
    _name = 'finan.relatorio'
    _inherit = 'finan.relatorio'

    _columns = {
        'vendedor_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'res_partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelese='restrict'),
    }

    def gera_relatorio_analise_contratos(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        texto_filtro = ''
        data_inicial_anterior = data_inicial + relativedelta(months=-1)
        data_inicial_anterior = primeiro_dia_mes(data_inicial_anterior)
        data_final_anterior = ultimo_dia_mes(data_inicial_anterior)

        filtro = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'company_id': company_id,
            'company_ids': company_id,
            'filtro_adicional': '',
            'filtro_adicional_anterior': '',
            'data_inicial_anterior': data_inicial_anterior,
            'data_final_anterior': data_final_anterior,
        }

        if rel_obj.vendedor_id:
            texto_filtro = u'Vendedor: ' + rel_obj.vendedor_id.name
            filtro['filtro_adicional'] = """and exists(
                select fcv.id
                from finan_contrato_vendedor fcv
                where fcv.contrato_id = fc.id
                and fcv.vendedor_id = {vendedor_id}
                and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
            )""".format(vendedor_id=rel_obj.vendedor_id.id, **filtro)
            filtro['filtro_adicional_anterior'] = """and exists(
                select fcv.id
                from finan_contrato_vendedor fcv
                where fcv.contrato_id = fc.id
                and fcv.vendedor_id = {vendedor_id}
                and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial_anterior}', '{data_final_anterior}')
            )""".format(vendedor_id=rel_obj.vendedor_id.id, **filtro)

        if rel_obj.hr_department_id:
            if len(texto_filtro) > 0:
                texto_filtro += u'; '

            texto_filtro += u'Posto: ' + rel_obj.hr_department_id.name
            filtro['filtro_adicional'] += 'and fc.hr_department_id = ' + str(rel_obj.hr_department_id.id)
            filtro['filtro_adicional_anterior'] += 'and fc.hr_department_id = ' + str(rel_obj.hr_department_id.id)

        if rel_obj.res_partner_category_id:
            if len(texto_filtro) > 0:
                texto_filtro += u'; '

            texto_filtro += u'Categoria: ' + rel_obj.res_partner_category_id.name
            filtro['filtro_adicional'] += 'and fc.res_partner_category_id = ' + str(rel_obj.res_partner_category_id.id)
            filtro['filtro_adicional_anterior'] += 'and fc.res_partner_category_id = ' + str(rel_obj.res_partner_category_id.id)

        if rel_obj.grupo_economico_id:
            if len(texto_filtro) > 0:
                texto_filtro += u'; '

            texto_filtro += u'Grupo econômico: ' + rel_obj.grupo_economico_id.nome
            filtro['filtro_adicional'] += 'and fc.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)
            filtro['filtro_adicional_anterior'] += 'and fc.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)

        rel = Report('Analise de Contratos', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_analise_contratos.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['IS_SINTETICO'] = rel_obj.tipo_rel
        rel.parametros['SQL_CONTRATOS_REGULARES'] = SQL_CONTRATOS_REGULARES.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_NOVOS'] = SQL_CONTRATOS_NOVOS.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_RESCINDIDOS'] = SQL_CONTRATOS_RESCINDIDOS.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_FATURAMENTO_AVULSO'] = SQL_FATURAMENTO_AVULSO.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_BAIXADOS'] = SQL_CONTRATOS_BAIXADOS.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_PROVISIONADOS'] = SQL_CONTRATOS_PROVISIONADOS.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_DIFERENCA_MESES'] = SQL_CONTRATOS_DIFERENCA_MESES.format(**filtro).replace('\n', ' ')
        rel.parametros['FILTRO_ADICIONAL'] = texto_filtro
        #rel.parametros['SQL_CONTRATOS_REGULARES_ANTERIOR'] = SQL_CONTRATOS_REGULARES_ANTERIOR.format(**filtro).replace('\n', ' ')
        #rel.parametros['SQL_CONTRATOS_NOVOS_ANTERIOR'] = SQL_CONTRATOS_NOVOS_ANTERIOR.format(**filtro).replace('\n', ' ')
        #rel.parametros['SQL_CONTRATOS_RESCINDIDOS_ANTERIOR'] = SQL_CONTRATOS_RESCINDIDOS_ANTERIOR.format(**filtro).replace('\n', ' ')
        #rel.parametros['SQL_CONTRATOS_BAIXADOS_ANTERIOR'] = SQL_CONTRATOS_BAIXADOS_ANTERIOR.format(**filtro).replace('\n', ' ')

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Analise_Contratos_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


    def gera_relatorio_contratos_baixados(self, cr, uid, ids, context={}):
        if not ids:
            return {}


        for rel_obj in self.browse(cr, uid, ids):

            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            sql = """
                select
                    co.name,
                    mb.nome as motivo_baixa,
                    fl.data_baixa as data_baixa,
                    fc.numero as numero_contrato,
                    rp.name as cliente,
                    coalesce(fl.valor_original_contrato, 0) as valor_contrato,
                    fl.valor_documento as valor_baixado,
                    fl.data_vencimento

                from
                    finan_lancamento fl
                    join finan_contrato fc on fc.id = fl.contrato_id
                    join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id
                    join res_partner rp on rp.id = fl.partner_id

                    join res_company c on c.id = fl.company_id
                    join res_partner co on co.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id


                where
                    fl.data_baixa between '{data_inicial}' and '{data_final}'
                    and (
                        c.id = {company_id}
                        or cc.id = {company_id}
                        or ccc.id = {company_id}
                    )
                    and fc.natureza = 'R' """


            if rel_obj.partner_id:
                sql += """
                        and rp.id = """  + str(rel_obj.partner_id.id)

            sql += """
                    order by
                        co.name,
                        mb.nome,
                        rp.name;
                    """

            sql = sql.format(company_id=company_id, data_inicial=formata_data(data_inicial), data_final=formata_data(data_final))
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for empresa, motivo_baixa, data_baixa, numero_contrato, cliente, valor_contrato, valor_baixado, data_vencimento in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['motivo_baixa'] = motivo_baixa

                linha['data_baixa'] = formata_data(data_baixa)
                linha['numero_contrato'] = numero_contrato
                linha['cliente'] = cliente
                linha['valor_contrato'] = valor_contrato
                linha['valor_baixado'] = valor_baixado
                linha['data_vencimento'] = formata_data(data_vencimento)
                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Contratos Baixados.'

            rel.colunas = [
                ['data_baixa', 'D', 10, u'Dt. Baixa', False],
                ['numero_contrato', 'C', 15, u'Nº Contrato', False],
                ['cliente', 'C', 40, u'Cliente', False],
                ['valor_contrato', 'F', 10, u'Vlr. Contrato', True],
                ['valor_baixado', 'F', 10, u'Vlr. Baixado', True],
                ['data_vencimento', 'D', 10, u'Dt. Venc.', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
                ['motivo_baixa', u'Motivo Baixa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = company_obj.name + u' DATA ' + parse_datetime(data_inicial).strftime('%d/%m/%Y') + u' - ' + parse_datetime(data_final).strftime('%d/%m/%Y')

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'Contratos_baixados_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contratos_fornecedores(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        rel = FinanRelatorioAutomaticoPaisagem()
        rel.title = u'Parcelas de Contratos de Fornecedores'
        rel.cpc_minimo_detalhe = 4
        
        sql = '''
            select
                case
                    when l.provisionado = True then 'Provisionado'
                    when l.sped_documento_id is not null then 'Realizado'
                    when l.situacao = 'Quitado' then 'Realizado'
                    else 'Provisionado'
                end as prov,
                case
                    when l.provisionado = True then l.data_vencimento_original
                    else l.data_vencimento
                end as data_vencimento,
                p.name as fornecedor,
                l.numero_documento,
                l.valor_original_contrato,
                case
                    when l.provisionado = True then 0
                    when l.sped_documento_id is not null then d.vr_nf
                    when l.situacao = 'Quitado' then l.valor_documento
                    else 0
                end as valor_documento,
                ct.data_assinatura,
                coalesce(ct.data_distrato, ct.data_renovacao) as data_fim                
                
            from
                finan_lancamento l
                join res_company c on c.id = l.company_id
                join res_partner p on p.id = l.partner_id
                left join sped_documento d on d.id = l.sped_documento_id
                join finan_contrato ct on ct.id = l.contrato_id
                
            where
                l.tipo = 'P'
                and (c.id = {company_id} or c.parent_id = {company_id})
                and l.data_vencimento between '{data_inicial}' and '{data_final}'
                {filtro_adicional}
                
            order by
                1,
                2,
                p.name,
                l.numero_documento_original
        '''
        
        filtro = {
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
            'company_id': rel_obj.company_id.id,
            'filtro_adicional': '',
        }
        
        if rel_obj.partner_id:
            filtro['filtro_adicional'] = ' and l.partner_id = ' + str(rel_obj.partner_id.id)
            
        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        
        if not len(dados):
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        for prov, data_vencimento, fornecedor, numero_documento, valor_original_contrato, valor_documento, data_inicio, data_fim in dados:
            linha = DicionarioBrasil()
            
            linha['prov'] = prov
            linha['fornecedor'] = fornecedor
            linha['numero_documento'] = numero_documento
            linha['data_vencimento'] = parse_datetime(data_vencimento).date()
            linha['valor_original_contrato'] = D(valor_original_contrato or 0)
            linha['valor_documento'] = D(valor_documento or 0)
            linha['data_inicio'] = None
            linha['data_fim'] = None
            
            if data_inicio:
                linha['data_inicio'] = parse_datetime(data_inicio)
            
            if data_fim:
                linha['data_fim'] = parse_datetime(data_fim)
                
            linhas.append(linha)
        
        rel.colunas = [
            ['fornecedor', 'C', 60, u'Fornecedor', False],
            ['data_inicio', 'D', 10, u'Início', False],
            ['data_fim', 'D', 10, u'Término', False],
            ['numero_documento', 'C', 30, u'Nº documento', False],
            ['data_vencimento', 'D', 10, u'Vencimento', False],
            ['valor_original_contrato', 'F', 10, u'Valor prov.', True],
            ['valor_documento', 'F', 10, u'Valor realizado', True],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['prov', u'Situação', False],
        ]
        rel.monta_grupos(rel.grupos)

        rel.band_page_header.elements[-1].text = u'Empresa/unidade ' + rel_obj.company_id.name

        rel.band_page_header.height += 18
        rel.band_page_header.elements[-1].text += u'<br/>Período de ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)
        
        if rel_obj.partner_id:
            rel.band_page_header.elements[-1].text += u'<br/>Fornecedor ' + rel_obj.partner_id.name
        
        pdf = gera_relatorio(rel, linhas)

        dados = {
            'nome': 'contratos_fornecedores.pdf',
            'arquivo': base64.encodestring(pdf),
        }
        rel_obj.write(dados)

        return True
        
        
finan_relatorio()
