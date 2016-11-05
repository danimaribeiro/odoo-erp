# -*- coding:utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime, ultimo_dia_mes, formata_data, primeiro_dia_mes, idade_meses
from copy import copy
from osv import fields, osv
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from hr_salary_rule import *
from pybrasil.data import hora_decimal_to_horas_minutos_segundos, horas_minutos_segundos_to_horario_decimal


class hr_payslip_media(osv.osv):
    _name = 'hr.payslip.media'
    _description = u'Médias de rubricas'
    _rec_name = 'nome'
    _order = 'slip_id, titulo desc, digitado desc'

    _columns = {
        'slip_id': fields.many2one('hr.payslip', u'Holerite'),
        'contract_id': fields.related('slip_id', 'contract_id', type='many2one', relation='hr.contract', string=u'Contrato'),
        'employee_id': fields.related('slip_id', 'employee_id', type='many2one', relation='hr.employee', string=u'Empregado'),
        'company_id': fields.related('slip_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'tipo_media': fields.selection(TIPO_MEDIA, u'Média para férias/rescisão'),
        'ultimos_meses': fields.boolean(u'Últimos meses?'),
        'nome': fields.char(u'Rubrica', size=60),
        'mes_01': fields.char(u'1º mês', size=30),
        'mes_02': fields.char(u'2º mês', size=30),
        'mes_03': fields.char(u'3º mês', size=30),
        'mes_04': fields.char(u'4º mês', size=30),
        'mes_05': fields.char(u'5º mês', size=30),
        'mes_06': fields.char(u'6º mês', size=30),
        'mes_07': fields.char(u'7º mês', size=30),
        'mes_08': fields.char(u'8º mês', size=30),
        'mes_09': fields.char(u'9º mês', size=30),
        'mes_10': fields.char(u'10º mês', size=30),
        'mes_11': fields.char(u'11º mês', size=30),
        'mes_12': fields.char(u'12º mês', size=30),
        'total': fields.float(u'Total'),
        'total_texto': fields.char(u'Total', size=30),
        'meses': fields.float(u'Meses'),
        'media': fields.float(u'Média'),
        'media_texto': fields.char(u'Média', size=30),
        'digitado': fields.boolean(u'Digitado?'),
        'titulo': fields.boolean(u'Títulos?'),
        'proporcao': fields.float(u'12 avos'),
    }


hr_payslip_media()


class hr_payslip(osv.osv):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'media_ids': fields.one2many('hr.payslip.media', 'slip_id', u'Médias'),
        'media_periodo_aquisitivo_ids': fields.one2many('hr.payslip.media', 'slip_id', u'Médias', domain=[('ultimos_meses', '=', False)]),
        'media_ultimos_meses_ids': fields.one2many('hr.payslip.media', 'slip_id', u'Médias', domain=[('ultimos_meses', '=', True)]),
    }

    _SQL_MEDIA = u"""
    select
        cast(coalesce(hl.{campo}, 0.00) as numeric(18,2))

    from
        hr_payslip h
        join hr_payslip_line hl on hl.slip_id = h.id and hl.holerite_anterior_line_id is null
        join hr_salary_rule r on r.id = hl.salary_rule_id

    where
        h.tipo in {tipos}
        and (
            (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
            or
            (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
        )
        and h.contract_id in ({contract_id})
        and (
            (h.simulacao is null or h.simulacao = False)
            or
            (r.tipo_media in ('valor', 'valor_ultimos_meses') and h.complementar = True and h.simulacao = True)
        )
        and coalesce(hl.{campo}, 0.00) > 0
        and r.id = {rule_id};
    """

    _SQL_MEDIA_VARIAVEL = u"""
    select
        cast(coalesce(hi.amount, 0.00) as numeric(18,2))

    from
        hr_payslip h
        join hr_payslip_input hi on hi.payslip_id = h.id
        join hr_salary_rule r on r.id = hi.rule_id

    where
        h.tipo in {tipos}
        and (
            (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
            or
            (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
        )
        and (h.simulacao is null or h.simulacao = False)
        and h.contract_id in ({contract_id})
        and coalesce(hi.amount, 0.00) > 0
        and r.id = {rule_id};
    """

    _SQL_MEDIA_AFASTAMENTO = u"""
    select
        cast(coalesce(ha.dias_afastamento, 0.00) as numeric(18,2))

    from
        hr_payslip h
        join hr_payslip_afastamento ha on ha.payslip_id = h.id
        join hr_salary_rule r on r.id = ha.rule_id

    where
        h.tipo in {tipos}
        and (
            (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
            or
            (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
        )
        and (h.simulacao is null or h.simulacao = False)
        and h.contract_id in ({contract_id})
        and r.id = {rule_id};
    """

    _SQL_RUBRICAS_MEDIAS = u"""
    select distinct
        m.id

    from (
    select
        r.id

    from
             hr_payslip h
        join hr_payslip_line hl on hl.slip_id = h.id and hl.holerite_anterior_line_id is null
        join hr_salary_rule r on r.id = hl.salary_rule_id

    where
        h.tipo in {tipos}
        and (
            (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
            or
            (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
        )
        and (h.simulacao is null or h.simulacao = False)
        and h.contract_id in ({contract_id})
        and r.tipo_media is not null
        and
            (r.tipo_media in ({tipos_medias})
            and
            case
               when (r.tipo_media = 'valor' or r.tipo_media = 'valor_ultimos_meses') then coalesce(hl.total, 0.00)
               when (r.tipo_media = 'quantidade' or r.tipo_media = 'quantidade_ultimos_meses') then coalesce(hl.quantity, 0.00)
            end > 0
        )
        --and r.tipo_media != 'calculada'

    union all

    select
        r.id

    from
        hr_payslip h
        join hr_payslip_input hi on hi.payslip_id = h.id
        join hr_salary_rule r on r.id = hi.rule_id

    where
        h.tipo in {tipos}
        and (
            (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
            or
            (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
        )
        and (h.simulacao is null or h.simulacao = False)
        and h.contract_id in ({contract_id})
        and r.tipo_media is not null
        and r.tipo_media not in ('quantidade', 'valor', 'quantidade_ultimos_meses', 'valor_ultimos_meses')
        and coalesce(hi.amount, 0.00) > 0
        -- and r.tipo_media != 'calculada'
    ) as m;
    """

    def calcula_medias(self, cr, uid, ids, context={}):
        if not ids:
            return

        for holerite_obj in self.browse(cr, uid, ids, context=context):
            holerite_obj._calcula_medias(context=context)

            if holerite_obj.tipo == 'F':
                holerite_obj._calcula_medias(ultimos_meses=True, context=context)

    def _calcula_medias(self, cr, uid, ids, ultimos_meses=False, context={}):
        if not ids:
            return

        media_pool = self.pool.get('hr.payslip.media')
        rubrica_pool = self.pool.get('hr.salary.rule')

        for holerite_obj in self.browse(cr, uid, ids, context=context):
            proporcao = D(12)

            if holerite_obj.tipo == 'R':
                data_base = parse_datetime(holerite_obj.data_afastamento).date()

            elif holerite_obj.tipo == 'F':
                if ultimos_meses:
                    data_base = parse_datetime(holerite_obj.date_from).date()
                else:
                    data_base = parse_datetime(holerite_obj.data_fim_periodo_aquisitivo).date()

                if data_base.day >= 15:
                    data_base += relativedelta(months=+1)

                proporcao = D(holerite_obj.dias_ferias or 0) / D('2.5')  # Meses de direito a férias

                if holerite_obj.abono_pecuniario_ferias:
                    proporcao += 4

            elif holerite_obj.tipo == 'D':
                data_base = parse_datetime(holerite_obj.date_from).date()
                proporcao = data_base.month

                ##
                ## 1ª parcela, tira 1 mês da proporção caso essa não seja de 12
                ## meses
                ##
                #if '-11-' in holerite_obj.date_from and proporcao < 12:
                    #proporcao -= D(1)

            elif holerite_obj.tipo == 'A':
                data_base = parse_datetime(holerite_obj.date_from).date()

            elif holerite_obj.tipo == 'M':
                #
                # Licença maternidade são 6 meses de média
                #
                data_base = parse_datetime(holerite_obj.date_to).date()
                proporcao = 6

            elif holerite_obj.tipo == 'C':
                #
                # Auxílio acidente de trabalho são 12 meses de média
                #
                data_base = parse_datetime(holerite_obj.date_to).date()
                proporcao = 12

            if not ultimos_meses:
                cr.execute('delete from hr_payslip_media where slip_id = {id} and (digitado is null or not digitado);'.format(id=holerite_obj.id))

            #
            # Trata o mês de contratação com menos de 15 dias trabalhados
            #
            data_contratacao = parse_datetime(holerite_obj.contract_id.date_start).date()

            #if holerite_obj.contract_id.unidade_salario != '1':

            if holerite_obj.tipo != 'F':
                fim_mes = ultimo_dia_mes(data_contratacao)
                dias_corridos_mes = fim_mes.toordinal() - data_contratacao.toordinal() + 1
                if dias_corridos_mes < 15:
                    data_contratacao = fim_mes + relativedelta(days=+1)

            data_contratacao = str(data_contratacao)[:10]

            meses = []
            total_meses = 0
            primeira_data = None
            ultima_data = None
            #for i in range(12):
            for i in range(proporcao):
                #
                # Simulação do 13º para inclusão da dif. de médias na folha de dezembro
                #
                if holerite_obj.media_inclui_mes or (holerite_obj.tipo == 'D' and holerite_obj.contract_id.date_end and holerite_obj.contract_id.date_end[:7] == holerite_obj.contract_id.date_start[:7]):
                    data_inicial = data_base + relativedelta(day=1, months=0 - i)
                else:
                    data_inicial = data_base + relativedelta(day=1, months=-1 - i)

                data_final = ultimo_dia_mes(data_inicial)
                titulo = formata_data(data_inicial, '%B/%Y')
                #print('data_inicial, data_final, titulo, proporcao')
                #print(data_inicial, data_final, titulo, proporcao)

                if str(data_inicial)[:7] >= data_contratacao[:7]:
                    if holerite_obj.tipo != 'D' or str(data_inicial)[:7] >= (holerite_obj.date_from[:5] + '01'):
                        #
                        # Verifica se houve perda por afastamento no período
                        #
                        filtro_afastamento = {
                            'data_inicial': str(data_inicial)[:10],
                            'data_final': str(data_final)[:10],
                            'contract_id': str(holerite_obj.contract_id.id),
                            'tipos': "('N')",
                        }

                        if holerite_obj.contract_id.contrato_transf_id:
                            filtro_afastamento['contract_id'] += ', ' + str(holerite_obj.contract_id.contrato_transf_id.id)

                        sql = holerite_obj.contract_id._SQL_HOLERITE_AFASTADO.format(**filtro_afastamento)
                        #print(sql)
                        cr.execute(sql)
                        dados_afastamento = cr.fetchall()
                        mes_afastado = len(dados_afastamento)
                        #print('mes_afastado, data_inicial, data_final')
                        ##print(mes_afastado, data_inicial, data_final)

                        if mes_afastado > 0:
                            continue

                        meses.append([data_inicial, data_final, titulo])
                        total_meses += 1

                        if ultima_data is None:
                            ultima_data = data_final

                        primeira_data = data_inicial

            #print('total_meses, meses, primeira_data, ultima_data')
            #print(total_meses, meses, primeira_data, ultima_data)
            if not meses or not primeira_data or not ultima_data:
                continue

            if holerite_obj.tipo == 'N' or holerite_obj.tipo == 'D':
                proporcao = total_meses

            ####
            #### No adiantamento, ou quando for horista ou vendedor, paga
            #### proporcional ao período de meses; caso contrário, paga
            #### até dezembro mesmo
            ####
            ###idade_contrato = idade_meses(holerite_obj.contract_id.date_start, holerite_obj.date_to)
            ###if holerite_obj.contract_id.unidade_salario != '1' and \
                ###idade_contrato >= 12 and '-12-' in holerite_obj.date_to and total_meses < 12:
                ###total_meses += 1

            dados_media_modelo = {
                'slip_id': holerite_obj.id,
                'nome': u'',
                'mes_01': ' ',
                'mes_02': ' ',
                'mes_03': ' ',
                'mes_04': ' ',
                'mes_05': ' ',
                'mes_06': ' ',
                'mes_07': ' ',
                'mes_08': ' ',
                'mes_09': ' ',
                'mes_10': ' ',
                'mes_11': ' ',
                'mes_12': ' ',
                'total': 0,
                'meses': 0,
                'media': 0,
                'proporcao': 12,
                'digitado': False,
                'titulo': False,
                'ultimos_meses': ultimos_meses,
            }

            dados_media = {
                'slip_id': holerite_obj.id,
                'nome': u'Meses',
                'mes_01': meses[0][2] if len(meses) >= 1 else u' ',
                'mes_02': meses[1][2] if len(meses) >= 2 else u' ',
                'mes_03': meses[2][2] if len(meses) >= 3 else u' ',
                'mes_04': meses[3][2] if len(meses) >= 4 else u' ',
                'mes_05': meses[4][2] if len(meses) >= 5 else u' ',
                'mes_06': meses[5][2] if len(meses) >= 6 else u' ',
                'mes_07': meses[6][2] if len(meses) >= 7 else u' ',
                'mes_08': meses[7][2] if len(meses) >= 8 else u' ',
                'mes_09': meses[8][2] if len(meses) >= 9 else u' ',
                'mes_10': meses[9][2] if len(meses) >= 10 else u' ',
                'mes_11': meses[10][2] if len(meses) >= 11 else u' ',
                'mes_12': meses[11][2] if len(meses) >= 12 else u' ',
                'total': False,
                'meses': False,
                'media': False,
                'proporcao': False,
                'digitado': False,
                'titulo': True,
                'ultimos_meses': ultimos_meses,
            }

            media_pool.create(cr, uid, dados_media)

            dados_filtro = {
                'data_inicial': primeira_data,
                'data_final': ultima_data,
                'contract_id': str(holerite_obj.contract_id.id),
                'tipos': "('N', 'R')",
            }

            if holerite_obj.contract_id.contrato_transf_id:
                dados_filtro['contract_id'] += ', ' + str(holerite_obj.contract_id.contrato_transf_id.id)

            #print('data contratacao, data rescisao')
            #print(holerite_obj.contract_id.date_start[:7], holerite_obj.contract_id.date_end[:7])

            #if holerite_obj.contract_id.date_end and holerite_obj.contract_id.date_start[:7] == holerite_obj.contract_id.date_end[:7]:
                #dados_filtro['tipos'] = "('N', 'R')"

            if holerite_obj.tipo == 'F':
                if ultimos_meses:
                    dados_filtro['tipos_medias'] = "'valor_ultimos_meses', 'quantidade_ultimos_meses'"
                else:
                    dados_filtro['tipos_medias'] = "'valor', 'quantidade'"
            else:
                dados_filtro['tipos_medias'] = "'valor', 'quantidade', 'valor_ultimos_meses', 'quantidade_ultimos_meses'"

            sql = self._SQL_RUBRICAS_MEDIAS.format(**dados_filtro)
            print(sql)
            cr.execute(sql)
            dados_rubrica = cr.fetchall()
            rubrica_ids = []
            for r_id, in dados_rubrica:
                rubrica_ids.append(r_id)

            sql_ja_existe = u'select id from hr_payslip_media where slip_id = {slip_id} and rule_id = {rule_id};'
            for rubrica_obj in rubrica_pool.browse(cr, uid, rubrica_ids):
                if rubrica_obj.tipo_media:
                    if holerite_obj.tipo == 'D' and rubrica_obj.ignora_media_13:
                        continue

                    if holerite_obj.tipo in ('F', 'N') and rubrica_obj.tipo_media == 'afastamento':
                        continue

                    cr.execute(sql_ja_existe.format(slip_id=holerite_obj.id, rule_id=rubrica_obj.id))
                    ja_existe = cr.fetchall()

                    if len(ja_existe) > 0:
                        continue

                    total = D(0)
                    dados_media = copy(dados_media_modelo)
                    dados_media['rule_id'] = rubrica_obj.id
                    dados_media['nome'] = rubrica_obj.name
                    dados_media['tipo_media'] = rubrica_obj.tipo_media
                    dados_media['titulo'] = False
                    dados_media['proporcao'] = D(proporcao)

                    for i in range(len(meses)):
                        data_inicial, data_final, titulo = meses[i]
                        dados_filtro = {
                            'tipos': "('N', 'R')",
                            'data_inicial': data_inicial,
                            'data_final': data_final,
                            'company_id': holerite_obj.company_id.id,
                            'rule_id': rubrica_obj.id,
                            'contract_id': str(holerite_obj.contract_id.id),
                            'campo': 'total' if rubrica_obj.tipo_media in ('valor', 'valor_ultimos_meses') else 'quantity',
                            'tipo_media': rubrica_obj.tipo_media,
                        }

                        if holerite_obj.contract_id.contrato_transf_id:
                            dados_filtro['contract_id'] += ', ' + str(holerite_obj.contract_id.contrato_transf_id.id)

                        #if holerite_obj.contract_id.date_end and holerite_obj.contract_id.date_start[:7] == holerite_obj.contract_id.date_end[:7]:
                            #dados_filtro['tipos'] = "('N', 'R')"

                        #
                        # Para calcular a média de horas trabalhadas
                        #
                        #print(rubrica_obj.category_id.code)
                        if rubrica_obj.category_id.code == 'BASE_TRIB':
                            sql = self._SQL_MEDIA_VARIAVEL.format(**dados_filtro)
                        elif rubrica_obj.tipo_media == 'afastamento':
                            sql = self._SQL_MEDIA_AFASTAMENTO.format(**dados_filtro)
                        else:
                            sql = self._SQL_MEDIA.format(**dados_filtro)

                        #print(sql)

                        cr.execute(sql)
                        valores = cr.fetchall()

                        #
                        # No caso de rubricas variaveis, verifica se houve
                        # digitação manual na tela de variáveis de média
                        #
                        if not len(valores) and rubrica_obj.category_id.code == 'BASE_TRIB':
                            sql = self._SQL_MEDIA.format(**dados_filtro)
                            cr.execute(sql)
                            valores = cr.fetchall()

                        if len(valores):
                            valor = D(valores[0][0])

                            #
                            # Na Patrimonial, até 31/07, os DSRs eram calculados
                            # dividindo o valor original por 6 SEMPRE
                            #
                            if cr.dbname.lower() == 'patrimonial' and rubrica_obj.code.startswith('DSR_') and str(data_final) <= '2015-07-31' and rubrica_obj.tipo_media == 'quantidade':
                                valor /= D(6)

                            #
                            # Para os afastamentos do INSS (licença maternidade),
                            # considera somente aqueles que tem pelo menos 15 dias
                            # e nesses casos considera que o mês todo será
                            # pago pelo INSS
                            #
                            if rubrica_obj.tipo_media == 'afastamento':
                                if valor >= 15:
                                    total += D(30)

                            elif rubrica_obj.tipo_media == 'calculada':
                                total += D(1)

                            #elif rubrica_obj.tipo_media == 'quantidade' and rubrica_obj.manual_horas:
                                #total += D(time_float(valor))

                            else:
                                total += valor

                            if rubrica_obj.manual_horas:
                                horas, minutos, segundos = hora_decimal_to_horas_minutos_segundos(valor)
                                dados_media['mes_' + str(i + 1).zfill(2)] = '%02d:%02d (%s)' % (horas, minutos, formata_valor(valor))

                            else:
                                dados_media['mes_' + str(i + 1).zfill(2)] = formata_valor(valor)

                    total = total.quantize(D('0.01'))

                    #
                    # Para os afastamentos do INSS (licença maternidade)
                    # divide pelo total de meses que está realmente afastado,
                    # e desconsidera a proporcionalidade
                    #
                    if rubrica_obj.tipo_media == 'afastamento':
                        media = total / D(30)
                    elif rubrica_obj.tipo_media == 'calculada':
                        media = total
                    else:
                        media = total / D(total_meses)

                    media = media.quantize(D('0.01'))

                    #
                    # Aplica a proporção
                    #
                    if rubrica_obj.tipo_media in ('afastamento', 'calculada'):
                        dados_media['total'] = total
                        dados_media['media'] = media
                        dados_media['meses'] = media
                        dados_media['proporcao'] = media
                        dados_media['total_texto'] = formata_valor(total)
                        dados_media['media_texto'] = formata_valor(media)

                    else:
                        #print(total, media, proporcao)
                        #
                        # Poporção dos avos somente para não-horistas
                        #
                        #if holerite_obj.contract_id.unidade_salario != '1':

                        ##if cr.dbname.lower() == 'protefort' or holerite_obj.contract_id.unidade_salario != '1':
                            ##if holerite_obj.tipo == 'M':
                                ##media *= D(proporcao) / D(6)
                                ###media *= total_meses / D(proporcao)
                            ##else:
                                ##media *= D(proporcao) / D(12)
                                ###media *= total_meses / D(proporcao)

                        if holerite_obj.tipo == 'M':
                            media *= D(proporcao) / D(6)
                            #media *= total_meses / D(proporcao)
                        else:
                            #pass
                            media *= D(proporcao) / D(12)
                            #media *= total_meses / D(proporcao)

                        media = media.quantize(D('0.01'))
                        #print(total, media, proporcao)

                        dados_media['total'] = total
                        dados_media['total_texto'] = formata_valor(total)
                        dados_media['media'] = media
                        dados_media['media_texto'] = formata_valor(media)
                        dados_media['meses'] = total_meses

                        if rubrica_obj.manual_horas:
                            horas, minutos, segundos = hora_decimal_to_horas_minutos_segundos(media)
                            dados_media['media_texto'] = '%02d:%02d (%s)' % (horas, minutos, formata_valor(media))
                            media = horas_minutos_segundos_to_horario_decimal(horas, minutos, segundos)
                            dados_media['media'] = media

                            horas, minutos, segundos = hora_decimal_to_horas_minutos_segundos(total)
                            dados_media['total_texto'] = '%02d:%02d (%s)' % (horas, minutos, formata_valor(total))

                    media_pool.create(cr, uid, dados_media)

            #cr.execute('delete from hr_payslip_media where slip_id = {id} and media = 0 and titulo != True;'.format(id=holerite_obj.id))

        variavel_pool = self.pool.get('hr.payslip.input')

        for holerite_obj in self.browse(cr, uid, ids):
            #
            # Lança agora as médias calculadas nas variáveis
            #
            for media_obj in holerite_obj.media_ids:
                if not media_obj.rule_id:
                    continue
                cr.execute('delete from hr_payslip_input where payslip_id = {slip_id} and rule_id = {rule_id};'.format(slip_id=holerite_obj.id, rule_id=media_obj.rule_id.id))
                dados_variavel = {
                    'payslip_id': holerite_obj.id,
                    'employee_id': holerite_obj.employee_id.id,
                    'contract_id': holerite_obj.contract_id.id,
                    'rule_id': media_obj.rule_id.id,
                    'amount': media_obj.media,
                    'data_inicial': holerite_obj.date_from,
                    'data_final': holerite_obj.date_to,
                }
                variavel_pool.create(cr, uid, dados_variavel, context={'calcula_medias': True})

