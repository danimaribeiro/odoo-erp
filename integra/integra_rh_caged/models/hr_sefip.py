# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from integra_rh.constantes_rh import *
from pybrasil.data import parse_datetime, hoje, dia_util_pagamento
from datetime import date
from pybrasil.valor.decimal import Decimal as D, ROUND_DOWN
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
import base64
import re
from sefip import *
from dateutil.relativedelta import relativedelta
from copy import copy


MESES = (
    ('1', 'janeiro'),
    ('2', 'fevereiro'),
    ('3', 'março'),
    ('4', 'abril'),
    ('5', 'maio'),
    ('6', 'junho'),
    ('7', 'julho'),
    ('8', 'agosto'),
    ('9', 'setembro'),
    ('10', 'outubro'),
    ('11', 'novembro'),
    ('12', 'dezembro'),
    ('13', 'décimo terceiro'),
)

MESES_DIC = dict(MESES)

SITUACAO_SEFIP = (
    ('aberto', u'Aberto'),
    ('fechado', u'Fechado'),
)


class hr_sefip(orm.Model):
    _name = 'hr.sefip'
    _description = 'Arquivo SEFIP'
    _order = 'ano desc, cast(mes as integer) desc, data desc, company_id'

    def get_payslip_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        holerite_pool = self.pool.get('hr.payslip')

        for sefip_obj in self.browse(cr, uid, ids):
            if sefip_obj.mes == '13':
                data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, 12)
            else:
                data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, int(sefip_obj.mes))
            data_inicial = str(data_inicial)
            data_final = str(data_final)

            sql_arquivo = """
            select
                h.id as holerite_id
            """

            if sefip_obj.mes != '13':
                if sefip_obj.codigo_recolhimento_fgts in ('650', '660'):
                    sql_arquivo += self.SQL_FROM + self.SQL_WHERE_FECHAMENTO_COMPLEMENTAR.format(data_inicial=data_inicial, data_final=data_final, cnpj=sefip_obj.company_id.partner_id.cnpj_cpf[:10])
                else:
                    sql_arquivo += self.SQL_FROM + self.SQL_WHERE_FECHAMENTO.format(data_inicial=data_inicial, data_final=data_final, cnpj=sefip_obj.company_id.partner_id.cnpj_cpf[:10])
            else:
                sql_arquivo += self.SQL_FROM + self.SQL_WHERE_FECHAMENTO_13.format(data_inicial=data_inicial, data_final=data_final, cnpj=sefip_obj.company_id.partner_id.cnpj_cpf[:10])

            sql_arquivo += """
                order by
                    e.nome;"""

            cr.execute(sql_arquivo)
            holerite_ids_lista = cr.fetchall()
            holerite_ids = []
            for dados in holerite_ids_lista:
                holerite_ids.append(dados[0])
            res[sefip_obj.id] = holerite_ids

        return res

    _columns = {
        'state': fields.selection(SITUACAO_SEFIP, u'Situação', select=True),

        'company_id': fields.many2one('res.company', u'Empresas', select=True, ondelete='restrict'),
        'responsavel_id': fields.many2one('res.company', u'Empresa responsável', select=True, ondelete='restrict'),
        'employee_id': fields.many2one('hr.employee', u'Contato', select=True, ondelete='restrict'),
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'indicador_recolhimento_fgts': fields.selection(INDICADOR_RECOLHIMENTO_FGTS, u'Recolhimento FGTS'),
        'data_recolhimento_fgts': fields.date(u'Data de recolhimento do FGTS'),
        'indicador_recolhimento_gps': fields.selection(INDICADOR_RECOLHIMENTO_GPS, u'Recolhimento GPS'),
        'data_recolhimento_gps': fields.date(u'Data de recolhimento da GPS'),
        'modalidade_arquivo': fields.selection(MODALIDADE_ARQUIVO_SEFIP, u'Modalidade do arquivo'),
        'codigo_recolhimento_fgts': fields.selection(CODIGO_RECOLHIMENTO_SEFIP, u'Código de recolhimento'),
        'centralizadora': fields.selection(CENTRALIZA_FGTS, u'Centralizadora'),
        'codigo_fpas': fields.char(u'Código FPAS', size=3),
        'codigo_outras_entidades': fields.char(u'Código outras entidades', size=4),
        'codigo_recolhimento_gps': fields.char(u'Código recolhimento GPS', size=4),
        'vr_inss_empresa': fields.float(u'Valor apurado para INSS empresa'),
        'vr_inss_rat': fields.float(u'Valor apurado para INSS RAT (somente quando depósito judicial)'),
        'payslip_ids': fields.function(get_payslip_ids, type='one2many', relation='hr.payslip', method=True, string=u'Holerites'),

        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'data': fields.date(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),

        'processo_numero': fields.float(u'Nº do processo', digits=(11, 0)),
        'processo_ano': fields.integer(u'Ano'),
        'processo_vara': fields.integer(u'Vara/JCJ'),
        'processo_inicial': fields.date(u'Data de início'),
        'processo_final': fields.date(u'Data de término'),
    }

    _defaults = {
        'data': fields.date.today,
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'indicador_recolhimento_fgts': '1',
        'indicador_recolhimento_gps': '1',
        'codigo_recolhimento_fgts': '150',
        'modalidade_arquivo': '0',
        'centralizadora': '0',
        'codigo_fpas': '515',
        'codigo_outras_entidades': '0115',
        'codigo_recolhimento_gps': '2100',
        'state': 'aberto',
    }

    def unlink(self, cr, uid, ids, context={}):
        for so in self.browse(cr, uid, ids):
            if so.state == 'fechado':
                raise osv.except_osv(u'Erro!', u'Não é permitida a exclusão de arquivo fechado e transmitido!')

        res = super(hr_sefip, self).unlink(cr, uid, ids, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if not dados:
            return True

        for so in self.browse(cr, uid, ids):
            if so.state == 'fechado' and len(dados) != 1:
                raise osv.except_osv(u'Erro!', u'Não é permitida a alteração de arquivo fechado e transmitido!')

        res = super(hr_sefip, self).write(cr, uid, ids, dados, context=context)

        return res

    def abre_arquivo(self, cr, uid, ids, context={}):
        for id in ids:
            sql = "update hr_sefip set state='aberto' where id = " + str(id) + ";"
            cr.execute(sql)

    def fecha_arquivo(self, cr, uid, ids, context={}):
        for so in self.browse(cr, uid, ids, context=context):
            so.write({'state': 'fechado'})

            if so.mes == '13':
                data_inicial, data_final = primeiro_ultimo_dia_mes(so.ano, 12)
            else:
                data_inicial, data_final = primeiro_ultimo_dia_mes(so.ano, int(so.mes))
            data_inicial = str(data_inicial)
            data_final = str(data_final)

            sql = """
            select
                h.id as holerite_id
            """ + self.SQL_FROM

            if so.mes != '13':
                sql += self.SQL_WHERE_FECHAMENTO
            else:
                sql += self.SQL_WHERE_FECHAMENTO_13

            sql = sql.format(data_inicial=data_inicial, data_final=data_final, cnpj=so.company_id.partner_id.cnpj_cpf[:10])

            cr.execute("""
                update hr_payslip set state = 'done' where id in
                (""" + sql + """);""")

    def onchange_mes_ano(self, cr, uid, ids, mes, ano, company_id):
        #
        # Calcula as datas de pagamento das guias conforme o mês e ano
        #
        if not mes or not ano or not company_id:
            return

        res = {}
        valores = {}
        res['value'] = valores

        if mes == '13':
            mes = '12'
            valores['indicador_recolhimento_fgts'] = '0'

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        data_ref = date(ano, int(mes), 1)
        data_ref += relativedelta(months=+1)
        estado = company_obj.partner_id.estado or ''
        municipio = company_obj.partner_id.cidade or ''

        #
        # Vencimento do FGTS é sempre dia 7 do mês seguinte
        #
        venc_fgts = date(data_ref.year, data_ref.month, 7)
        valores['data_recolhimento_fgts'] = str(dia_util_pagamento(venc_fgts, estado, (estado, municipio), antecipa=True))

        #
        # Vencimento da GPS é sempre no dia 20 do mês seguinte
        #
        venc_inss = date(data_ref.year, data_ref.month, 20)
        valores['data_recolhimento_gps'] = str(dia_util_pagamento(venc_inss, estado, (estado, municipio), antecipa=True))


        return res

    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        retorno = {}
        valores = {}
        retorno['value'] = valores

        if not company_id:
            return retorno

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        #
        # Regime tributário SIMPLES
        #
        if company_obj.regime_tributario == '1':
            valores['codigo_recolhimento_gps'] = '2003'
            valores['codigo_fpas'] = '507'
            valores['codigo_recolhimento_fgts'] = '115'

        ##
        ## Regime tributário lucro presumido
        ##
        #elif company_obj.al_pis_cofins_id.al_pis == 0.65:
            #valores['codigo_recolhimento_gps'] = '2003'

        #
        # Regime tributário lucro real
        #
        else:
            valores['codigo_recolhimento_gps'] = '2100'
            valores['codigo_fpas'] = '515'
            valores['codigo_recolhimento_fgts'] = '150'

        return retorno

    def _cria_tomador(self, cr, uid, sefip, tomador_empresa, data_inicial, data_final, tomador_cnpj, empregado_nis=''):
        partner_pool = self.pool.get('res.partner')

        if tomador_cnpj in sefip.tomadores:
            tomador = sefip.tomadores[tomador_cnpj]
        elif tomador_cnpj == tomador_empresa.cnpj:
            sefip.tomadores[tomador_cnpj] = tomador_empresa
            tomador = tomador_empresa
        else:
            partner_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', tomador_cnpj)], order='id', limit=1)[0]
            partner_obj = partner_pool.browse(cr, 1, partner_id)

            tomador = Tomador()
            tomador.sefip = sefip
            try:
                tomador.cnpj = partner_obj.cnpj_cpf
                tomador.razao_social = partner_obj.razao_social or partner_obj.name
                tomador.endereco = partner_obj.endereco or ''
                tomador.bairro = partner_obj.bairro or ''
                tomador.cidade = partner_obj.municipio_id.nome
                tomador.estado = partner_obj.municipio_id.estado_id.uf
                tomador.cep = partner_obj.cep or ''
            except:
                if empregado_nis:
                    raise osv.except_osv(u'Erro!', u'O cadastro do tomador CNPJ {cnpj}, empregado PIS {pis} está com problemas!'.format(cnpj=partner_obj.cnpj_cpf, pis=empregado_nis))
                else:
                    raise osv.except_osv(u'Erro!', u'O cadastro do tomador CNPJ {cnpj} está com problemas!'.format(cnpj=partner_obj.cnpj_cpf))

            if sefip.mes != 13:
                if not tomador.cnpj:
                    if empregado_nis:
                        raise osv.except_osv(u'Erro!', u'O cadastro do tomador CNPJ {cnpj}, empregado PIS {pis} está com problemas!'.format(cnpj=partner_obj.cnpj_cpf, pis=empregado_nis))
                    else:
                        raise osv.except_osv(u'Erro!', u'O cadastro do tomador CNPJ {cnpj} está com problemas!'.format(cnpj=partner_obj.cnpj_cpf))

                cr.execute("""
                    select
                    coalesce(sum(d.bc_previdencia), 0.00) as bc_previdencia,
                    coalesce(sum(d.vr_previdencia), 0.00) as vr_previdencia

                    from sped_documento d
                    join res_company c on c.id = d.company_id
                    join res_partner p on p.id = c.partner_id
                    join res_partner f on f.id = d.partner_id

                    where
                    p.cnpj_cpf = '""" + tomador_empresa.cnpj + """'
                    and cast(d.data_emissao as date) between '""" + data_inicial + """' and '""" + data_final + """'
                    and f.cnpj_cpf = '""" + tomador.cnpj + """'
                    and d.vr_previdencia > 0
                    and d.emissao = '0'
                    and (d.situacao = '00' or d.situacao is null);
                    """)

                retencoes = cr.fetchall()

                if sefip.codigo_recolhimento == '211':
                    tomador.valor_faturado = D(retencoes[0][0])

                if sefip.codigo_recolhimento in ['150', '155']:
                    tomador.valor_retido = D(retencoes[0][1])

            sefip.tomadores[tomador_cnpj] = tomador

        return tomador

    def _cria_empregado_rateio(self, cr, uid, sefip, empregado_nis, proporcao, tomador):
        empregado_original = sefip.empregados[empregado_nis]

        #if empregado_nis in tomador.empregados:
            #empregado_novo = tomador.empregados[empregado_nis]
        #else:
        empregado_novo = Empregado()
        empregado_novo.sefip = empregado_original.sefip
        empregado_novo.nis = empregado_original.nis
        empregado_novo.data_admissao = empregado_original.data_admissao
        empregado_novo.categoria_trabalhador = empregado_original.categoria_trabalhador
        empregado_novo.nome = empregado_original.nome
        empregado_novo.matricula = empregado_original.matricula
        empregado_novo.carteira_trabalho_numero = empregado_original.carteira_trabalho_numero
        empregado_novo.carteira_trabalho_serie = empregado_original.carteira_trabalho_serie
        empregado_novo.data_opcao_fgts = empregado_original.data_opcao_fgts
        empregado_novo.data_nascimento = empregado_original.data_nascimento
        empregado_novo.cbo = empregado_original.cbo
        empregado_novo.movimentacoes = empregado_original.movimentacoes

        for m in empregado_novo.movimentacoes:
            empregado_novo.movimentacoes[m].empregado = empregado_novo

        #
        # Valores em proporção e arredondados
        #
        empregado_novo.salario_liquido += D(empregado_original.salario_liquido) * proporcao
        empregado_novo.decimo_terceiro_liquido += D(empregado_original.decimo_terceiro_liquido) * proporcao
        empregado_novo.base_inss += D(empregado_original.base_inss) * proporcao
        empregado_novo.base_decimo_terceiro_rescisao += D(empregado_original.base_decimo_terceiro_rescisao) * proporcao
        empregado_novo.base_decimo_terceiro += D(empregado_original.base_decimo_terceiro) * proporcao
        empregado_novo.valor_inss += D(empregado_original.valor_inss) * proporcao
        empregado_novo.salario_familia += D(empregado_original.salario_familia) * proporcao
        empregado_novo.salario_maternidade += D(empregado_original.salario_maternidade) * proporcao

        if empregado_nis == '12713266531_581':
            print(empregado_original.salario_liquido, proporcao, D(empregado_original.salario_liquido) * proporcao)

        empregado_novo.salario_liquido = empregado_novo.salario_liquido.quantize(D('0.01'))
        empregado_novo.decimo_terceiro_liquido = empregado_novo.decimo_terceiro_liquido.quantize(D('0.01'))
        empregado_novo.base_inss = empregado_novo.base_inss.quantize(D('0.01'))
        empregado_novo.base_decimo_terceiro_rescisao = empregado_novo.base_decimo_terceiro_rescisao.quantize(D('0.01'))
        empregado_novo.base_decimo_terceiro = empregado_novo.base_decimo_terceiro.quantize(D('0.01'))
        empregado_novo.valor_inss = empregado_novo.valor_inss.quantize(D('0.01'))
        empregado_novo.salario_familia = empregado_novo.salario_familia.quantize(D('0.01'))
        empregado_novo.salario_maternidade = empregado_novo.salario_maternidade.quantize(D('0.01'))

        #
        # Certifica de que a base do INSS tenha pelo menos R$ 0,01
        #
        if empregado_novo.base_inss < D('0.01'):
            empregado_novo.base_inss = D('0.01')

        return empregado_novo

    def _gera_rateio_tomadores(self, cr, uid, sefip, tomador_empresa, data_inicial, data_final):

        sql = """
select
    p.cnpj_cpf, e.nis || '_' || c.id as nis, e.nome, h.dias_saldo_salario, h.tipo
from
    (
        select
            ca.contract_id,
            ca.data_alteracao,
            ca.lotacao_id,
            (
                select
                    caa.data_alteracao
                from
                    hr_contract_alteracao caa
                where
                        caa.contract_id = ca.contract_id
                    and caa.tipo_alteracao = ca.tipo_alteracao
                    and caa.data_alteracao > ca.data_alteracao
                order by
                    caa.data_alteracao
                limit 1
            ) as data_limite
        from
            hr_contract_alteracao ca
        where
            ca.tipo_alteracao = 'L'

        union

        select
            c.id,
            c.date_start,
            case
                when c.lotacao_id is null then cc.partner_id
                else c.lotacao_id
            end as lotacao_id,
            (
                select
                    caa.data_alteracao
                from
                    hr_contract_alteracao caa
                where
                        caa.contract_id = c.id
                    and caa.tipo_alteracao = 'L'
                    and caa.data_alteracao > c.date_start
                order by
                    caa.data_alteracao
                limit 1
            ) as data_limite
        from
            hr_contract c
            join res_company cc on cc.id = c.company_id
    ) as lotacao
left join res_partner p on p.id = lotacao.lotacao_id
join hr_contract c on c.id = lotacao.contract_id
join hr_employee e on e.id = c.employee_id
join res_company cp on cp.id = c.company_id
join res_partner pp on pp.id = cp.partner_id
join hr_payslip h on h.contract_id = c.id and (h.simulacao is null or h.simulacao = False)
"""

        if sefip.mes == 13:
            sql += """
where
            (h.tipo = 'D'
            and h.date_from >= '{data_inicial}'
            and h.date_to <= '{data_final}')
            and pp.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
and lotacao.data_alteracao <= '{data_final}'
and (lotacao.data_limite is null
or lotacao.data_limite > '{data_inicial}')

order by p.cnpj_cpf, 2;
            """.format(data_inicial=data_inicial, data_final=data_final, cnpj=tomador_empresa.cnpj)

        elif sefip.codigo_recolhimento in ('650', '660'):
            sql += """
where
            h.complementar = True
            and ((h.tipo = 'N'
            and h.data_complementar between '{data_inicial}' and '{data_final}')
            or (h.tipo = 'R' and h.data_complementar between '{data_inicial}' and '{data_final}'))
            and pp.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
and lotacao.data_alteracao <= '{data_final}'
and (lotacao.data_limite is null
or lotacao.data_limite > '{data_inicial}')

order by p.cnpj_cpf, 2;
            """.format(data_inicial=data_inicial, data_final=data_final, cnpj=tomador_empresa.cnpj)

        else:
            sql += """
where
            ((h.tipo = 'N'
            and h.date_from >= '{data_inicial}'
            and h.date_to <= '{data_final}')
            or (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}'))
            and pp.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
and lotacao.data_alteracao <= '{data_final}'
and (lotacao.data_limite is null
or lotacao.data_limite > '{data_inicial}')

order by p.cnpj_cpf, 2;
            """.format(data_inicial=data_inicial, data_final=data_final, cnpj=tomador_empresa.cnpj)

        #print(sql)

        cr.execute(sql)

        lista_rateio = cr.fetchall()

        for tomador_cnpj, empregado_nis, nome_empregado, dias_saldo_salario, tipo_holerite in lista_rateio:
            if sefip.mes == 13 and empregado_nis not in sefip.empregados:
                continue

            tomador = self._cria_tomador(cr, uid, sefip, tomador_empresa, data_inicial, data_final, tomador_cnpj, empregado_nis)
            #
            # Agora, ajusta os possíveis períodos diferentes
            # em que o funcionário possa ter sido alocado
            #
            sql = """
                select
                    p.cnpj_cpf,
                    a.data_alteracao

                from
                    hr_contract_alteracao a
                    join hr_contract c on c.id = a.contract_id
                    join hr_employee e on e.id = c.employee_id
                    join res_partner p on p.id = a.lotacao_id

                where
                    a.tipo_alteracao = 'L'
                    and e.nis = '""" + empregado_nis.split('_')[0] + """'
                    and c.id = """ + empregado_nis.split('_')[1] + """
                    and a.data_alteracao <= '""" + data_final + """'

                order by
                    a.data_alteracao desc;
            """

            #if empregado_nis == "12713266531_581":
                #print(sql)

            #print(sql)

            cr.execute(sql)

            rateios = cr.fetchall()
            if dias_saldo_salario < 30 and dias_saldo_salario > 0:
                dias_mes = dias_saldo_salario
            else:
                dias_mes = parse_datetime(data_final) - parse_datetime(data_inicial)
                dias_mes = dias_mes.days + 1

            #
            # Totais para ajuste de centavos
            #
            total_salario_liquido = D(0)
            total_decimo_terceiro_liquido = D(0)
            total_base_inss = D(0)
            total_base_decimo_terceiro_rescisao = D(0)
            total_base_decimo_terceiro = D(0)
            total_valor_inss = D(0)
            total_salario_familia = D(0)
            total_salario_maternidade = D(0)

            data_anterior = parse_datetime(data_final)

            ajustar = False
            p_total = 0
            passou_primeiro = False
            for tomador_cnpj, data_alteracao in rateios:
                if data_alteracao < data_inicial:
                    if str(data_anterior)[:10] == data_inicial:
                        continue
                    else:
                        data_alteracao = data_inicial

                ajuste = 0
                if data_anterior == parse_datetime(data_final) and not passou_primeiro:
                    ajuste = 1
                    passou_primeiro = True

                data_alteracao = parse_datetime(data_alteracao)
                dias = data_anterior - data_alteracao
                dias = dias.days + ajuste

                if dias > dias_mes:
                    dias = dias_mes

                #if empregado_nis == "12713266531_581":
                    #print(data_alteracao, dias, ajuste)

                if tipo_holerite == 'R':
                    proporcao = D(1)
                else:
                    proporcao = D(dias) / D(dias_mes)

                p_total += proporcao

                data_anterior = data_alteracao

                tomador = self._cria_tomador(cr, uid, sefip, tomador_empresa, data_inicial, data_final, tomador_cnpj)

                if proporcao == 1:
                    empregado_novo = sefip.empregados[empregado_nis]
                else:
                    empregado_novo = self._cria_empregado_rateio(cr, uid, sefip, empregado_nis, proporcao, tomador)
                    ajustar = True

                if nome_empregado == 'ODACIR ANTONIO PIRES':
                    print(nome_empregado, empregado_nis, tomador.razao_social, ajuste, proporcao, dias, data_alteracao, empregado_novo.salario_liquido)

                empregado_novo.tomador = tomador
                tomador.empregados[empregado_nis] = empregado_novo

                #
                # Acumula os totais
                #
                total_salario_liquido += empregado_novo.salario_liquido
                total_decimo_terceiro_liquido += empregado_novo.decimo_terceiro_liquido
                total_base_inss += empregado_novo.base_inss
                total_base_decimo_terceiro_rescisao += empregado_novo.base_decimo_terceiro_rescisao
                total_base_decimo_terceiro += empregado_novo.base_decimo_terceiro
                total_valor_inss += empregado_novo.valor_inss
                total_salario_familia += empregado_novo.salario_familia
                total_salario_maternidade += empregado_novo.salario_maternidade

            #
            # Não teve subalocação ao longo do mês, só a do contrato
            #
            if p_total == 0:
                empregado_novo = sefip.empregados[empregado_nis]
                empregado_novo.tomador = tomador
                tomador.empregados[empregado_nis] = empregado_novo

            #
            # Por fim, ajusta os centavos, caso haja necessidade
            #
            if ajustar:
                empregado_original = sefip.empregados[empregado_nis]                #empregado_novo.salario_liquido -= total_salario_liquido - empregado_original.salario_liquido
                empregado_novo.decimo_terceiro_liquido -= total_decimo_terceiro_liquido - empregado_original.decimo_terceiro_liquido
                empregado_novo.base_inss -= total_base_inss - empregado_original.base_inss
                empregado_novo.base_decimo_terceiro_rescisao -= total_base_decimo_terceiro_rescisao - empregado_original.base_decimo_terceiro_rescisao
                empregado_novo.base_decimo_terceiro -= total_base_decimo_terceiro - empregado_original.base_decimo_terceiro
                empregado_novo.valor_inss -= total_valor_inss - empregado_original.valor_inss
                empregado_novo.salario_familia -= total_salario_familia - empregado_original.salario_familia
                empregado_novo.salario_maternidade -= total_salario_maternidade - empregado_original.salario_maternidade
                empregado_novo.salario_liquido -= total_salario_liquido - empregado_original.salario_liquido
                empregado_novo.decimo_terceiro_liquido -= total_decimo_terceiro_liquido - empregado_original.decimo_terceiro_liquido
                empregado_novo.base_inss -= total_base_inss - empregado_original.base_inss
                empregado_novo.base_decimo_terceiro_rescisao -= total_base_decimo_terceiro_rescisao - empregado_original.base_decimo_terceiro_rescisao
                empregado_novo.base_decimo_terceiro -= total_base_decimo_terceiro - empregado_original.base_decimo_terceiro
                empregado_novo.valor_inss -= total_valor_inss - empregado_original.valor_inss
                empregado_novo.salario_familia -= total_salario_familia - empregado_original.salario_familia
                empregado_novo.salario_maternidade -= total_salario_maternidade - empregado_original.salario_maternidade

    SQL_FROM = """
        from
            hr_payslip h
            join hr_contract c on c.id = h.contract_id
            join res_company cp on cp.id = c.company_id
            join res_partner p on p.id = cp.partner_id
            join hr_employee e on e.id = h.employee_id
            join hr_payroll_structure s on s.id = h.struct_id
    """

    SQL_WHERE = """
        where
            h.tipo in ('N', 'R') and (h.simulacao is null or h.simulacao = False)
            and (
                (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                or (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
            )
            and p.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
    """

    SQL_WHERE_FECHAMENTO = """
        where
            h.tipo = 'N'
            and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
            and p.cnpj_cpf like '{cnpj}%'
    """

    SQL_WHERE_13 = """
        where
            h.tipo = 'D'
            and (h.simulacao is null or h.simulacao = False)
            and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
            and p.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
    """

    SQL_WHERE_FECHAMENTO_13 = """
        where
            h.tipo = 'D'
            and (h.simulacao is null or h.simulacao = False)
            and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
            and p.cnpj_cpf like '{cnpj}%'
    """

    SQL_WHERE_COMPLEMENTAR = """
        where
            h.tipo in ('N', 'R')
            and (h.simulacao is null or h.simulacao = False)
            -- and h.complementar = True
            and (
                (h.tipo = 'N' and h.data_complementar between '{data_inicial}' and '{data_final}')
                or (h.tipo = 'R' and h.data_complementar between '{data_inicial}' and '{data_final}')
            )
            and p.cnpj_cpf = '{cnpj}'
            and c.categoria_trabalhador != '901'
    """

    SQL_WHERE_FECHAMENTO_COMPLEMENTAR = """
        where
            h.tipo = 'N'
            and h.complementar = True
            and h.data_complementar between '{data_inicial}' and '{data_final}'
            and p.cnpj_cpf like '{cnpj}%'
    """

    def _sql_arquivo(self, cr, uid, sefip_obj, company_obj):
        if sefip_obj.mes == '13':
            data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, 12)
        else:
            data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, int(sefip_obj.mes))

        data_inicial = str(data_inicial)
        data_final = str(data_final)

        sql_arquivo = """
        select
            h.id as holerite_id,
            h.data_afastamento,
            h.data_pagamento,
            s.codigo_afastamento,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
                join hr_salary_rule_category rc on rc.id = r.category_id
            where
                hi.slip_id = h.id
                and rc.sinal = '+'
            ), 0) as proventos,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
                join hr_salary_rule_category rc on rc.id = r.category_id
            where
                hi.slip_id = h.id
                and rc.sinal = '-'
            ), 0) as deducoes,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                -- and r.code in ('BASE_INSS', 'BASE_INSS_13', 'BASE_INSS_13_AP') and hi.code != 'BASE_INSS_anterior'
                and r.code in ('BASE_INSS') and hi.code != 'BASE_INSS_anterior'
            ), 0) as base_inss,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                -- and r.code in ('INSS', 'INSS_13', 'INSS_13_AP')
                and r.code in ('INSS')
            ), 0) as valor_inss,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code = 'SALFAM'
            ), 0) as salario_familia,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code = 'LICENCA_MATERNIDADE'
            ), 0) as licenca_maternidade,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code in ('BASE_INSS_13', 'BASE_INSS_13_AP', 'BASE_FGTS_13') and hi.code != 'BASE_INSS_anterior'
            ), 0) as base_inss_13,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code in ('INSS_13', 'INSS_13_AP')
            ), 0) as valor_inss_13,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code in ('AUX_ACIDENTE_TRABALHO', 'PERICULOSIDADE_AUX_ACIDENTE_TRABALHO', 'ADNOT_AUX_ACIDENTE_TRABALHO', 'H50_AUX_ACIDENTE_TRABALHO', 'MEDIA_VAR_AUX_ACIDENTE_TRABALHO')
            ), 0) as acidente_trabalho,
            coalesce((select
                sum(hi.total)
            from
                hr_payslip_line hi
                join hr_salary_rule r on r.id = hi.salary_rule_id
            where
                hi.slip_id = h.id
                and r.code in ('INSS_INDIVIDUAL')
            ), 0) as valor_inss_individual
            """

        sql_arquivo += self.SQL_FROM

        if sefip_obj.mes == '13':
            sql_arquivo += self.SQL_WHERE_13.format(data_inicial=data_inicial, data_final=data_final, cnpj=company_obj.partner_id.cnpj_cpf)
        elif sefip_obj.codigo_recolhimento_fgts in ('650', '660'):
            sql_arquivo += self.SQL_WHERE_COMPLEMENTAR.format(data_inicial=data_inicial, data_final=data_final, cnpj=company_obj.partner_id.cnpj_cpf)
        else:
            sql_arquivo += self.SQL_WHERE.format(data_inicial=data_inicial, data_final=data_final, cnpj=company_obj.partner_id.cnpj_cpf)

        sql_arquivo += """
            order by
                e.nis, c.date_start;"""

        return sql_arquivo

    def _gera_arquivo(self, cr, uid, sefip_obj, company_obj, arquivo_texto=None, context={}):
        sefip = SEFIP()

        if sefip_obj.responsavel_id:
            sefip.cnpj_responsavel = sefip_obj.responsavel_id.partner_id.cnpj_cpf
            sefip.razao_social_responsavel = sefip_obj.responsavel_id.partner_id.razao_social
        else:
            sefip.cnpj_responsavel = company_obj.partner_id.cnpj_cpf
            sefip.razao_social_responsavel = company_obj.partner_id.razao_social

        sefip.cnpj = company_obj.partner_id.cnpj_cpf
        sefip.razao_social = company_obj.partner_id.razao_social
        sefip.contato = sefip_obj.employee_id.nome
        sefip.endereco = company_obj.partner_id.endereco + ' ' + company_obj.partner_id.numero
        sefip.bairro = company_obj.partner_id.bairro or ''
        sefip.cidade = company_obj.partner_id.municipio_id.nome
        sefip.estado = company_obj.partner_id.municipio_id.estado_id.uf
        sefip.cep = company_obj.partner_id.cep or ''
        sefip.telefone = company_obj.partner_id.fone or ''
        sefip.email = sefip_obj.employee_id.user_id.user_email or ''
        sefip.ano = sefip_obj.ano
        sefip.mes = int(sefip_obj.mes)

        #if sefip.mes != 13:
        sefip.codigo_recolhimento = sefip_obj.codigo_recolhimento_fgts
        sefip.indicador_recolhimento_fgts = sefip_obj.indicador_recolhimento_fgts

        if sefip_obj.data_recolhimento_fgts:
            sefip.data_recolhimento_fgts = parse_datetime(sefip_obj.data_recolhimento_fgts)

        sefip.indicador_recolhimento_gps = sefip_obj.indicador_recolhimento_gps
        sefip.modalidade_arquivo = sefip_obj.modalidade_arquivo

        #else:
            #sefip.codigo_recolhimento = sefip_obj.codigo_recolhimento_fgts
            #sefip.indicador_recolhimento_fgts = '0'
            #sefip.indicador_recolhimento_gps = '0'
            #sefip.modalidade_arquivo = sefip_obj.modalidade_arquivo

        if sefip_obj.data_recolhimento_gps:
            sefip.data_recolhimento_gps = parse_datetime(sefip_obj.data_recolhimento_gps)

        if company_obj.partner_id.cnae_id:
            sefip.cnae = company_obj.partner_id.cnae_id.codigo
        else:
            sefip.cnpae = '8121400'

        sefip.aliquota_rat = 3.0 if company_obj.regime_tributario != '1' else 0
        sefip.centralizadora = sefip_obj.centralizadora
        sefip.simples = '2' if company_obj.regime_tributario == '1' else '1'
        sefip.codigo_fpas = sefip_obj.codigo_fpas
        sefip.codigo_outras_entidades = sefip_obj.codigo_outras_entidades if company_obj.regime_tributario != '1' else ''
        sefip.codigo_recolhimento_gps = sefip_obj.codigo_recolhimento_gps
        sefip.salario_familia = 0
        sefip.salario_maternidade = 0
        sefip.cooperativas = 0

        if sefip.codigo_recolhimento in ('650', '660'):
            sefip.processo_numero = str(sefip_obj.processo_numero or 0).replace('.00', '').replace('.0', '')
            sefip.processo_ano = str(sefip_obj.processo_ano or 0)
            sefip.processo_vara = str(sefip_obj.processo_vara or 0)
            sefip.processo_inicial = str(sefip_obj.processo_inicial).replace('-', '')[:6]
            sefip.processo_final = str(sefip_obj.processo_final).replace('-', '')[:6]

        primeira_empresa = False
        if arquivo_texto is None:
            arquivo_texto = sefip.registro()
            primeira_empresa = True

        if sefip_obj.mes == '13':
            data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, 12)
        else:
            data_inicial, data_final = primeiro_ultimo_dia_mes(sefip_obj.ano, int(sefip_obj.mes))

        data_inicial = str(data_inicial)
        data_final = str(data_final)

        cr.execute(self._sql_arquivo(cr, uid, sefip_obj, company_obj))

        print(self._sql_arquivo(cr, uid, sefip_obj, company_obj))

        resumo_holerites = cr.fetchall()

        #
        # Não há funcionários na empresa?
        #
        if len(resumo_holerites) == 0:
            return arquivo_texto, None

        #
        # No 13º não informa os valores de cooperativas
        #
        if sefip_obj.mes != '13':
            cr.execute("""
                select
                coalesce(sum(d.bc_previdencia), 0.00) as bc_previdencia,
                coalesce(sum(d.vr_previdencia), 0.00) as vr_previdencia

                from sped_documento d
                join res_company c on c.id = d.company_id
                join res_partner p on p.id = c.partner_id
                join res_partner f on f.id = d.partner_id

                where
                p.cnpj_cpf = '""" + company_obj.partner_id.cnpj_cpf + """'
                and cast(d.data_emissao as date) between '""" + data_inicial + """' and '""" + data_final + """'
                and d.vr_previdencia > 0
                and d.emissao = '1'
                and d.situacao = '00'
                and f.eh_cooperativa = True;
                """)

            cooperativas = cr.fetchall()
            sefip.cooperativas = cooperativas[0][1] / (15.0 / 100.0)

        #
        # Cria um tomador que é a própria empresa
        #
        tomador = Tomador()
        tomador.sefip = sefip
        tomador.cnpj = sefip.cnpj
        tomador.razao_social = sefip.razao_social
        tomador.endereco = sefip.endereco
        tomador.bairro = sefip.bairro
        tomador.cidade = sefip.cidade
        tomador.estado = sefip.estado
        tomador.cep = sefip.cep

        #
        # Cria agora todos os empregados
        #
        total_salario_familia = 0
        total_salario_maternidade = 0

        holerite_pool = self.pool.get('hr.payslip')
        for holerite_id, data_afastamento, data_pagamento, codigo_afastamento, proventos, deducoes, base_inss, valor_inss, salario_familia, salario_maternidade, base_inss_13, inss_13, acidente_trabalho, valor_inss_individual in resumo_holerites:
            #
            # Na competência 13 não entra os afastados: 13º zerado
            #
            if sefip_obj.mes == '13' and base_inss <= 0:
                continue

            holerite_obj = holerite_pool.browse(cr, uid, holerite_id)
            contrato_obj = holerite_obj.contract_id
            empregado_obj = holerite_obj.employee_id
            empregado_obj.nis = empregado_obj.nis + '_' + str(contrato_obj.id)

            #
            # O mesmo empregado pode constar várias vezes nos holerites, por causa
            # das rescisões e rescisões complementares
            #
            if empregado_obj.nis in sefip.empregados:
                empregado = sefip.empregados[empregado_obj.nis]

                #
                # INSS individual gera ocorrência 05
                #
                if valor_inss_individual:
                    empregado.ocorrencia = '05'

                if sefip.mes != 13:
                    empregado.salario_liquido += base_inss + acidente_trabalho
                    empregado.decimo_terceiro_liquido += base_inss_13
                    #empregado.salario_liquido = proventos
                    #empregado.salario_liquido = proventos - deducoes
                    empregado.base_inss += D(base_inss)

                    print(empregado_obj.nome, data_afastamento)
                    if data_afastamento:
                        if codigo_afastamento not in ['H'] and data_afastamento[5:10] < '12-20':
                            empregado.base_decimo_terceiro_rescisao += D(base_inss_13)
                    else:
                        empregado.base_decimo_terceiro += D(base_inss_13)

                    empregado.valor_inss += D(valor_inss)

                    empregado.salario_familia += D(salario_familia)
                    empregado.salario_maternidade += D(salario_maternidade)

                else:
                    #empregado.decimo_terceiro_liquido += base_inss + acidente_trabalho
                    empregado.base_decimo_terceiro_rescisao += D(base_inss)
                    #empregado.base_inss += D(base_inss)
                    #empregado.valor_inss += D(valor_inss)

                    empregado.salario_familia += D(salario_familia)
                    empregado.salario_maternidade += D(salario_maternidade)

            else:
                empregado = Empregado()
                empregado.sefip = sefip
                empregado.nis = empregado_obj.nis
                sefip.empregados[empregado.nis] = empregado

                #
                # INSS individual gera ocorrência 05
                #
                if valor_inss_individual:
                    empregado.ocorrencia = '05'

                #
                # Não aloca mais automaticamente
                # em caso de codigo de recolhimento 150 - rateio por tomadores
                #
                if sefip.codigo_recolhimento != '150':  # or sefip.mes == 13:
                    empregado.tomador = tomador
                    tomador.empregados[empregado.nis] = empregado

                empregado.data_admissao = parse_datetime(contrato_obj.date_start).date()

                #
                # Autônomo
                #
                if contrato_obj.categoria_trabalhador in ['701', '702', '703']:
                    empregado.categoria_trabalhador = '13'

                #
                # Pro-labore
                #
                elif contrato_obj.categoria_trabalhador in ['721', '722']:
                    empregado.categoria_trabalhador = '11'

                #
                # Aprendiz
                #
                elif contrato_obj.categoria_trabalhador == '103':
                    empregado.categoria_trabalhador = '07'

                else:
                    empregado.categoria_trabalhador = '01'
                empregado.nome = empregado_obj.nome
                empregado.matricula = contrato_obj.name or ''
                empregado.carteira_trabalho_numero = empregado_obj.carteira_trabalho_numero or ''
                try:
                    if empregado_obj.carteira_trabalho_serie:
                        empregado.carteira_trabalho_serie = str(int(empregado_obj.carteira_trabalho_serie.strip()))
                except:
                    empregado.carteira_trabalho_serie = empregado_obj.carteira_trabalho_serie or ''

                #empregado.data_opcao_fgts = parse_datetime(contrato_obj.data_opcao_fgts or contrato_obj.date_start).date()
                empregado.data_opcao_fgts = parse_datetime(contrato_obj.date_start).date()

                if empregado_obj.data_nascimento:
                    empregado.data_nascimento = parse_datetime(empregado_obj.data_nascimento).date()

                if contrato_obj.job_id.cbo_id:
                    empregado.cbo = contrato_obj.job_id.cbo_id.codigo

                if sefip_obj.mes != '13':
                    empregado.salario_liquido = base_inss + D(acidente_trabalho)
                    #empregado.salario_liquido = proventos
                    #empregado.salario_liquido = proventos - deducoes
                    empregado.decimo_terceiro_liquido = D(base_inss_13)
                    empregado.base_inss = D(base_inss)

                    #
                    # É rescisão ou não?
                    #
                    print(empregado_obj.nome, data_afastamento)
                    if data_afastamento:
                        if codigo_afastamento not in ['H']:
                            if base_inss_13 > 0 and (data_afastamento[5:10] < '12-20' and ((not data_pagamento) or data_pagamento[5:10] < '12-20')):
                                empregado.base_decimo_terceiro_rescisao = D(base_inss_13)
                            elif holerite_obj.tipo == 'R' and base_inss < 0.01:
                                empregado.base_decimo_terceiro_rescisao = D('0.01')

                    else:
                        empregado.base_decimo_terceiro = D(base_inss_13)

                    empregado.valor_inss = D(valor_inss)
                    empregado.valor_inss_decimo_terceiro = D(inss_13)

                    empregado.salario_familia = D(salario_familia)
                    empregado.salario_maternidade = D(salario_maternidade)
                else:
                    #empregado.decimo_terceiro_liquido = base_inss + D(acidente_trabalho)
                    empregado.base_decimo_terceiro_rescisao = base_inss
                    empregado.salario_familia = D(salario_familia)
                    empregado.salario_maternidade = D(salario_maternidade)

            total_salario_familia += D(salario_familia)
            total_salario_maternidade += D(salario_maternidade)

            #
            # Movimentações / Afastamentos
            #
            cr.execute("""
                select
                r.codigo_afastamento,
                a.data_inicial,
                a.data_final

                from hr_payslip_afastamento ha
                join hr_afastamento a on ha.afastamento_id = a.id
                join hr_salary_rule r on r.id = a.rule_id

                where
                ha.payslip_id = """ + str(holerite_id) + """
                and r.codigo_afastamento is not null;
                --and r.code = 'LICENCA_MATERNIDADE';
            """)

            if data_afastamento or codigo_afastamento:
                movimento = Movimentacao()
                movimento.sefip = sefip
                movimento.empregado = empregado
                movimento.codigo = codigo_afastamento
                if holerite_obj.data_complementar:
                    movimento.data = parse_datetime(holerite_obj.data_complementar)
                elif data_afastamento:
                    movimento.data = parse_datetime(data_afastamento)
                else:
                    movimento.data = parse_datetime(holerite_obj.date_from)
                empregado.movimentacoes[movimento.codigo] = movimento

            else:
                movimentacoes = cr.fetchall()
                for codigo_afastamento, data_inicio, data_retorno in movimentacoes:
                    data_inicio = parse_datetime(data_inicio) + relativedelta(days=-1)

                    if data_retorno:
                        data_retorno = parse_datetime(data_retorno) + relativedelta(days=-1)

                        if str(data_retorno)[:10] <= data_inicial:
                            continue

                    movimento = Movimentacao()
                    movimento.sefip = sefip
                    movimento.empregado = empregado
                    movimento.codigo = codigo_afastamento
                    movimento.data = data_inicio
                    empregado.movimentacoes[movimento.codigo] = movimento

                    if data_retorno and str(data_retorno)[:10] <= data_final:
                        movimento = Movimentacao()
                        movimento.sefip = sefip
                        movimento.empregado = empregado
                        movimento.data = data_retorno
                        movimento.codigo = TIPO_RETORNO[codigo_afastamento]
                        empregado.movimentacoes[movimento.codigo] = movimento


        if sefip.codigo_recolhimento not in ['150', '155', '608']:
            sefip.salario_familia = D(total_salario_familia)

        sefip.salario_maternidade = D(total_salario_maternidade)
        arquivo_texto += sefip.registro_10()
        arquivo_texto += sefip.registro_12()

        #
        # Aplica agora o rateio entre os clientes
        #
        if sefip.codigo_recolhimento == '150': # and sefip.mes != 13:
            self._gera_rateio_tomadores(cr, uid, sefip, tomador, data_inicial, data_final)
        else:
            sefip.tomadores[tomador.cnpj] = tomador

        #
        # Acumula o salário família e maternidade
        #
        if sefip.codigo_recolhimento in ['150', '155', '608']:
            for cnpj, tomador in sefip.tomadores.iteritems():
                if len(tomador.empregados) == 0:
                    continue

                total_salario_familia = 0
                total_salario_maternidade = 0

                for nis, empregado in tomador.empregados.iteritems():
                    total_salario_familia += D(empregado.salario_familia)
                    total_salario_maternidade += D(empregado.salario_maternidade)
                    #if cnpj == '83.310.441/0022-41':
                        #print(empregado.nome, nis, total_salario_familia, total_salario_maternidade)

                tomador.salario_familia = D(total_salario_familia)
                tomador.salario_maternidade = D(total_salario_maternidade)

        #
        # Ajusta a ordem dos registros
        #
        sefip.reordena_tomadores()

        for cnpj, tomador in sefip.tomadores.iteritems():
            if len(tomador.empregados) == 0:
                continue

            if sefip.codigo_recolhimento == '150': # and sefip.mes != 13:
                arquivo_texto += tomador.registro()

            for nis, empregado in tomador.empregados.iteritems():
                #if empregado.salario_liquido == 0 and empregado.base_decimo_terceiro_rescisao == 0:
                    #continue
                empregado.tomador = tomador
                arquivo_texto += empregado.registro()

                for codigo_movimento, movimento in empregado.movimentacoes.iteritems():
                    movimento.empregado.tomador = tomador
                    arquivo_texto += movimento.registro()

        #arquivo_texto += sefip.registro_90()

        return arquivo_texto, sefip

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return True

        for sefip_obj in self.browse(cr, uid, ids):
            cnpj = sefip_obj.company_id.partner_id.cnpj_cpf

            if sefip_obj.modalidade_arquivo == '0' or sefip_obj.mes == '13':
                raiz_cnpj = cnpj[:10]
            else:
                raiz_cnpj = cnpj

            cr.execute("""
                select distinct
                p.cnpj_cpf

                from res_company c
                join res_partner p on p.id = c.partner_id
                join sped_municipio m on m.id = p.municipio_id
                join sped_cnae cn on cn.id = p.cnae_id

                where
                p.cnpj_cpf != ''
                and p.cnpj_cpf like '""" + raiz_cnpj +  """%'

                order by
                p.cnpj_cpf;
            """)

            lista_cnpjs = cr.fetchall()
            cnpjs = []
            for lista_cnpj in lista_cnpjs:
                cnpjs.append(lista_cnpj[0])

            print(raiz_cnpj, lista_cnpjs)

            arquivo_texto = None
            ultimo_sefip = None
            for cnpj in cnpjs:
                cr.execute("""
                    select
                        c.id
                    from
                        res_company c
                        join res_partner p on p.id = c.partner_id
                    where
                        p.cnpj_cpf = '""" + cnpj + """'
                    limit 1;
                """)
                company_id = cr.fetchall()[0][0]
                company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

                arquivo_texto, sefip = self._gera_arquivo(cr, uid, sefip_obj, company_obj, arquivo_texto=arquivo_texto)

                print(cnpj, len(arquivo_texto))

                if sefip is not None:
                    ultimo_sefip = sefip

            if ultimo_sefip:
                arquivo_texto += ultimo_sefip.registro_90()

            dados = {
                'nome_arquivo': 'sefip.re',
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }
            sefip_obj.write(dados)
