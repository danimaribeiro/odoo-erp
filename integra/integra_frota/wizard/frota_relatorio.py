# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora, data_hora_horario_brasilia, formata_data, idade_meses_sem_dia, UTC
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from finan.wizard.finan_relatorio import Report, cm
from pybrasil.valor.decimal import Decimal as D
from StringIO import StringIO
from PyPDF2 import PdfFileWriter, PdfFileReader


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)


class frota_relatorio(osv.Model):
    _name = 'frota.relatorio'
    _description = u'Relatórios de Frota'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        
        'data_hora_inicial': fields.datetime(u'Data inicial'),
        'data_hora_final': fields.datetime(u'Data final'),
        
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'hr_employee_id': fields.many2one('hr.employee', u'Empregado/motorista'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'servico_id': fields.many2one('frota.servico', u'Serviço/atividade'),
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo'),
        'tipo_id': fields.many2one('frota.tipo', 'Tipo'),
        'partner_id': fields.many2one('res.partner', u'Fornecedor'),
        'sintetico': fields.boolean(u'Sintético?'),
        'todos': fields.boolean(u'Todos?'),
        'servico_ids': fields.many2many('frota.servico', 'frota_relatorio_servico_incluido', 'relatorio_id', 'servico_id', string=u'Serviços/atividades'),
        'servico_excluido_ids': fields.many2many('frota.servico', 'frota_relatorio_servico_excluido', 'relatorio_id', 'servico_id', string=u'Serviços excluídos'),
        'incluir_abastecimento': fields.boolean(u'Incluir abastecimento?'),
        'incluir_lavacao': fields.boolean(u'Incluir lavação?'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'frota.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'nome': '',
        'formato': 'pdf',
        'sintetico': True,
        'todos': True,
        'servico_excluido_ids': lambda self, cr, uid, context: self.pool.get('frota.servico').search(cr, 1, [('custo_ativo', '=', False)])
    }

    def gera_relatorio_km_rodado(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            filtro = {
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            sql = """
                select
                    rp.name,
                    fo.veiculo_id,
                    t.nome as tipo,
                    fv.placa,
                    coalesce(sum(fo.valor_atual - fo.valor_anterior),0) as valor,
                    coalesce((
                        select
                            sum(coalesce(os.quantidade_combustivel, 0))
                        from
                            frota_os os
                            join frota_os_item foi on foi.os_id = os.id
                            join frota_servico fis on fis.id = foi.servico_id
                            join res_company cq on cq.id = os.res_company_id
                            left join res_company ccq on ccq.id = cq.parent_id

                        where
                            os.state = 'F'
                            and fis.nome = 'ABASTECIMENTO'
                            and os.quantidade_combustivel > 0
                            and cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                            and os.veiculo_id = fo.veiculo_id
                            {filtro_company}
                    ), 0) as quantidade,
                    coalesce((
                        select
                            sum(coalesce(os.valor_combustivel, 0))
                        from
                            frota_os os
                            join frota_os_item foi on foi.os_id = os.id
                            join frota_servico fis on fis.id = foi.servico_id
                            join res_company cq on cq.id = os.res_company_id
                            left join res_company ccq on ccq.id = cq.parent_id

                        where
                            os.state = 'F'
                            and fis.nome = 'ABASTECIMENTO'
                            and os.quantidade_combustivel > 0
                            and cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                            and os.veiculo_id = fo.veiculo_id
                            {filtro_company}
                    ), 0) as valor_combustivel,
                    coalesce((
                        select
                            sum(coalesce(os.valor, 0))
                        from
                            frota_os os
                            join frota_os_item foi on foi.os_id = os.id
                            join frota_servico fis on fis.id = foi.servico_id
                            join res_company cq on cq.id = os.res_company_id
                            left join res_company ccq on ccq.id = cq.parent_id

                        where
                            os.state = 'F'
                            and fis.nome != 'ABASTECIMENTO'
                            and cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                            and os.veiculo_id = fo.veiculo_id
                            {filtro_company}
                    ), 0) as valor_servicos

                from
                    frota_odometro fo
                    join frota_veiculo fv on fv.id = fo.veiculo_id
                    join res_company c on c.id = fv.res_company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id
                    left join frota_servico s on s.id = fo.servico_id
                    join frota_modelo m on m.id = fv.modelo_id
                    join frota_tipo t on t.id = m.tipo_id
                    left join hr_employee e on e.id = fo.hr_employee_id

                where
                    cast(fo.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                    and (fo.servico_id is null or (s.ignora_km is null or s.ignora_km = False))
                    and fo.data_fechamento is not null
            """

            filtro_company = ''
            if rel_obj.company_id:
                sql += """
                    and
                    (
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )
                """.format(company_id=rel_obj.company_id.id)

                filtro_company = """
                    and (
                        cq.id = {company_id}
                        or cq.parent_id = {company_id}
                        or ccq.parent_id = {company_id}
                    )
                """.format(company_id=rel_obj.company_id.id)

            filtro['filtro_company'] = filtro_company

            if rel_obj.veiculo_id:
                sql += """
                    and fo.veiculo_id = {veiculo_id}
                """
                filtro['veiculo_id'] = rel_obj.veiculo_id.id

            if rel_obj.hr_employee_id:
                sql += """
                    and e.id = {employee_id}
                """
                filtro['employee_id'] = rel_obj.hr_employee_id.id

            sql += """
                group by
                    rp.id, t.nome, fo.veiculo_id, fv.placa

                order by
                    --rp.name, t.nome, fv.placa
                    t.nome, fv.placa
            """

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            linhas = []
            veiculo_ids = []
            for empresa, veiculo_id, tipo, placa, valor, quantidade, valor_combustivel, valor_servicos in dados:
                linha = DicionarioBrasil()
                veiculo_ids.append(veiculo_id)
                linha['empresa'] = empresa
                linha['tipo'] = tipo
                linha['placa'] = placa
                linha['valor'] = valor
                linha['quantidade'] = quantidade
                linha['valor_combustivel'] = valor_combustivel
                linha['valor_servicos'] = valor_servicos
                linha['media'] = D(0)
                linha['media_valor_combustivel'] = D(0)
                #linha['numero_os'] = ''
                linha['valor_total'] = D(valor_combustivel or 0) + D(valor_servicos or 0)

                if quantidade > 0:
                    linha['media'] = D(valor or 0) / D(quantidade or 1)

                if valor > 0:
                    linha['media_valor_combustivel'] = D(valor_combustivel) / D(valor or 1)

                linhas.append(linha)

            ###
            ### Agora, vamos pegar os veículos que têm OS mas não têm registro
            ### de odômetro
            ###
            ##if rel_obj.sintetico:
                ##sql = """
                    ##select
                        ##t.nome as tipo,
                        ##fv.placa as placa,
                        ##fo.quantidade_combustivel as quantidade,
                        ##fo.id as numero_os,
                        ##to_char(fo.data at time zone 'UTC' at time zone 'America/Sao_Paulo', 'dd/mm/yyyy') as data_os

                    ##from
                        ##frota_os fo
                        ##join frota_veiculo fv on fv.id = fo.veiculo_id
                        ##join frota_os_item foi on foi.os_id = fo.id
                        ##join frota_servico fis on fis.id = foi.servico_id
                        ##join res_company c on c.id = fo.res_company_id
                        ##left join res_company cc on cc.id = c.parent_id
                        ##join frota_modelo m on m.id = fv.modelo_id
                        ##join frota_tipo t on t.id = m.tipo_id

                    ##where
                        ##cast(fo.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                        ##and fis.nome = 'ABASTECIMENTO'
                        ##and fo.state = 'F'
                        ##and fo.quantidade_combustivel > 0
                        ##--and
                        ##--(
                        ##--    c.id = {company_id}
                        ##--    or c.parent_id = {company_id}
                        ##--    or cc.parent_id = {company_id}
                        ##--)
                ##"""

                ##if len(veiculo_ids):
                    ##filtro['veiculo_ids'] = str(veiculo_ids).replace(']', ')').replace('[', '(')
                    ##sql += """
                        ##and fo.veiculo_id not in {veiculo_ids}
                    ##"""

                ##if rel_obj.veiculo_id:
                    ##sql += """
                        ##and fo.veiculo_id = {veiculo_id}
                    ##"""
                    ##filtro['veiculo_id'] = rel_obj.veiculo_id.id

                ##sql += """
                    ##order by
                        ##t.nome,
                        ##fv.placa
                ##"""

                ##sql = sql.format(**filtro)
                ##print(sql)
                ##cr.execute(sql)

                ##dados = cr.fetchall()
                ##for tipo, placa, quantidade, numero_os, data_os in dados:
                    ##linha = DicionarioBrasil()
                    ##linha['empresa'] = u'Veículos com OS de abastecimento, sem registro de odômetro'
                    ##linha['tipo'] = tipo
                    ##linha['placa'] = placa
                    ##linha['valor'] = D(0)
                    ##linha['quantidade'] = quantidade
                    ##linha['media'] = D(0)
                    ##linha['valor_combustivel'] = D(0)
                    ##linha['media_valor_combustivel'] = D(0)
                    ##linha['numero_os'] = str(numero_os)
                    ##linha['data_os'] = data_os
                    ##linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Km Rodados'
            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Período de '
            filtro.text += formata_data(data_inicial)
            filtro.text += u' a '
            filtro.text += formata_data(data_final)

            if rel_obj.company_id:
                filtro.text += u'; Empresa/unidade: ' + rel_obj.company_id.name

            if rel_obj.hr_employee_id:
                filtro.text += u'; motorista: ' + rel_obj.hr_employee_id.nome

            if rel_obj.sintetico:
                rel.colunas = [
                    ['placa', 'C', 15, u'Veículo', False],
                    ['valor', 'F', 15, u'km rodado', True],
                    ['quantidade', 'F', 15, u'Litros', True],
                    ['media', 'F', 15, u'km/L', False],
                    ['media_valor_combustivel', 'F', 15, u'R$/km', False],
                    ['valor_combustivel', 'F', 15, u'Total abastecimento', True],
                    #['valor_servicos', 'F', 15, u'Outros serviços', True],
                    #['valor_total', 'F', 15, u'Total geral', True],
                    #['numero_os', 'C', 7, u'OS', False],
                    #['data_os', 'C', 10, u'Data OS', False],
                ]
            else:
                rel.colunas = [
                    ['placa', 'C', 15, u'Código do Veículo', False],
                    ['valor', 'F', 15, u'km rodado', True],
                    #['numero_os', 'C', 7, u'OS', False],
                    #['data_os', 'C', 10, u'Data OS', False],
                ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                #['empresa', u'Empresa', False],
                ['tipo', u'Tipo', False],
            ]
            rel.monta_grupos(rel.grupos)

            #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            #rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'km_rodado_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'km_rodado_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_os_veiculo(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Frota Ordem de Serviço por Veículo', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'frota_os_veiculo.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]

        if rel_obj.servico_id:
            rel.parametros['SERVICO_ID'] = rel_obj.servico_id.id
        else:
            rel.parametros['SERVICO_ID'] = '%'

        if rel_obj.veiculo_id:
            rel.parametros['VEICULO_ID'] = rel_obj.veiculo_id.id
        else:
            rel.parametros['VEICULO_ID'] = '%'

        if rel_obj.tipo_id:
            rel.parametros['TIPO_ID'] = rel_obj.tipo_id.id
        else:
            rel.parametros['TIPO_ID'] = '%'

        if rel_obj.sintetico:
            rel.parametros['SINTETICO'] = '1'
        else:
            rel.parametros['SINTETICO'] = '0'

        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'frota_os_veiculos.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_os_fornecedor(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Frota Ordem de Serviço por Fornecedor', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'frota_os_fornecedor.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]

        if rel_obj.servico_id:
            rel.parametros['SERVICO_ID'] = rel_obj.servico_id.id
        else:
            rel.parametros['SERVICO_ID'] = '%'

        if rel_obj.partner_id:
            rel.parametros['FORNECEDOR_ID'] = rel_obj.partner_id.id
        else:
            rel.parametros['FORNECEDOR_ID'] = '%'

        if rel_obj.tipo_id:
            rel.parametros['TIPO_ID'] = rel_obj.tipo_id.id
        else:
            rel.parametros['TIPO_ID'] = '%'

        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'frota_os_fornecedor.' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_justificativa_km(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        company_obj = rel_obj.company_id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        meses = idade_meses_sem_dia(data_inicial, data_final)
        dia_corte = data_inicial.day

        sql = """
            select
                pr.name as proprietario,
                srv.nome as servico,
                cast(od.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_fechamento,
                coalesce(od.distancia, 0) as distancia,
                e.nome as motorista

            from
                frota_odometro od
                join frota_servico srv on srv.id = od.servico_id
                join frota_servico srv_pai on srv_pai.id = srv.parent_id
                join frota_veiculo fv on fv.id = od.veiculo_id
                join res_company c on c.id = fv.res_company_id
                join res_partner rp on rp.id = c.partner_id
                left join res_partner pr on (fv.proprietario_id is not null and pr.id = fv.proprietario_id) or (fv.proprietario_id is null and pr.id = c.partner_id)
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                left join hr_employee e on od.hr_employee_id = e.id

            where
                cast(od.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                and srv_pai.nome like 'OCORR%'
                and (srv.ignora_km is null or srv.ignora_km = False)
        """

        if rel_obj.company_id:
            sql += """
                and (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                )
            """.format(company_id=rel_obj.company_id.id)

        if rel_obj.hr_employee_id:
            sql += """
            and e.id = {employee_id}

            order by
                e.nome,
                pr.name,
                srv.nome
            """.format(employee_id=rel_obj.hr_employee_id.id)

        else:
            sql += """
            order by
                pr.name,
                srv.nome
            """

        sql = sql.format(data_inicial=str(data_inicial), data_final=str(data_final))
        #print(sql)
        cr.execute(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existem dados com os parâmetros informados!')

        colunas = {}
        linhas = {}
        total_geral = D(0)

        #
        # Acumulamos as linhas e colunas das datas
        #
        for proprietario, servico, data_fechamento, distancia, motorista in dados:
            chave = proprietario + '_' + servico
            if chave not in linhas:
                linha = DicionarioBrasil()
                linha['total'] = D(0)
                linha['servico'] = servico
                linha['proprietario'] = proprietario
                linha['chave'] = chave
                linha['motorista'] = motorista
                linhas[chave] = linha

            linha = linhas[chave]

            data_fechamento = parse_datetime(data_fechamento).date()
            #
            # Qual o mês que vai entrar?
            #
            if data_fechamento.day < dia_corte:
                data_fechamento += relativedelta(day=1)
                data_fechamento += relativedelta(months=-1)
                nome_mes = formata_data(data_fechamento, 'mes_%Y_%m')
            else:
                data_fechamento += relativedelta(day=1)
                nome_mes = formata_data(data_fechamento, 'mes_%Y_%m')

            if nome_mes not in linha:
                linha[nome_mes] = D(0)

            if nome_mes not in colunas:
                colunas[nome_mes] = formata_data(data_fechamento, '%b')
                colunas[nome_mes] += '/' + formata_data(data_fechamento + relativedelta(months=1), '%b')

            linha[nome_mes] += D(distancia)
            linha['total'] += D(distancia)
            total_geral += D(distancia)

        colunas_ordem = colunas.keys()
        colunas_ordem.sort()
        #
        # Agora, calculamos o % de cada mês frente ao total
        #
        for chave in linhas:
            linha = linhas[chave]

            for mes in colunas_ordem:
                if mes not in linha:
                    linha[mes] = D(0)

                distancia_mes = linha[mes]
                percentual = D(0)

                if total_geral > 0 and distancia_mes > 0:
                    percentual = distancia_mes / total_geral * D(100)
                    percentual = percentual.quantize(D('0.01'))

                linha[mes + '_percentual'] = percentual

        #
        # Agora, colocamos as colunas que serão impressas, na ordem dos meses
        #
        rel = FinanRelatorioAutomaticoPaisagem()
        rel.title = u'Justificativa de Quilometragem'
        filtro = rel.band_page_header.elements[-1]
        filtro.text = 'De '
        filtro.text += formata_data(data_inicial)
        filtro.text += ' a '
        filtro.text += formata_data(data_final)

        if rel_obj.company_id:
            filtro.text += u', empresa/Unidade ' + company_obj.name

        if rel_obj.hr_employee_id:
            filtro.text += u', motorista ' + rel_obj.hr_employee_id.nome

        rel.colunas = [
            ['servico', 'C', 30, u'Ocorrência', False],
        ]

        for mes in colunas_ordem:
            rel.colunas += [[mes, 'F', 10, colunas[mes], True]]
            rel.colunas += [[mes + '_percentual', 'F', 5, '%', False]]

        rel.colunas += [['total', 'F', 12, 'Total', True]]

        rel.monta_detalhe_automatico(rel.colunas)

        if rel_obj.hr_employee_id:
            rel.grupos = [
                ['motorista', u'Motorista', False],
                ['proprietario', u'Proprietário', False],
            ]

        else:
            rel.grupos = [
                ['proprietario', u'Proprietário', False],
            ]

        rel.monta_grupos(rel.grupos)

        linhas_impressas = []
        servicos_ordem = linhas.keys()
        servicos_ordem.sort()
        for servico in servicos_ordem:
            linhas_impressas.append(linhas[servico])

        pdf = gera_relatorio(rel, linhas_impressas)
        csv = gera_relatorio_csv(rel, linhas_impressas)

        dados = {
            'nome': 'justificativa_km_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'justificativa_km_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
            'arquivo_csv': base64.encodestring(csv)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_custo_imobilizado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        filtro = {
            'data_inicial': str(data_inicial),
            'data_final': str(data_final),
        }
        texto_filtro = u'Período de '
        texto_filtro += formata_data(data_inicial)
        texto_filtro += u' a '
        texto_filtro += formata_data(data_final)

        sql = """
            select
                t.nome as tipo,
                vei.placa as veiculo,
                srv.nome as servico,
                cast(to_char(cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm-01') as date) as mes,
                sum(coalesce(osi.valor, 0)) as valor

            from
                frota_os os
                join frota_veiculo vei on vei.id = os.veiculo_id
                join frota_os_item osi on osi.os_id = os.id
                join frota_servico srv on srv.id = osi.servico_id
                left join res_company c on c.id = os.res_company_id
                join frota_modelo m on m.id = vei.modelo_id
                join frota_tipo t on t.id = m.tipo_id
                left join hr_employee e on os.hr_employee_id = e.id

            where
                cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                and os.state = 'F'
        """

        if rel_obj.tipo_id:
            filtro['tipo_id'] = rel_obj.tipo_id.id
            sql += """
                and t.id = {tipo_id}
            """
            texto_filtro += u'; Tipo: '
            texto_filtro += rel_obj.tipo_id.nome

        if rel_obj.veiculo_id:
            filtro['veiculo_id'] = rel_obj.veiculo_id.id
            sql += """
                and os.veiculo_id = {veiculo_id}
            """
            texto_filtro += u'; Veículo: '
            texto_filtro += rel_obj.veiculo_id.placa

        if rel_obj.company_id:
            filtro['company_id'] = rel_obj.company_id.id
            sql += """
                and (
                    os.res_company_id = {company_id}
                  or c.parent_id = {company_id}
                )
            """
            texto_filtro += u'; Empresa: '
            texto_filtro += rel_obj.company_id.name

        if rel_obj.hr_employee_id:
            filtro['employee_id'] = rel_obj.hr_employee_id.id
            sql += """
                and e.id = {employee_id}
            """
            texto_filtro += u'; Motorista: '
            texto_filtro += rel_obj.hr_employee_id.nome

        if (not rel_obj.partner_id) and (not rel_obj.todos):
            texto_filtro += u'; Somente veículos próprios'
            sql += "and vei.proprietario_id is null"

        elif rel_obj.partner_id:
            texto_filtro += u'; Propriedade de: '
            texto_filtro += rel_obj.partner_id.razao_social.strip()
            texto_filtro += u' - '
            texto_filtro += rel_obj.partner_id.cnpj_cpf
            filtro['proprietario_id'] = rel_obj.partner_id.id
            sql += """
                and vei.proprietario_id = {proprietario_id}
            """

        if len(rel_obj.servico_excluido_ids):
            servico_excluido_ids = []

            for servico_obj in rel_obj.servico_excluido_ids:
                if rel_obj.incluir_abastecimento and u'ABASTECIMENTO' in servico_obj.nome.upper():
                    continue
                if rel_obj.incluir_lavacao and u'LAVAÇÃO' in servico_obj.nome.upper():
                    continue

                servico_excluido_ids.append(servico_obj.id)

            filtro['servico_excluido_ids'] = str(servico_excluido_ids).replace(']', ')').replace('[', '(')
            sql += """
                and srv.id not in {servico_excluido_ids}
            """
        else:
            if not rel_obj.incluir_abastecimento:
                sql += """
                    and srv.nome != 'ABASTECIMENTO' 
                """
            if not rel_obj.incluir_lavacao:
                sql += """
                    and srv.nome != 'LAVAÇÃO' 
                """
        
        sql_grafico = sql    
        sql += """
            group by
                t.nome,
                vei.placa,
                srv.nome,
                mes

            order by
                t.nome,
                vei.placa,
                srv.nome,
                mes;
        """
        
        sql_grafico +="""
            group by
                t.nome,
                mes,
                vei.placa,
                srv.nome

            order by
                t.nome,
                mes,
                vei.placa,
                srv.nome;
        """
         
        sql = sql.format(**filtro)
        print(sql)
        sql_grafico = sql_grafico.format(**filtro)        
        cr.execute(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existem dados com os parâmetros informados!')

        colunas = {}
        linhas = {}
        total_geral = D(0)
        total_meses = {}

        #
        # Acumulamos as linhas e colunas das datas
        #
        for tipo, veiculo, servico, data_os, valor in dados:
            chave = tipo + '|' + veiculo + '|' + servico
            if chave not in linhas:
                linha = DicionarioBrasil()
                linha['total'] = D(0)
                linha['veiculo'] = veiculo
                linha['servico'] = servico
                linha['tipo'] = tipo
                linha['chave'] = chave
                linhas[chave] = linha

            linha = linhas[chave]

            data_os = parse_datetime(data_os).date()
            nome_mes = formata_data(data_os, 'mes_%Y_%m')

            if nome_mes not in linha:
                linha[nome_mes] = D(0)

            if nome_mes not in colunas:
                colunas[nome_mes] = formata_data(data_os, '%b/%Y')
                
            if veiculo not in total_meses:
                total_meses[veiculo] = {}
                
            if nome_mes not in total_meses[veiculo]:
                total_meses[veiculo][nome_mes] = D(0)
                
            total_meses[veiculo][nome_mes] += D(valor)
            linha[nome_mes] += D(valor)
            linha['total'] += D(valor)
            total_geral += D(valor)

        colunas_ordem = colunas.keys()
        colunas_ordem.sort()
        #
        # Agora, calculamos o % de cada mês frente ao total
        #
        for chave in linhas:
            linha = linhas[chave]
            
            veiculo = linha.veiculo
            
            for nome_mes in total_meses[veiculo]:
                linha[nome_mes + '_percentual'] = D(0)
                
                if total_meses[veiculo][nome_mes] > 0 and nome_mes in linha:
                    linha[nome_mes + '_percentual'] = linha[nome_mes] / total_meses[veiculo][nome_mes] * 100

            #for mes in colunas_ordem:
                #if mes not in linha:
                    #linha[mes] = D(0)

                #distancia_mes = linha[mes]
                #percentual = D(0)

                #if total_geral > 0 and distancia_mes > 0:
                    #percentual = distancia_mes / total_geral * D(100)
                    #percentual = percentual.quantize(D('0.01'))

                #linha[mes + '_percentual'] = percentual

        #
        # Agora, colocamos as colunas que serão impressas, na ordem dos meses
        #
        rel = FinanRelatorioAutomaticoPaisagem()
        rel.title = u'Custo de Ativo Imobilizado'
        filtro = rel.band_page_header.elements[-1]
        filtro.text = texto_filtro
        rel.colunas = [
            ['veiculo', 'C', 8, u'Tipo', False],
            ['servico', 'C', 30, u'Serviço/uso', False],
        ]

        for mes in colunas_ordem:
            rel.colunas += [[mes, 'F', 10, colunas[mes], True]]
            rel.colunas += [[mes + '_percentual', 'F', 5, '%', False]]

        rel.colunas += [['total', 'F', 12, 'Total', True]]

        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['tipo', u'Tipo', False],
            ['veiculo', u'Veículo', False],
        ]
        rel.monta_grupos(rel.grupos)

        linhas_impressas = []
        servicos_ordem = linhas.keys()
        servicos_ordem.sort()
        for servico in servicos_ordem:
            linhas_impressas.append(linhas[servico])

        pdf = gera_relatorio(rel, linhas_impressas)
        csv = gera_relatorio_csv(rel, linhas_impressas)
        
        #
        # Somente faz a união dos PDFs quando houver necessidade de mostrar
        # o gráfico
        #
        if rel_obj.sintetico:
            rel = Report(u'Frota Custo Imobilidado Serviço', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'frota_custo_imobilizado_servico.jrxml')
            rel.parametros['SQL'] = sql_grafico
            rel.parametros['NOME_EMPRESA'] = texto_filtro

            pdf_grafico, formato = rel.execute()        
            
            pdf_unico = PdfFileWriter()

            arq_pdf_custo = StringIO()
            
            arq_pdf_custo.write(pdf)
            separa_paginas = PdfFileReader(arq_pdf_custo)
            for i in range(separa_paginas.numPages):
                pdf_unico.addPage(separa_paginas.getPage(i))

        
            arq_pdf_grafico = StringIO()
            arq_pdf_grafico.write(pdf_grafico)            
            separa_paginas = PdfFileReader(arq_pdf_grafico)
            for i in range(separa_paginas.numPages):
                pdf_unico.addPage(separa_paginas.getPage(i))
                
                
            arq_pdf = StringIO()
            pdf_unico.write(arq_pdf)
            arq_pdf.seek(0)
            pdf = arq_pdf.read()
            arq_pdf_custo.close()
            arq_pdf_grafico.close()
            arq_pdf.close()
        
        dados = {
            'nome': 'custo_ativo_frota_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'custo_ativo_frota_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
            'arquivo_csv': base64.encodestring(csv)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_veiculo_manutencao(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
            select
                o.veiculo_id,
                t.nome as tipo,
                v.placa as placa,
                s.nome as servico,
                p.name as fornecedor,
                cast(o.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) as data_servico,
                oi.km_atual km_servico,
                oi.km_proximo km_proximo,
                (select max(cast(od.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date)) from frota_odometro od where od.veiculo_id = o.veiculo_id and od.os_id is null) as data_km,
                (select max(coalesce(od.valor_atual, 0)) from frota_odometro od where od.veiculo_id = o.veiculo_id and od.os_id is null) as km_atual

            from
                frota_os_item oi
                join frota_servico s on s.id = oi.servico_id
                join frota_os o on o.id = oi.os_id
                join frota_veiculo v on v.id = o.veiculo_id
                join frota_modelo m on m.id = v.modelo_id
                join frota_tipo t on t.id = m.tipo_id
                join res_partner p on p.id = o.res_partner_id

            where
                oi.km_proximo is not null
                and oi.km_proximo > 0
        """

        #
        # O código abaixo filtra somente as datas mais recentes, e exige que haja
        # somente 1 registro por veículo (o da data mais recente)
        #
        sql += """
                and cast(o.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) = (select max(cast(oo.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date)) from frota_os oo where oo.veiculo_id = o.veiculo_id and oo.servico_id = o.servico_id)
        """

        if rel_obj.veiculo_id:
            sql += """
                and o.veiculo_id = {veiculo_id}
            """.format(veiculo_id=rel_obj.veiculo_id.id)

        if rel_obj.servico_id:
            sql += """
                and o.servico_id = {servico_id}
            """.format(servico_id=rel_obj.servico_id.id)

        if rel_obj.company_id:
            sql += """
                and o.res_company_id = {company_id}
            """.format(company_id=rel_obj.company_id.id)

        sql += """

            order by
                servico,
                t.nome,
                placa,
                data_servico desc
        """

        cr.execute(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existem dados com os parâmetros informados!')


        linhas = []
        for veiculo_id, tipo, placa, servico, fornecedor, data_servico, km_servico, km_proximo, data_km, km_atual in dados:
            linha = DicionarioBrasil()

            km_servico = D(km_servico or 0)
            km_proximo = D(km_proximo or 0)
            km_atual = D(km_atual or 0)

            linha['tipo'] = tipo
            linha['placa'] = placa
            linha['servico'] = servico
            linha['fornecedor'] = fornecedor
            linha['data_servico'] = parse_datetime(data_servico).date()
            linha['km_servico'] = km_servico
            linha['km_proximo'] = km_proximo
            linha['data_km'] = parse_datetime(data_km).date()
            linha['km_atual'] = km_atual
            linha['faltam'] = D(0)

            if km_atual < km_proximo:
                linha['faltam'] = km_proximo - km_atual

            linhas.append(linha)

        rel = FinanRelatorioAutomaticoRetrato()
        rel.title = u'Manutenção de Veículos'

        if rel_obj.company_id:
            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Empresa/Unidade ' + rel_obj.company_id.name
            #filtro.text += ' - '
            #filtro.text += formata_data(data_inicial)
            #filtro.text += ' a '
            #filtro.text += formata_data(data_final)

        rel.colunas = [
            ['placa', 'C', 8, u'Veículo', False],
            ['fornecedor', 'C', 60, u'Fornecedor', False],
            ['data_servico', 'D', 10, u'Últ. serviço', False],
            ['km_servico', 'F', 10, u'Últ. serviço', False],
            ['data_km', 'D', 10, u'km Atual', False],
            ['km_atual', 'F', 10, u'km Atual', False],
            ['km_proximo', 'F', 10, u'Próx. serviço', False],
            ['faltam', 'F', 10, u'km faltam', False],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['servico', u'Serviço', False],
            ['tipo', u'Tipo', False],
        ]
        rel.monta_grupos(rel.grupos)

        pdf = gera_relatorio(rel, linhas)
        csv = gera_relatorio_csv(rel, linhas)

        dados = {
            'nome': 'manutencao_veiculo_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'manutencao_veiculo_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
            'arquivo_csv': base64.encodestring(csv)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_custo_atividade(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            filtro = {
                'data_inicial': data_inicial,
                'data_final': data_final,
            }
            texto_filtro = u'Período de '
            texto_filtro += formata_data(data_inicial)
            texto_filtro += u' a '
            texto_filtro += formata_data(data_final)

            sql = """
            select 
                resumo.*,
                coalesce((
                    select
                        coalesce(sum(fot.valor_atual - fot.valor_anterior), 0)
                    from
                        frota_odometro fot

                    where
                        to_char(cast(fot.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm') = resumo.mes
                        and fot.veiculo_id = resumo.veiculo_id
                ), 0) as km_total,
                
                coalesce((
                    select
                        sum(coalesce(os.quantidade_combustivel, 0))
                    from
                        frota_os os
                        join frota_os_item foi on foi.os_id = os.id
                        join frota_servico fis on fis.id = foi.servico_id
                        join res_company cq on cq.id = os.res_company_id
                        left join res_company ccq on ccq.id = cq.parent_id

                    where
                        os.state = 'F'
                        and fis.nome = 'ABASTECIMENTO'
                        and os.quantidade_combustivel > 0
                        and to_char(cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm') = resumo.mes
                        and os.veiculo_id = resumo.veiculo_id
                ), 0) as quantidade,

                coalesce((
                    select
                        sum(coalesce(os.valor_combustivel, 0))
                    from
                        frota_os os
                        join frota_os_item foi on foi.os_id = os.id
                        join frota_servico fis on fis.id = foi.servico_id
                        join res_company cq on cq.id = os.res_company_id
                        left join res_company ccq on ccq.id = cq.parent_id

                    where
                        os.state = 'F'
                        and fis.nome = 'ABASTECIMENTO'
                        and os.quantidade_combustivel > 0
                        and to_char(cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm') = resumo.mes
                        and os.veiculo_id = resumo.veiculo_id
                ), 0) as valor_combustivel
                

            from 
                (select
                    to_char(cast(fo.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm') as mes,
                    fo.veiculo_id,
                    t.nome as tipo,
                    fv.placa,
                    coalesce(sum(fo.valor_atual - fo.valor_anterior),0) as valor

                from
                    frota_odometro fo
                    join frota_veiculo fv on fv.id = fo.veiculo_id
                    join res_company c on c.id = fv.res_company_id
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id
                    left join frota_servico s on s.id = fo.servico_id
                    join frota_modelo m on m.id = fv.modelo_id
                    join frota_tipo t on t.id = m.tipo_id
                    left join hr_employee e on e.id = fo.hr_employee_id

                where
                    cast(fo.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                    and (fo.servico_id is null or (s.ignora_km is null or s.ignora_km = False))
                    and fo.data_fechamento is not null
            """

            filtro_company = ''
            if rel_obj.company_id:
                sql += """
                    and
                    (
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                    )
                """.format(company_id=rel_obj.company_id.id)

                filtro_company = """
                    and (
                        cq.id = {company_id}
                        or cq.parent_id = {company_id}
                        or ccq.parent_id = {company_id}
                    )
                """.format(company_id=rel_obj.company_id.id)
                
                texto_filtro += u'<br/>Empresa/unidade: ' + rel_obj.company_id.name


            filtro['filtro_company'] = filtro_company

            if rel_obj.veiculo_id:
                sql += """
                    and fo.veiculo_id = {veiculo_id}
                """
                filtro['veiculo_id'] = rel_obj.veiculo_id.id
                texto_filtro += u'<br/>Veículo: ' + rel_obj.veiculo_id.placa

            if rel_obj.hr_employee_id:
                sql += """
                    and e.id = {employee_id}
                """
                filtro['employee_id'] = rel_obj.hr_employee_id.id
                texto_filtro += u'<br/>Motorista: ' + rel_obj.hr_employee_id.nome

            if rel_obj.servico_id:
                sql += """
                    and fo.servico_id = {servico_id}
                """
                filtro['servico_id'] = rel_obj.servico_id.id
                texto_filtro += u'<br/>Serviço: ' + rel_obj.servico_id.nome_completo

            if len(rel_obj.servico_ids):
                texto_filtro += u'<br/>Serviços/atividades: '
                servico_ids = []
                for servico_obj in rel_obj.servico_ids:
                    servico_ids.append(servico_obj.id)
                    texto_filtro += u', ' + servico_obj.nome_completo

                texto_filtro = texto_filtro.replace(u'Serviços/atividades: , ', u'Serviços/atividades: ')

                sql += """
                    and fo.servico_id in ({servico_ids})
                """
                filtro['servico_ids'] = str(servico_ids).replace('[', '').replace(']', '')


            sql += """
                group by
                    1, t.nome, fo.veiculo_id, fv.placa

                order by
                    1, t.nome, fv.placa
            ) as resumo
            """

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            linhas = []
            linhas_meses = {}
            veiculo_ids = []
            meses = []
            for mes, veiculo_id, tipo, placa, valor, km_total, quantidade, valor_combustivel in dados:
                linha = DicionarioBrasil()
                veiculo_ids.append(veiculo_id)
                linha['mes'] = formata_data(parse_datetime(mes + '-01'), '%B/%Y').upper()
                
                mes = mes.replace('-', '_')
                if mes not in meses:
                    meses.append(mes)
                
                chave_mes = tipo + placa
                if chave_mes not in linhas_meses:
                    linhas_meses[chave_mes] = DicionarioBrasil()
                    linhas_meses[chave_mes]['tipo'] = tipo
                    linhas_meses[chave_mes]['placa'] = placa
                    #linhas_meses[chave_mes]['quantidade'] = D(0)
                    #linhas_meses[chave_mes]['valor_combustivel'] = D(0)
                    #linhas_meses[chave_mes]['valor_servicos'] = D(0)
                    #linhas_meses[chave_mes]['media'] = D(0)
                    #linhas_meses[chave_mes]['media_valor_combustivel'] = D(0)
                    #linhas_meses[chave_mes]['valor_total'] = D(0)
                    
                if mes not in linhas_meses[chave_mes]:
                    linhas_meses[chave_mes][mes] = D(0)
                
                linhas_meses[chave_mes][mes] += valor
                
                linha['tipo'] = tipo
                linha['placa'] = placa
                
                km = D(valor or 0)
                km_total = D(km_total or 0)
                
                linha['valor'] = valor
                linha['km_total'] = km_total
                
                proporcao_km = D(1)
                if km_total:
                    proporcao_km = km / km_total
                
                linha['percentual'] = proporcao_km * 100
                
                quantidade = D(quantidade or 0)
                quantidade *= proporcao_km
                quantidade = quantidade.quantize(D('0.01'))
                
                valor_combustivel = D(valor_combustivel or 0)
                valor_combustivel *= proporcao_km
                valor_combustivel = valor_combustivel.quantize(D('0.01'))

                valor_servicos = D(0)
                #valor_servicos = D(valor_servicos or 0)
                #valor_servicos *= proporcao_km
                #valor_servicos = valor_servicos.quantize(D('0.01'))
                
                linha['quantidade'] = quantidade
                linha['valor_combustivel'] = valor_combustivel
                #linha['valor_servicos'] = valor_servicos
                linha['media'] = D('0')
                linha['media_valor_combustivel'] = D('0')
                #linha['numero_os'] = ''
                linha['valor_total'] = D(valor_combustivel or 0) + D(valor_servicos or 0)

                if quantidade > 0:
                    linha['media'] = D(valor or 0) / D(quantidade or 1)
                    linha['media'] = linha['media'].quantize(D('0.01'))

                if valor > 0:
                    linha['media_valor_combustivel'] = D(valor_combustivel) / D(valor or 1)
                    linha['media_valor_combustivel'] = linha['media_valor_combustivel'].quantize(D('0.01'))

                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Km Rodados'
            filtro = rel.band_page_header.elements[-1]
            filtro.text = texto_filtro
            rel.band_page_header.height += len(texto_filtro.split('<br/>')) * 0.28 * cm

            if rel_obj.sintetico:
                rel.colunas = [
                    ['mes'  , 'C', 15, u'MÊS', False],
                    ['placa', 'C', 15, u'Veículo', False],
                    ['valor', 'F', 15, u'km rodado', True],
                    ['km_total', 'F', 15, u'km total', True],
                    ['percentual', 'F', 15, u'% km', True],
                    ['quantidade', 'F', 15, u'Litros', True],
                    ['media', 'F', 15, u'km/L', False],
                    ['media_valor_combustivel', 'F', 15, u'R$/km', False],
                    ['valor_combustivel', 'F', 15, u'Total abastecimento', True],
                    #['valor_servicos', 'F', 15, u'Outros serviços', True],
                    #['valor_total', 'F', 15, u'Total geral', True],
                    #['numero_os', 'C', 7, u'OS', False],
                    #['data_os', 'C', 10, u'Data OS', False],
                ]
                rel.monta_detalhe_automatico(rel.colunas)

                rel.grupos = [
                    ['mes', u'MÊS', False],
                    ['tipo', u'Tipo', False],
                ]
                rel.monta_grupos(rel.grupos)
                
            else:
                
                rel.colunas = [
                    ['placa', 'C', 15, u'Veículo', False],
                    #['valor', 'F', 15, u'km rodado', True],
                    #['numero_os', 'C', 7, u'OS', False],
                    #['data_os', 'C', 10, u'Data OS', False],
                ]
                
                for mes in meses:
                    rel.colunas.append([mes, 'F', 15, formata_data(parse_datetime(mes.replace('_', '-') + '-01'), '%B/%Y'), True])
                
                rel.monta_detalhe_automatico(rel.colunas)

                rel.grupos = [
                    ['tipo', u'Tipo', False],
                ]
                rel.monta_grupos(rel.grupos)
                
                linhas = []
                chaves = linhas_meses.keys()
                for chave in sorted(chaves):
                    linhas.append(linhas_meses[chave])

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'km_rodado_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'km_rodado_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_custo_imobilizado_servico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        filtro = {
            'data_inicial': str(data_inicial),
            'data_final': str(data_final),
        }
        texto_filtro = u'Período de '
        texto_filtro += formata_data(data_inicial)
        texto_filtro += u' a '
        texto_filtro += formata_data(data_final)

        sql = """
            select
                t.nome as tipo,
                case
                    when srv.nome != 'ABASTECIMENTO' then 'MANUTENÇÃO'
                    else srv.nome
                end as servico,
                vei.placa as veiculo,
                cast(to_char(cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'yyyy-mm-01') as date) as mes,
                sum(coalesce(osi.valor, 0)) as valor

            from
                frota_os os
                join frota_veiculo vei on vei.id = os.veiculo_id
                join frota_os_item osi on osi.os_id = os.id
                join frota_servico srv on srv.id = osi.servico_id
                left join res_company c on c.id = os.res_company_id
                join frota_modelo m on m.id = vei.modelo_id
                join frota_tipo t on t.id = m.tipo_id

            where
                cast(os.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                and os.state = 'F'
        """

        if rel_obj.tipo_id:
            filtro['tipo_id'] = rel_obj.tipo_id.id
            sql += """
                and t.id = {tipo_id}
            """
            texto_filtro += u'; Tipo: '
            texto_filtro += rel_obj.tipo_id.nome

        if rel_obj.veiculo_id:
            filtro['veiculo_id'] = rel_obj.veiculo_id.id
            sql += """
                and os.veiculo_id = {veiculo_id}
            """
            texto_filtro += u'; Veículo: '
            texto_filtro += rel_obj.veiculo_id.placa

        if rel_obj.company_id:
            filtro['company_id'] = rel_obj.company_id.id
            sql += """
                and (
                    os.res_company_id = {company_id}
                  or c.parent_id = {company_id}
                )
            """
            texto_filtro += u'; Empresa: '
            texto_filtro += rel_obj.company_id.name

        if (not rel_obj.partner_id) and (not rel_obj.todos):
            texto_filtro += u'; Somente veículos próprios'
            sql += "and vei.proprietario_id is null"

        elif rel_obj.partner_id:
            texto_filtro += u'; Propriedade de: '
            texto_filtro += rel_obj.partner_id.razao_social.strip()
            texto_filtro += u' - '
            texto_filtro += rel_obj.partner_id.cnpj_cpf
            filtro['proprietario_id'] = rel_obj.partner_id.id
            sql += """
                and vei.proprietario_id = {proprietario_id}
            """

        if len(rel_obj.servico_excluido_ids):
            servico_excluido_ids = []

            for servico_obj in rel_obj.servico_excluido_ids:
                if rel_obj.incluir_abastecimento and u'ABASTECIMENTO' in servico_obj.nome.upper():
                    continue
                if rel_obj.incluir_lavacao and u'LAVAÇÃO' in servico_obj.nome.upper():
                    continue

                servico_excluido_ids.append(servico_obj.id)

            filtro['servico_excluido_ids'] = str(servico_excluido_ids).replace(']', ')').replace('[', '(')
            sql += """
                and srv.id not in {servico_excluido_ids}
            """

        sql += """
            group by
                t.nome,
                2,
                vei.placa,
                mes

            order by
                t.nome,
                2,
                vei.placa,
                mes;
        """

        sql = sql.format(**filtro)
        #print(sql)
        cr.execute(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existem dados com os parâmetros informados!')

        colunas = {}
        linhas = {}
        total_geral = D(0)

        #
        # Acumulamos as linhas e colunas das datas
        #
        for tipo, servico, veiculo, data_os, valor in dados:
            chave = tipo + '|' + servico + '|' + veiculo
            if chave not in linhas:
                linha = DicionarioBrasil()
                linha['total'] = D(0)
                linha['servico'] = servico
                linha['veiculo'] = veiculo
                linha['tipo'] = tipo
                linha['chave'] = chave
                linhas[chave] = linha

            linha = linhas[chave]

            data_os = parse_datetime(data_os).date()
            nome_mes = formata_data(data_os, 'mes_%Y_%m')

            if nome_mes not in linha:
                linha[nome_mes] = D(0)

            if nome_mes not in colunas:
                colunas[nome_mes] = formata_data(data_os, '%b/%Y')

            linha[nome_mes] += D(valor)
            linha['total'] += D(valor)
            total_geral += D(valor)

        colunas_ordem = colunas.keys()
        colunas_ordem.sort()
        #
        # Agora, calculamos o % de cada mês frente ao total
        #
        for chave in linhas:
            linha = linhas[chave]

            for mes in colunas_ordem:
                if mes not in linha:
                    linha[mes] = D(0)

                distancia_mes = linha[mes]
                percentual = D(0)

                if total_geral > 0 and distancia_mes > 0:
                    percentual = distancia_mes / total_geral * D(100)
                    percentual = percentual.quantize(D('0.01'))

                linha[mes + '_percentual'] = percentual

        #
        # Agora, colocamos as colunas que serão impressas, na ordem dos meses
        #
        rel = FinanRelatorioAutomaticoPaisagem()
        rel.title = u'Custo de Ativo Imobilizado - Por serviço'
        filtro = rel.band_page_header.elements[-1]
        filtro.text = texto_filtro
        rel.colunas = [
            ['servico', 'C', 30, u'Serviço/uso', False],
            ['veiculo', 'C', 8, u'Placa', False],
        ]

        for mes in colunas_ordem:
            rel.colunas += [[mes, 'F', 10, colunas[mes], True]]
            rel.colunas += [[mes + '_percentual', 'F', 5, '%', False]]

        rel.colunas += [['total', 'F', 12, 'Total', True]]

        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['tipo', u'Tipo', False],
            ['servico', u'Serviço', False],
        ]
        rel.monta_grupos(rel.grupos)

        linhas_impressas = []
        servicos_ordem = linhas.keys()
        servicos_ordem.sort()
        for servico in servicos_ordem:
            linhas_impressas.append(linhas[servico])

        pdf = gera_relatorio(rel, linhas_impressas)
        csv = gera_relatorio_csv(rel, linhas_impressas)

        dados = {
            'nome': 'custo_ativo_frota_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'custo_ativo_frota_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
            'arquivo_csv': base64.encodestring(csv)
        }
        rel_obj.write(dados)

        return True

    def gera_grafico_abastecimento_manutencao(self, cr, uid, ids):
        TEMPLATE_HTML_INICIO = u"""
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["line", "corechart", "gauge"], 'language': 'pt-BR'});
      google.setOnLoadCallback(drawChart);

      function drawChart() {

        var dados_grafico_linha = google.visualization.arrayToDataTable([
          ['Mês', 'Abastecimento', 'Manutenção', 'Total'],
"""

        TEMPLATE_HTML_DADOS = u"['{mes}',  {abastecimento}, {manutencao}, {total}],"

        TEMPLATE_HTML_FIM = u"""        ]);

        var visao_linha = new google.visualization.DataView(dados_grafico_linha);

        visao_linha.setColumns(
            [0, 1,
             {type: 'string', role: 'annotation', sourceColumn: 1, calc: 'stringify'},
             2,
             {type: 'string', role: 'annotation', sourceColumn: 2, calc: 'stringify'},
             3,
             {type: 'string', role: 'annotation', sourceColumn: 3, calc: 'stringify'}
             ]
        );

        var opcoes_linha = {
           title: 'Valores de Abastecimento e Manutenção',
           curveType: 'function'
          // is3D: true
          // legend: {position: 'top', textStyle: {color: 'blue', fontSize: 16}}
        };

        var grafico_linha = new google.visualization.LineChart(document.getElementById('grafico_linha'));

        grafico_linha.draw(visao_linha, opcoes_linha);
      }
    </script>
  </head>
  <body style="border:0; margin: 0;">
    <div id="grafico_linha" style="width: 1300px; height: 800px;"></div>
  </body>
</html>
"""

    def gera_listagem_odometro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = data_hora_horario_brasilia(parse_datetime(rel_obj.data_hora_inicial + ' UTC'))
        data_final = data_hora_horario_brasilia(parse_datetime(rel_obj.data_hora_final + ' UTC'))
        
        if data_final == data_inicial:
            data_final += relativedelta(days=+1)

        filtro = {
            'data_inicial': str(data_inicial),
            'data_final': str(data_final),
        }
        texto_filtro = u'Período de '
        texto_filtro += formata_data(data_inicial, '%d/%m/%Y %H:%M:%S')
        texto_filtro += u' a '
        texto_filtro += formata_data(data_final, '%d/%m/%Y %H:%M:%S')

        sql = """
            select
                rp.name as empresa,
                t.nome as tipo,
                fv.placa,
                coalesce(e.nome, '') as motorista,
                s.nome as servico,
                cast(fo.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as timestamp) as data_abertura,
                cast(fo.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as timestamp) as data_fechamento,
                coalesce(fo.valor_anterior, 0) as km_abertura,
                coalesce(fo.valor_atual, 0) as km_fechamento,
                case
                    when coalesce(fo.valor_atual, 0) != 0 then coalesce(fo.valor_atual, 0) - coalesce(fo.valor_anterior, 0) 
                    else 0
                end as km_rodado

            from
                frota_odometro fo
                join frota_veiculo fv on fv.id = fo.veiculo_id
                join res_company c on c.id = fv.res_company_id
                join res_partner rp on rp.id = c.partner_id
                left join res_company cc on cc.id = c.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                left join frota_servico s on s.id = fo.servico_id
                join frota_modelo m on m.id = fv.modelo_id
                join frota_tipo t on t.id = m.tipo_id
                left join hr_employee e on e.id = fo.hr_employee_id
                left join hr_department d on d.id = fo.hr_department_id

            where
                (
                    cast(fo.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as timestamp with time zone) between '{data_inicial}' and '{data_final}'
                    or cast(fo.data_fechamento at time zone 'UTC' at time zone 'America/Sao_Paulo' as timestamp with time zone) between '{data_inicial}' and '{data_final}'
                )
            --    and (fo.servico_id is null or (s.ignora_km is null or s.ignora_km = False))
        """

        filtro_company = ''
        if rel_obj.company_id:
            sql += """
                and
                (
                    c.id = {company_id}
                    or c.parent_id = {company_id}
                    or cc.parent_id = {company_id}
                )
            """.format(company_id=rel_obj.company_id.id)

            filtro_company = """
                and (
                    cq.id = {company_id}
                    or cq.parent_id = {company_id}
                    or ccq.parent_id = {company_id}
                )
            """.format(company_id=rel_obj.company_id.id)
            texto_filtro += u'<br/>Empresa/unidade: ' + rel_obj.company_id.name                

        filtro['filtro_company'] = filtro_company
        
        if rel_obj.servico_id:
            sql += """
                and fo.servico_id = {servico_id}
            """.format(servico_id=rel_obj.servico_id.id)
            texto_filtro += u'<br/>Serviço: ' + rel_obj.servico_id.nome                

        if rel_obj.tipo_id:
            filtro['tipo_id'] = rel_obj.tipo_id.id
            sql += """
                and t.id = {tipo_id}
            """
            texto_filtro += u'<br/>Tipo: '
            texto_filtro += rel_obj.tipo_id.nome

        if rel_obj.veiculo_id:
            filtro['veiculo_id'] = rel_obj.veiculo_id.id
            sql += """
                and fo.veiculo_id = {veiculo_id}
            """
            texto_filtro += u'<br/>Veículo: '
            texto_filtro += rel_obj.veiculo_id.placa

        if rel_obj.hr_employee_id:
            sql += """
                and e.id = {employee_id}
            """
            filtro['employee_id'] = rel_obj.hr_employee_id.id
            texto_filtro += u'<br/>Motorista: ' + rel_obj.hr_employee_id.nome                

        sql += """

            order by
                t.nome, fo.data, fo.data_fechamento, fv.placa
        """

        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)

        dados = cr.fetchall()
        linhas = []
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

        linhas = []
        for empresa, tipo, placa, motorista, servico, data_abertura, data_fechamento, km_abertura, km_fechamento, km_rodado in dados:
            linha = DicionarioBrasil()
            linha['empresa'] = empresa
            linha['tipo'] = tipo
            linha['placa'] = placa
            linha['motorista'] = motorista
            linha['servico'] = servico
            linha['data_abertura'] = None
            
            if data_abertura:
                linha['data_abertura'] = parse_datetime(data_abertura)
                
            linha['data_fechamento'] = None

            if data_fechamento:
                linha['data_fechamento'] = parse_datetime(data_fechamento)

            linha['km_abertura'] = D(km_abertura or 0)
            linha['km_fechamento'] = D(km_fechamento or 0)
            linha['km_rodado'] = D(km_rodado or 0)

            linhas.append(linha)

        rel = FinanRelatorioAutomaticoRetrato()
        rel.title = u'Relatório de Km Rodados - Odômetros'
        filtro = rel.band_page_header.elements[-1]
        filtro.text = texto_filtro
        print(filtro.height)
        filtro.height += len(texto_filtro.split('<br/>')) * 0.28 * cm
        rel.band_page_header.height += len(texto_filtro.split('<br/>')) * 0.28 * cm
        print(filtro.height)


        rel.colunas = [
            ['placa', 'C', 9, u'Veículo', False],
            ['motorista', 'C', 30, u'Motorista', False],
            ['servico', 'C', 30, u'Serviço', False],
            ['data_abertura', 'DH', 19, u'Abertura', False],
            ['data_fechamento', 'DH', 19, u'Fechamento', False],
            ['km_abertura', 'F', 10, u'km abertura', False],
            ['km_fechamento', 'F', 10, u'km fechamento', False],
            ['km_rodado', 'F', 10, u'km rodado', True],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            #['empresa', u'Empresa', False],
            ['tipo', u'Tipo', False],
        ]
        rel.monta_grupos(rel.grupos)

        pdf = gera_relatorio(rel, linhas)
        csv = gera_relatorio_csv(rel, linhas)

        dados = {
            'nome': 'odometros_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'odometros_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
            'arquivo_csv': base64.encodestring(csv)
        }
        rel_obj.write(dados)


frota_relatorio()
