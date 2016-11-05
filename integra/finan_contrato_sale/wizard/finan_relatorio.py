# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import *
from finan_contrato_sale.models.sql_contratos_comercial import *
from copy import copy


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'

    _columns = {
        'company_2_id': fields.many2one('res.company', u'Empresa 2'),
        'company_ids': fields.many2many('res.company', 'finan_relatorio_company', 'relatorio_id', 'company_id', u'Empresas'),
        'hr_department_ids': fields.many2many('hr.department', 'finan_relatorio_department', 'relatorio_id', 'department_id', u'Postos'),
        'exclui_categoria_ids': fields.many2many('res.partner.category', 'finan_relatorio_categoria_excluir', 'relatorio_id', 'categoria_id', u'Categorias a excluir'),
        'contratos_faturados': fields.boolean(u'Somente Contratos ?'),

        'indicador_corporativo': fields.boolean('Indicadores corporativos?'),

        'incluir_monitoramento_garantido': fields.boolean(u'Incluir SOMENTE serviço de monitoramento garantido?'),
    }


    def _monta_filtro(self, cr, uid, rel_obj, filtro, texto_filtro, filtro_faturamento=False):
        texto_filtro = u'Unidades '

        company_ids = []
        for c_obj in rel_obj.company_ids:
            company_ids.append(c_obj.id)
            texto_filtro += u', ' + c_obj.name

        filtro['company_ids'] = str(company_ids).replace('[', '').replace(']', '')
        texto_filtro = texto_filtro.replace(u'Unidades , ', u'Unidades ')

        filtro['filtro_adicional'] = ''
        filtro['filtro_adicional_anterior'] = ''

        if filtro_faturamento:
            if rel_obj.vendedor_id:
                texto_filtro = u'Vendedor: ' + rel_obj.vendedor_id.name
                filtro['filtro_adicional'] += ' and vendedor.id = ' + str(rel_obj.vendedor_id.id)
                filtro['filtro_adicional_anterior'] += ' and vendedor.id = ' + str(rel_obj.vendedor_id.id)

        else:
            if rel_obj.vendedor_id:
                texto_filtro = u'Vendedor: ' + rel_obj.vendedor_id.name
                filtro['filtro_adicional'] = """and (
                exists(
                    select fcv.id
                    from finan_contrato_vendedor fcv
                    where fcv.contrato_id = fc.id
                    and fcv.vendedor_id = {vendedor_id}
                    and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
                ) or (
                   coalesce((select
                        count(*)
                    from
                        finan_contrato_vendedor fcv
                    where
                        fcv.contrato_id = fc.id
                    ), 0) = 0
                    and fc.vendedor_id = {vendedor_id}
                ))
                """.format(vendedor_id=rel_obj.vendedor_id.id, **filtro)
                filtro['filtro_adicional_anterior'] = """and (
                exists(
                    select fcv.id
                    from finan_contrato_vendedor fcv
                    where fcv.contrato_id = fc.id
                    and fcv.vendedor_id = {vendedor_id}
                    and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial_anterior}', '{data_final_anterior}')
                ) or  (
                   coalesce((select
                        count(*)
                    from
                        finan_contrato_vendedor fcv
                    where
                        fcv.contrato_id = fc.id
                    ), 0) = 0
                    and fc.vendedor_id = {vendedor_id}
                ))
                """.format(vendedor_id=rel_obj.vendedor_id.id, **filtro)

        if filtro_faturamento:
            if len(rel_obj.hr_department_ids):
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Posto '
                posto_ids = []
                for posto_obj in rel_obj.hr_department_ids:
                    posto_ids.append(posto_obj.id)
                    texto_filtro += u', ' + posto_obj.name

                texto_filtro = texto_filtro.replace(u'Posto , ', u'Posto ')
                filtro['filtro_adicional'] += ' and posto.id in ({postos})'.format(postos=posto_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and posto.id in ({postos})'.format(postos=posto_ids).replace('[', '').replace(']', '')

        else:
            if len(rel_obj.hr_department_ids):
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Posto '
                posto_ids = []
                for posto_obj in rel_obj.hr_department_ids:
                    posto_ids.append(posto_obj.id)
                    texto_filtro += u', ' + posto_obj.name

                texto_filtro = texto_filtro.replace(u'Posto , ', u'Posto ')
                filtro['filtro_adicional'] += ' and fc.hr_department_id in ({postos})'.format(postos=posto_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and fc.hr_department_id in ({postos})'.format(postos=posto_ids).replace('[', '').replace(']', '')


        if filtro_faturamento:
            if rel_obj.categoria_id:
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Categoria: ' + rel_obj.categoria_id.complete_name
                filtro['filtro_adicional'] += ' and ped.res_partner_category_id = ' + str(rel_obj.categoria_id.id)
                filtro['filtro_adicional_anterior'] += ' and ped.res_partner_category_id = ' + str(rel_obj.categoria_id.id)

            elif len(rel_obj.exclui_categoria_ids):
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Todas as categorias exceto '
                categoria_ids = []
                for cat_obj in rel_obj.exclui_categoria_ids:
                    categoria_ids.append(cat_obj.id)
                    texto_filtro += u', ' + cat_obj.complete_name

                texto_filtro = texto_filtro.replace(u'Todas as categorias exceto , ', u'Todas as categorias exceto ')

                filtro['filtro_adicional'] += ' and (ped.res_partner_category_id is null or ped.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and (ped.res_partner_category_id is null or ped.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')

        else:
            if rel_obj.categoria_id:
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Categoria: ' + rel_obj.categoria_id.complete_name
                filtro['filtro_adicional'] += ' and fc.res_partner_category_id = ' + str(rel_obj.categoria_id.id)
                filtro['filtro_adicional_anterior'] += ' and fc.res_partner_category_id = ' + str(rel_obj.categoria_id.id)

            elif len(rel_obj.exclui_categoria_ids):
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Todas as categorias exceto '
                categoria_ids = []
                for cat_obj in rel_obj.exclui_categoria_ids:
                    categoria_ids.append(cat_obj.id)
                    texto_filtro += u', ' + cat_obj.complete_name

                texto_filtro = texto_filtro.replace(u'Todas as categorias exceto , ', u'Todas as categorias exceto ')

                filtro['filtro_adicional'] += ' and (fc.res_partner_category_id is null or fc.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and (fc.res_partner_category_id is null or fc.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')

        if filtro_faturamento:
            if rel_obj.grupo_economico_id:
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Grupo econômico: ' + rel_obj.grupo_economico_id.nome
                filtro['filtro_adicional'] += ' and ped.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)
                filtro['filtro_adicional_anterior'] += ' and ped.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)

        else:
            if rel_obj.grupo_economico_id:
                if len(texto_filtro) > 0:
                    texto_filtro += u'; '

                texto_filtro += u'Grupo econômico: ' + rel_obj.grupo_economico_id.nome
                filtro['filtro_adicional'] += ' and fc.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)
                filtro['filtro_adicional_anterior'] += ' and fc.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)

        if filtro_faturamento:
            return texto_filtro

        #
        # Vai excluir os serviços de vigilância
        #
        if rel_obj.provisionado:
            texto_filtro += u'; incluídos SOMENTE serviços de vigilância'

            filtro['filtro_adicional'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) > 0)
            """
            filtro['filtro_adicional_anterior'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) > 0)
            """
        elif rel_obj.incluir_monitoramento_garantido:
            texto_filtro += u'; incluídos SOMENTE serviços de monitoramento garantido'

            filtro['filtro_adicional'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3179)
                ),0) > 0)
            """
            filtro['filtro_adicional_anterior'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3179)
                ),0) > 0)
            """

        elif not rel_obj.zera_saldo:
            texto_filtro += u'; não incluídos serviços de vigilância'

            filtro['filtro_adicional'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) = 0)
            """
            filtro['filtro_adicional_anterior'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) = 0)
            """

        return texto_filtro

    def gera_relatorio_analise_contratos_comercial(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id, context=context)
        #company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        texto_filtro = ''

        #
        # Caso seja informado dia 1º e último dia do mês, as datas seguem o mês calendário,
        # caso contrário, são meses corridos
        #
        if data_inicial == primeiro_dia_mes(data_inicial) and data_final == ultimo_dia_mes(data_final):
            meses = idade_meses_sem_dia(data_inicial, data_final) + 1

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_inicial_anterior = primeiro_dia_mes(data_inicial_anterior)
            data_final_anterior = ultimo_dia_mes(data_inicial_anterior + relativedelta(months=+meses-1))

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(day=1)
            data_final_competencia += relativedelta(months=+1)
            data_final_competencia = ultimo_dia_mes(data_final_competencia)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(day=1)
            data_final_competencia_anterior += relativedelta(months=+1)
            data_final_competencia_anterior = ultimo_dia_mes(data_final_competencia_anterior)

        else:
            meses = idade_meses_sem_dia(data_inicial, data_final)

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_final_anterior = data_final + relativedelta(months=-meses)

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(months=+1)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)

        ####meses = idade_meses_sem_dia(data_inicial, data_final)
        ###meses = 1

        ###data_inicial_anterior = data_inicial + relativedelta(months=-meses)
        ###data_final_anterior = data_final + relativedelta(months=-meses)

        ###data_inicial_competencia = data_inicial + relativedelta(months=+1)
        ###data_final_competencia = data_final + relativedelta(months=+1)

        ###data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
        ###data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)


        filtro = {
            #'campo_data_vencimento': 'data_vencimento',
            'campo_data_vencimento': 'data_vencimento_original',

            'data_inicial': data_inicial,
            'data_final': data_final,
            'data_inicial_competencia': data_inicial_competencia,
            'data_final_competencia': data_final_competencia,
            #'company_id': company_id,
            'company_ids': '',
            'filtro_adicional': '',
            'filtro_adicional_anterior': '',
            'data_inicial_anterior': data_inicial_anterior,
            'data_final_anterior': data_final_anterior,
            'data_inicial_competencia_anterior': data_inicial_competencia_anterior,
            'data_final_competencia_anterior': data_final_competencia_anterior,
        }

        print('data inicial e final ' + formata_data(data_inicial) + ' e ' + formata_data(data_final))
        print('data inicial e final do periodo anterior ' + formata_data(data_inicial_anterior)  + ' e ' +  formata_data(data_final_anterior))
        print('data inicial e final do vencimento (competencia) ' + formata_data(data_inicial_competencia)  + ' e ' + formata_data(data_final_competencia))
        print('data inicial e final do vencimento (competencia) anterior ' + formata_data(data_inicial_competencia_anterior)  + ' e ' + formata_data(data_final_competencia_anterior))

        #if rel_obj.company_2_id:
        #    filtro['company_ids'] += ', ' + str(rel_obj.company_2_id.id)

        rel = Report('Analise de Contratos', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_analise_contratos_comercial.jrxml')
        rel.outputFormat = rel_obj.formato
        rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['IS_SINTETICO'] = rel_obj.tipo_rel
        rel.parametros['USO_COMERCIAL'] = True

        texto_filtro = u''
        texto_filtro = self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, texto_filtro)
        #print(texto_filtro)

        rel.parametros['SQL_CONTRATOS_REGULARES'] = SQL_CONTRATOS_REGULARES_COMERCIAL.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_NOVOS'] = SQL_CONTRATOS_NOVOS_COMERCIAL.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_RESCINDIDOS'] = SQL_CONTRATOS_RESCINDIDOS_COMERCIAL.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_DIFERENCA_MESES'] = SQL_CONTRATOS_DIFERENCA_MESES_COMERCIAL.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_CONTRATOS_ALTERADOS'] = SQL_CONTRATOS_ALTERADOS_COMERCIAL.format(**filtro).replace('\n', ' ')
        rel.parametros['FILTRO_ADICIONAL'] = texto_filtro
        rel.parametros['meses'] = meses

        valores_gerais = rel_obj.agrupa_indicadores(rel_obj, copy(filtro), numero_empresa=0)
        #valores_unidade_1 = rel_obj.agrupa_indicadores(rel_obj, copy(filtro), numero_empresa=1)
        #valores_unidade_2 = rel_obj.agrupa_indicadores(rel_obj, copy(filtro), numero_empresa=2)

        for campo in valores_gerais:
            valores_gerais[campo] = float(valores_gerais[campo])
        #for campo in valores_unidade_1:
            #valores_unidade_1[campo] = float(valores_unidade_1[campo])
        #for campo in valores_unidade_2:
            #valores_unidade_2[campo] = float(valores_unidade_2[campo])

        rel.parametros.update(valores_gerais)
        #rel.parametros.update(valores_unidade_1)
        #rel.parametros.update(valores_unidade_2)

        print(SQL_CONTRATOS_NOVOS_COMERCIAL.format(**filtro))

        pdf, formato = rel.execute()

        dados = {
            'nome': u'analise_contratos_comercial_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def agrupa_indicadores(self, cr, uid, ids, rel_obj, filtro, numero_empresa=0, context={}):
        agrupa = {}

        if numero_empresa == 0:
            indice = 'total'
        else:
            indice = str(numero_empresa)

        agrupa['vr_regulares_%s' % indice] = D(0)
        agrupa['qtd_regulares_%s' % indice] = D(0)
        agrupa['vr_regulares_anterior_%s' % indice] = D(0)
        agrupa['qtd_regulares_anterior_%s' % indice] = D(0)
        agrupa['vr_novos_%s' % indice] = D(0)
        agrupa['qtd_novos_%s' % indice] = D(0)
        agrupa['vr_novos_anterior_%s' % indice] = D(0)
        agrupa['qtd_novos_anterior_%s' % indice] = D(0)
        agrupa['vr_rescindidos_%s' % indice] = D(0)
        agrupa['qtd_rescindidos_%s' % indice] = D(0)
        agrupa['vr_rescindidos_anterior_%s' % indice] = D(0)
        agrupa['qtd_rescindidos_anterior_%s' % indice] = D(0)
        agrupa['vr_baixados_%s' % indice] = D(0)
        agrupa['qtd_baixados_%s' % indice] = D(0)
        agrupa['vr_baixados_anterior_%s' % indice] = D(0)
        agrupa['qtd_baixados_anterior_%s' % indice] = D(0)
        agrupa['vr_anterior_%s' % indice] = D(1)
        agrupa['qtd_anterior_%s' % indice] = D(1)
        agrupa['vr_reducao_%s' % indice] = D(0)
        agrupa['vr_diferenca_%s' % indice] = D(0)
        agrupa['vr_reajuste_%s' % indice] = D(0)
        agrupa['vr_faturamento_%s' % indice] = D(0)
        agrupa['vr_perdas_%s' % indice] = D(0)
        agrupa['media_perdas_%s' % indice] = D(0)
        agrupa['vr_vendas_%s' % indice] = D(0)

        #if numero_empresa == 1:
            #filtro['company_ids'] = rel_obj.company_id.id
        #elif numero_empresa == 2:
            #if rel_obj.company_2_id:
                #filtro['company_ids'] = rel_obj.company_2_id.id
            #else:
                #return agrupa

        self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, '', filtro_faturamento=True)
        #
        # Valor de vendas (vendas - devoluções)
        #
        sql = SQL_RESUMO_FATURAMENTO.format(**filtro)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            for tipo, unidade, posto, vendedor, vr_faturado in dados:
                agrupa['vr_vendas_%s' % indice] += vr_faturado

        self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, '')
        #
        # Buscamos as reduções e diferenças do período
        #
        sql = SQL_CONTRATOS_DIFERENCA_MESES_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for numero_documento_original, numero_documento, data_vencimento_contrato, valor_contrato, valor_contrato_anterior, data_vencimento_anterior, contrato_id, reajuste_ids, contrato_ids, diferenca, cliente, numero_contrato in dados:
            if not reajuste_ids:
                agrupa['vr_diferenca_%s' % indice] += D(diferenca or 0)

                if diferenca < 0:
                    agrupa['vr_reducao_%s' % indice] += D(diferenca or 0)
            else:
                agrupa['vr_reajuste_%s' % indice] += D(diferenca or 0)

        #
        # Agrupamos os dados do período anterior
        #
        #
        # Valores agrupados para indicadores - REGULARES
        #
        sql = SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_regulares_anterior_%s' % indice], agrupa['qtd_regulares_anterior_%s' % indice] = dados[0]
            agrupa['vr_regulares_anterior_%s' % indice] = D(agrupa['vr_regulares_anterior_%s' % indice] or 0)
            agrupa['qtd_regulares_anterior_%s' % indice] = D(agrupa['qtd_regulares_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - NOVOS
        #
        sql = SQL_CONTRATOS_NOVOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_novos_anterior_%s' % indice], agrupa['qtd_novos_anterior_%s' % indice] = dados[0]
            agrupa['vr_novos_anterior_%s' % indice] = D(agrupa['vr_novos_anterior_%s' % indice] or 0)
            agrupa['qtd_novos_anterior_%s' % indice] = D(agrupa['qtd_novos_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - RESCINDIDOS
        #
        sql = SQL_CONTRATOS_RESCINDIDOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_rescindidos_anterior_%s' % indice], agrupa['qtd_rescindidos_anterior_%s' % indice] = dados[0]
            agrupa['vr_rescindidos_anterior_%s' % indice] = D(agrupa['vr_rescindidos_anterior_%s' % indice] or 0)
            agrupa['qtd_rescindidos_anterior_%s' % indice] = D(agrupa['qtd_rescindidos_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - BAIXADOS
        #
        sql = SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_baixados_anterior_%s' % indice], agrupa['qtd_baixados_anterior_%s' % indice] = dados[0]
            agrupa['vr_baixados_anterior_%s' % indice] = D(agrupa['vr_baixados_anterior_%s' % indice] or 0)
            agrupa['qtd_baixados_anterior_%s' % indice] = D(agrupa['qtd_baixados_anterior_%s' % indice] or 0)

        agrupa['vr_anterior_%s' % indice] = agrupa['vr_regulares_anterior_%s' % indice] + agrupa['vr_novos_anterior_%s' % indice]
        agrupa['vr_anterior_%s' % indice] = agrupa['vr_anterior_%s' % indice] or D(1)
        agrupa['qtd_anterior_%s' % indice] = agrupa['qtd_regulares_anterior_%s' % indice] + agrupa['qtd_novos_anterior_%s' % indice]
        agrupa['qtd_anterior_%s' % indice] = agrupa['qtd_anterior_%s' % indice] or D(1)

        #
        # Montamos o filtro do mês atual
        #
        filtro['data_inicial_anterior'] = filtro['data_inicial']
        filtro['data_final_anterior'] = filtro['data_final']
        filtro['data_inicial_competencia_anterior'] = filtro['data_inicial_competencia']
        filtro['data_final_competencia_anterior'] = filtro['data_final_competencia']
        self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, '')

        #
        # Valores agrupados para indicadores - REGULARES
        #
        sql = SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL.format(**filtro)
        #print('regulares')
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_regulares_%s' % indice], agrupa['qtd_regulares_%s' % indice] = dados[0]
            agrupa['vr_regulares_%s' % indice] = D(agrupa['vr_regulares_%s' % indice] or 0)
            agrupa['qtd_regulares_%s' % indice] = D(agrupa['qtd_regulares_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - NOVOS
        #
        sql = SQL_CONTRATOS_NOVOS_ANTERIOR_COMERCIAL.format(**filtro)
        #print('novos')
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_novos_%s' % indice], agrupa['qtd_novos_%s' % indice] = dados[0]
            agrupa['vr_novos_%s' % indice] = D(agrupa['vr_novos_%s' % indice] or 0)
            agrupa['qtd_novos_%s' % indice] = D(agrupa['qtd_novos_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - RESCINDIDOS
        #
        sql = SQL_CONTRATOS_RESCINDIDOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_rescindidos_%s' % indice], agrupa['qtd_rescindidos_%s' % indice] = dados[0]
            agrupa['vr_rescindidos_%s' % indice] = D(agrupa['vr_rescindidos_%s' % indice] or 0)
            agrupa['qtd_rescindidos_%s' % indice] = D(agrupa['qtd_rescindidos_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - BAIXADOS
        #
        sql = SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_baixados_%s' % indice], agrupa['qtd_baixados_%s' % indice] = dados[0]
            agrupa['vr_baixados_%s' % indice] = D(agrupa['vr_baixados_%s' % indice] or 0)
            agrupa['qtd_baixados_%s' % indice] = D(agrupa['qtd_baixados_%s' % indice] or 0)

        #
        # Calcula a média ponderada de perdas
        #
        agrupa['vr_faturamento_%s' % indice] = agrupa['vr_regulares_%s' % indice] + agrupa['vr_novos_%s' % indice]
        agrupa['vr_perdas_%s' % indice] = agrupa['vr_rescindidos_%s' % indice] + agrupa['vr_reducao_%s' % indice]
        agrupa['media_perdas_%s' % indice] = (agrupa['vr_perdas_%s' % indice] * 100)

        if agrupa['vr_faturamento_%s' % indice]:
            agrupa['media_perdas_%s' % indice] /= agrupa['vr_faturamento_%s' % indice]
        else:
            agrupa['media_perdas_%s' % indice] = D(0)

        agrupa['media_perdas_%s' % indice] /= 100
        agrupa['media_perdas_%s' % indice] = agrupa['media_perdas_%s' % indice].quantize(D('0.01'))

        return agrupa

    def gera_relatorio_evolucao_receita(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        filtro = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'company_ids': '',
        }


        SQL_EVOLUCAO_RECEITA = """
        select
            ano_nf,
            data_nf, empresa_id,
            unidade,
            sum(vr_nf) as vr_nf

        from(
            select
                to_char(nf.data_emissao_brasilia, 'YYYY') as ano_nf,
                to_char(nf.data_emissao_brasilia, 'MM/YYYY') as data_nf,
                uni.id as empresa_id,
                uni.name as unidade,
                sum(coalesce(nf.vr_nf, 0)) as vr_nf
            from
                sped_documento nf
                join res_partner cli on cli.id = nf.partner_id
                join res_company uni on uni.id = nf.company_id
                left join finan_contrato fc on fc.id = nf.finan_contrato_id
                left join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
                left join sale_order_sped_documento pednota on pednota.sped_documento_id = nf.id
                left join sale_order ped on ped.id = pednota.sale_order_id
                left join res_users vendedor on vendedor.id = ped.user_id
                left join hr_department posto on posto.id = ped.hr_department_id

            where
                nf.emissao = '0'
                and nf.situacao in ('00','01')
                and nf.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
                and (nf.company_id in ({company_ids}) or uni.parent_id in ({company_ids}))
                and (natop.considera_venda = True or nf.modelo in ('2D', 'SE'))
                {filtro_adicional}

            group by
                ano_nf,
                data_nf,
                empresa_id,
                uni.name
        UNION
            select
                to_char(nf.data_emissao_brasilia, 'YYYY') as ano_nf,
                to_char(nf.data_emissao_brasilia, 'MM/YYYY') as data_nf,
                uni.id as empresa_id,
                uni.name as unidade,
                sum(coalesce(nf.vr_nf, 0) * -1) as vr_nf
            from
                sped_documento nf
                join res_partner cli on cli.id = nf.partner_id
                join res_company uni on uni.id = nf.company_id
                join sped_naturezaoperacao natop on natop.id = nf.naturezaoperacao_id
                left join sped_documentoreferenciado docref on docref.documento_id = nf.id
                left join sped_documento nfdev on nfdev.id = docref.documentoreferenciado_id or nfdev.chave = docref.chave
                left join sale_order_sped_documento pednota on pednota.sped_documento_id = nfdev.id
                left join sale_order ped on ped.id = pednota.sale_order_id
                left join res_users vendedor on vendedor.id = ped.user_id
                left join hr_department posto on posto.id = ped.hr_department_id
            where
                nf.situacao in ('00','01')
                and nf.data_entrada_saida_brasilia between '{data_inicial}' and '{data_final}'
                and (nf.company_id in ({company_ids}) or uni.parent_id in ({company_ids}))
                and natop.considera_devolucao_venda = True


            group by
                ano_nf,
                data_nf,
                empresa_id,
                uni.name
        ) as a

        group by
            ano_nf,
            data_nf,
            empresa_id,
            unidade

        order by
            empresa_id,
            ano_nf,
            data_nf

        """

        rel = Report('Evolução do faturamento', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_evolucao_faturamento.jrxml')
        rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]

        company_ids = []
        for c_obj in rel_obj.company_ids:
            company_ids.append(c_obj.id)

        filtro['company_ids'] = str(company_ids).replace('[', '').replace(']', '')

        filtro['filtro_adicional'] = ''
        texto_filtro = u''
        if rel_obj.grupo_economico_id:
            texto_filtro += rel_obj.grupo_economico_id.nome
            filtro['filtro_adicional'] += ' and fc.grupo_economico_id = ' + str(rel_obj.grupo_economico_id.id)

        if rel_obj.contratos_faturados:
            filtro['filtro_adicional'] += ' and fc.id is not null'

        rel.parametros['SQL_EVOLUCAO_RECEITA'] = SQL_EVOLUCAO_RECEITA.format(**filtro).replace('\n', ' ')
        rel.parametros['TEXTO_FILTRO'] = texto_filtro
        rel.parametros['SOMENTE_CONTRATOS'] = rel_obj.contratos_faturados
        #print(rel.parametros['SQL_EVOLUCAO_RECEITA'])

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Evolucao_Faturamento' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


    def gera_relatorio_analise_faturamento(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        texto_filtro = ''

        #
        # Caso seja informado dia 1º e último dia do mês, as datas seguem o mês calendário,
        # caso contrário, são meses corridos
        #
        if data_inicial == primeiro_dia_mes(data_inicial) and data_final == ultimo_dia_mes(data_final):
            meses = idade_meses_sem_dia(data_inicial, data_final) + 1

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_inicial_anterior = primeiro_dia_mes(data_inicial_anterior)
            data_final_anterior = ultimo_dia_mes(data_inicial_anterior + relativedelta(months=+meses-1))

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(day=1)
            data_final_competencia += relativedelta(months=+1)
            data_final_competencia = ultimo_dia_mes(data_final_competencia)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(day=1)
            data_final_competencia_anterior += relativedelta(months=+1)
            data_final_competencia_anterior = ultimo_dia_mes(data_final_competencia_anterior)

        else:
            meses = idade_meses_sem_dia(data_inicial, data_final)

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_final_anterior = data_final + relativedelta(months=-meses)

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(months=+1)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)

        ####meses = idade_meses_sem_dia(data_inicial, data_final)
        ###meses = 1

        ###data_inicial_anterior = data_inicial + relativedelta(months=-meses)
        ###data_final_anterior = data_final + relativedelta(months=-meses)

        ###data_inicial_competencia = data_inicial + relativedelta(months=+1)
        ###data_final_competencia = data_final + relativedelta(months=+1)

        ###data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
        ###data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)

        filtro = {
            #'campo_data_vencimento': 'data_vencimento',
            'campo_data_vencimento': 'data_vencimento_original',

            'data_inicial': data_inicial,
            'data_final': data_final,
            'data_inicial_competencia': data_inicial_competencia,
            'data_final_competencia': data_final_competencia,
            #'company_id': company_id,
            'company_ids': '',
            'filtro_adicional': '',
            'filtro_adicional_anterior': '',
            'data_inicial_anterior': data_inicial_anterior,
            'data_final_anterior': data_final_anterior,
            'data_inicial_competencia_anterior': data_inicial_competencia_anterior,
            'data_final_competencia_anterior': data_final_competencia_anterior,
        }

        self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, '', filtro_faturamento=True)

        ###filtro = {
            ###'data_inicial': data_inicial,
            ###'data_final': data_final,
            ###'company_ids': company_id,
            ###'filtro_adicional': '',
            ###'data_inicial_anterior': data_inicial_anterior,
            ###'data_final_anterior': data_final_anterior,
        ###}

        ###if rel_obj.vendedor_id:
            ###texto_filtro = u'Vendedor: ' + rel_obj.vendedor_id.name
            ###filtro['filtro_adicional'] = 'and vendedor.id = ' + str(rel_obj.vendedor_id.id)

        ###if len(rel_obj.hr_department_ids):
            ###if len(texto_filtro) > 0:
                ###texto_filtro += u'; '

            ###texto_filtro += u'Posto '
            ###posto_ids = []
            ###for posto_obj in rel_obj.hr_department_ids:
                ###posto_ids.append(posto_obj.id)
                ###texto_filtro += u', ' + posto_obj.name

            ###texto_filtro = texto_filtro.replace(u'Posto , ', u'Posto ')
            ###filtro['filtro_adicional'] += ' and ped.hr_department_id in ({postos})'.format(postos=posto_ids).replace('[', '').replace(']', '')

        ####if rel_obj.hr_department_id:
            ####if len(texto_filtro) > 0:
                ####texto_filtro += u'; '

            ####texto_filtro += u'Posto: ' + rel_obj.hr_department_id.name
            ####filtro['filtro_adicional'] += 'and ped.hr_department_id = ' + str(rel_obj.hr_department_id.id)

        rel = Report('Análise de Faturamento', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_analise_faturamento.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['IS_SINTETICO'] = rel_obj.tipo_rel
        rel.parametros['SQL_FATURAMENTO_PRODUTO'] = SQL_FATURAMENTO_PRODUTO.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_DEVOLUCAO_PRODUTO'] = SQL_DEVOLUCAO_PRODUTO.format(**filtro).replace('\n', ' ')
        rel.parametros['SQL_RESUMO_FATURAMENTO'] = SQL_RESUMO_FATURAMENTO.format(**filtro).replace('\n', ' ')
        rel.parametros['FILTRO_ADICIONAL'] = texto_filtro

        print(SQL_FATURAMENTO_PRODUTO.format(**filtro))

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Analise_Faturamento_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }

        rel.outputFormat = 'xls'
        pdf, formato = rel.execute()

        dados['nome_csv'] = dados['nome'].replace('.pdf', '.xls')
        dados['arquivo_csv'] = base64.encodestring(pdf)

        rel_obj.write(dados)

        return True

    def gera_relatorio_curva_abc_contratos(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id, context=context)
        #company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        texto_filtro = ''

        #
        # Caso seja informado dia 1º e último dia do mês, as datas seguem o mês calendário,
        # caso contrário, são meses corridos
        #
        if data_inicial == primeiro_dia_mes(data_inicial) and data_final == ultimo_dia_mes(data_final):
            meses = idade_meses_sem_dia(data_inicial, data_final) + 1

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_inicial_anterior = primeiro_dia_mes(data_inicial_anterior)
            data_final_anterior = ultimo_dia_mes(data_inicial_anterior + relativedelta(months=+meses-1))

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(day=1)
            data_final_competencia += relativedelta(months=+1)
            data_final_competencia = ultimo_dia_mes(data_final_competencia)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(day=1)
            data_final_competencia_anterior += relativedelta(months=+1)
            data_final_competencia_anterior = ultimo_dia_mes(data_final_competencia_anterior)

        else:
            meses = idade_meses_sem_dia(data_inicial, data_final)

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_final_anterior = data_final + relativedelta(months=-meses)

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(months=+1)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)

        ####meses = idade_meses_sem_dia(data_inicial, data_final)
        ###meses = 1

        ###data_inicial_anterior = data_inicial + relativedelta(months=-meses)
        ###data_final_anterior = data_final + relativedelta(months=-meses)

        ###data_inicial_competencia = data_inicial + relativedelta(months=+1)
        ###data_final_competencia = data_final + relativedelta(months=+1)

        ###data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
        ###data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)


        filtro = {
            #'campo_data_vencimento': 'data_vencimento',
            'campo_data_vencimento': 'data_vencimento_original',

            'data_inicial': data_inicial,
            'data_final': data_final,
            'data_inicial_competencia': data_inicial_competencia,
            'data_final_competencia': data_final_competencia,
            #'company_id': company_id,
            'company_ids': '',
            'filtro_adicional': '',
            'filtro_adicional_anterior': '',
            'data_inicial_anterior': data_inicial_anterior,
            'data_final_anterior': data_final_anterior,
            'data_inicial_competencia_anterior': data_inicial_competencia_anterior,
            'data_final_competencia_anterior': data_final_competencia_anterior,
        }

        print('data inicial e final ' + formata_data(data_inicial) + ' e ' + formata_data(data_final))
        print('data inicial e final do periodo anterior ' + formata_data(data_inicial_anterior)  + ' e ' +  formata_data(data_final_anterior))
        print('data inicial e final do vencimento (competencia) ' + formata_data(data_inicial_competencia)  + ' e ' + formata_data(data_final_competencia))
        print('data inicial e final do vencimento (competencia) anterior ' + formata_data(data_inicial_competencia_anterior)  + ' e ' + formata_data(data_final_competencia_anterior))

        #if rel_obj.company_2_id:
        #    filtro['company_ids'] += ', ' + str(rel_obj.company_2_id.id)

        rel = Report('ABC de Contratos', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_curva_abc_contratos.jrxml')
        rel.outputFormat = rel_obj.formato
        rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        #rel.parametros['IS_SINTETICO'] = rel_obj.tipo_rel

        texto_filtro = u''
        texto_filtro = self.pool.get('finan.relatorio')._monta_filtro(cr, uid, rel_obj, filtro, texto_filtro)
        #print(texto_filtro)

        rel.parametros['SQL_CONTRATOS_REGULARES'] = SQL_CONTRATOS_ABC_GERAL.format(**filtro).replace('\n', ' ')
        rel.parametros['FILTRO_ADICIONAL'] = texto_filtro

        pdf, formato = rel.execute()

        dados = {
            'nome': u'curva_abc_contratos_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


finan_relatorio()
