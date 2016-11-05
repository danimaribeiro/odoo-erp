drop function if exists finan_analitico(data_inicial date, data_final date, company_id int, zera_saldo boolean);
-- drop function if exists finan_analitico(data_inicial date, data_final date, company_id int);


CREATE OR REPLACE FUNCTION finan_analitico(IN data_ini date, IN data_fin date, IN company_id integer, zera_saldo boolean default False)
    RETURNS TABLE(
        id integer,
        codigo character varying,
        descricao character varying,
        titulo_01 character varying,
        titulo_02 character varying,
        titulo_03 character varying,
        titulo_04 character varying,
        titulo_05 character varying,
        titulo_06 character varying,
        titulo_07 character varying,
        titulo_08 character varying,
        titulo_09 character varying,
        titulo_10 character varying,
        titulo_11 character varying,
        titulo_12 character varying,
        quitado_anterior numeric,
        quitado_01 numeric,
        quitado_02 numeric,
        quitado_03 numeric,
        quitado_04 numeric,
        quitado_05 numeric,
        quitado_06 numeric,
        quitado_07 numeric,
        quitado_08 numeric,
        quitado_09 numeric,
        quitado_10 numeric,
        quitado_11 numeric,
        quitado_12 numeric,
        quitado_total numeric,
        percentual_quitado numeric,
        vencido_anterior numeric,
        vencido_01 numeric,
        vencido_02 numeric,
        vencido_03 numeric,
        vencido_04 numeric,
        vencido_05 numeric,
        vencido_06 numeric,
        vencido_07 numeric,
        vencido_08 numeric,
        vencido_09 numeric,
        vencido_10 numeric,
        vencido_11 numeric,
        vencido_12 numeric,
        vencido_total numeric,
        percentual_vencido numeric) AS
$BODY$
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, formata_data, tempo
from dateutil.relativedelta import relativedelta


res = []
#
# Cria um modelo de dicionário para retorno
#
linha_modelo = {
    'id': -1,
    'codigo': u'',
    'descricao': u'',
    'quitado_anterior': D('0.00'),
    'vencido_anterior': D('0.00'),
    'quitado_total': D('0.00'),
    'vencido_total': D('0.00'),
    'quitado_01': D('0.00'),
    'quitado_02': D('0.00'),
    'quitado_03': D('0.00'),
    'quitado_04': D('0.00'),
    'quitado_05': D('0.00'),
    'quitado_06': D('0.00'),
    'quitado_07': D('0.00'),
    'quitado_08': D('0.00'),
    'quitado_09': D('0.00'),
    'quitado_10': D('0.00'),
    'quitado_11': D('0.00'),
    'quitado_12': D('0.00'),
    'vencido_01': D('0.00'),
    'vencido_02': D('0.00'),
    'vencido_03': D('0.00'),
    'vencido_04': D('0.00'),
    'vencido_05': D('0.00'),
    'vencido_06': D('0.00'),
    'vencido_07': D('0.00'),
    'vencido_08': D('0.00'),
    'vencido_09': D('0.00'),
    'vencido_10': D('0.00'),
    'vencido_11': D('0.00'),
    'vencido_12': D('0.00'),
    'titulo_01': '',
    'titulo_02': '',
    'titulo_03': '',
    'titulo_04': '',
    'titulo_05': '',
    'titulo_06': '',
    'titulo_07': '',
    'titulo_08': '',
    'titulo_09': '',
    'titulo_10': '',
    'titulo_11': '',
    'titulo_12': '',
    'percentual_quitado': D('0.00'),
    'percentual_vencido': D('0.00'),
}

#
# Ajusta os nomes dos dias e meses
#
data_inicial = parse_datetime(data_ini).date()
data_final = parse_datetime(data_fin).date()

dif = tempo(data_final, data_inicial)
data = data_inicial
i = 1
lista_meses = []
while data <= data_final:
    #
    # Relatório por dia
    #
    if (dif.years == 0 and dif.months == 0) and dif.days <= 7:
        linha_modelo['titulo_' + str(i).zfill(2)] = formata_data(data, '%a %d/%m/%Y')
        data += relativedelta(days=+1)
    else:
        linha_modelo['titulo_' + str(i).zfill(2)] = formata_data(data, '%B de %Y')
        lista_meses.append('_' + formata_data(data, '%m'))
        data += relativedelta(months=+1)

    i += 1

sql_company_ids = "(select c.id from res_company c where c.id = %d or c.parent_id = %d)" % (company_id, company_id)
total_quitado_grupo = D('0')
total_vencido_grupo = D('0')

linha_receita = copy(linha_modelo)
linha_receita['descricao'] = 'RECEITAS'
linha_despesa = copy(linha_modelo)
linha_despesa['descricao'] = 'DESPESAS'
total_grupo = {}

for dados in plpy.execute("SELECT id, codigo_completo, nome, sintetica, parent_id, tipo FROM finan_conta where tipo in ('R', 'D') ORDER BY parent_left, parent_right;"):
    codigo = dados['codigo_completo']
    id = dados['id']
    descricao = dados['nome']
    sintetica = dados['sintetica']
    parent_id = dados['parent_id']
    tipo = dados['tipo']
    linha = copy(linha_modelo)
    linha['id'] = id
    linha['codigo'] = codigo
    linha['descricao'] = descricao

    if sintetica:
        sql_conta_ids = "(select c.id from finan_conta c where c.codigo_completo ilike '" + codigo + "\.%')"
        total_grupo[id] = linha

    else:
        sql_conta_ids = '(' + str(id) + ')'

    linha['quitado_anterior'] = D(0)

    if not zera_saldo:
        sql_quitado_anterior = """
            select
                coalesce(sum(pr.valor), 0.00) as quitado
            from finan_pagamento_rateio pr
            where
                pr.tipo in ('R', 'P', 'E', 'S')
                and pr.conta_id in """ + sql_conta_ids + """
                and pr.data_quitacao < '""" + str(data_inicial) + """'
                and pr.company_id in """ + sql_company_ids + """;"""

        linha['quitado_anterior'] = D(plpy.execute(sql_quitado_anterior)[0]['quitado'])

    linha['quitado_total'] = D(linha['quitado_anterior'])

    #
    # Agora, os valores mensais
    #
    sql_meses_quitado = """
        select
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '01' then l.valor
                else 0.00
            end), 0.00) as mes_01,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '02' then l.valor
                else 0.00
            end), 0.00) as mes_02,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '03' then l.valor
                else 0.00
            end), 0.00) as mes_03,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '04' then l.valor
                else 0.00
            end), 0.00) as mes_04,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '05' then l.valor
                else 0.00
            end), 0.00) as mes_05,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '06' then l.valor
                else 0.00
            end), 0.00) as mes_06,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '07' then l.valor
                else 0.00
            end), 0.00) as mes_07,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '08' then l.valor
                else 0.00
            end), 0.00) as mes_08,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '09' then l.valor
                else 0.00
            end), 0.00) as mes_09,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '10' then l.valor
                else 0.00
            end), 0.00) as mes_10,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '11' then l.valor
                else 0.00
            end), 0.00) as mes_11,
            coalesce(sum(case
                when to_char(l.data_quitacao, 'MM') = '12' then l.valor
                else 0.00
            end), 0.00) as mes_12
        from finan_pagamento_rateio l
        where
            l.tipo in ('R', 'P', 'E', 'S')
            and l.conta_id in """ + sql_conta_ids + """
            and l.data_quitacao between '""" + str(data_inicial) + """' and '"""+ str(data_final) + """'
            and l.company_id in """ + sql_company_ids + """;"""

    dados_quitado = plpy.execute(sql_meses_quitado)[0]

    for i in range(len(lista_meses)):
        mes = lista_meses[i]
        linha['quitado_' + str(i + 1).zfill(2)] = D(dados_quitado['mes' + mes])
        linha['quitado_total'] += D(dados_quitado['mes' + mes])

    linha['vencido_anterior'] = D(0)

    if not zera_saldo:
        sql_vencido_anterior = """
            select
                cast(coalesce(sum(l.valor_saldo * lr.porcentagem / 100.00), 0.00) as numeric(18,2)) as vencido
            from finan_lancamento_rateio_geral lr
            join finan_lancamento l on l.id = lr.lancamento_id
            where
                l.tipo in ('R', 'P')
                and lr.conta_id in """ + sql_conta_ids + """
                and l.data_baixa is null
                and l.data_quitacao is null
                and l.data_vencimento < '""" + str(data_inicial) + """'
                and lr.company_id in """ + sql_company_ids + """;"""

        linha['vencido_anterior'] = D(plpy.execute(sql_vencido_anterior)[0]['vencido'])

    linha['vencido_total'] = D(linha['vencido_anterior'])

    #
    # Agora, os valores mensais por vencimento
    #
    sql_meses_vencido = """
        select
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '01' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_01,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '02' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_02,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '03' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_03,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '04' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_04,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '05' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_05,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '06' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_06,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '07' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_07,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '08' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_08,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '09' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_09,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '10' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_10,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '11' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_11,
            coalesce(sum(case
                when to_char(l.data_vencimento, 'MM') = '12' then l.valor_saldo * lr.porcentagem / 100.00
                else 0.00
            end), 0.00) as mes_12
        from finan_lancamento_rateio_geral lr
        join finan_lancamento l on l.id = lr.lancamento_id
        where
            l.tipo in ('R', 'P')
            and lr.conta_id in """ + sql_conta_ids + """
            and l.data_baixa is null
            and l.data_quitacao is null
            and l.data_vencimento between '""" + str(data_inicial) + """' and '""" + str(data_final) + """'
            and lr.company_id in """ + sql_company_ids + """;"""

    dados_vencido = plpy.execute(sql_meses_vencido)[0]
    for i in range(len(lista_meses)):
        mes = lista_meses[i]
        linha['vencido_' + str(i + 1).zfill(2)] = D(dados_vencido['mes' + mes])
        linha['vencido_total'] += D(dados_vencido['mes' + mes])

    #
    # Ajusta o percentual no grupo
    #
    if parent_id is not None and parent_id in total_grupo:
        if total_grupo[parent_id]['quitado_total']:
            linha['percentual_quitado'] = linha['quitado_total'] / total_grupo[parent_id]['quitado_total'] * D('100.00')
            linha['percentual_quitado'] = linha['percentual_quitado'].quantize(D('0.01'))

        if total_grupo[parent_id]['vencido_total']:
            linha['percentual_vencido'] = linha['vencido_total'] / total_grupo[parent_id]['vencido_total'] * D('100.00')
            linha['percentual_vencido'] = linha['percentual_vencido'].quantize(D('0.01'))
    elif parent_id is None:
        if linha['quitado_total'] > 0:
            linha['percentual_quitado'] = D('100')

        if linha['vencido_total'] > 0:
            linha['percentual_vencido'] = D('100')

    #
    # Acumula o total de receitas e despesas
    #
    if not sintetica:
        for campo in linha:
            if isinstance(linha[campo], D):
                if tipo == 'R':
                    linha_receita[campo] += linha[campo]
                else:
                    linha_despesa[campo] += linha[campo]

    res.append(linha)

#
# Agora, no final, fazemos a linha do acumulado
#
linha_final = copy(linha_modelo)
linha_final['descricao'] = 'SALDO FINAL'
for campo in linha:
    if isinstance(linha[campo], D):
        linha_final[campo] = linha_receita[campo] - linha_despesa[campo]

linha_acumulado = copy(linha_final)
linha_acumulado['descricao'] = 'ACUMULADO'
for i in range(len(lista_meses)):
    if i == 0:
        linha_acumulado['quitado_' + str(i + 1).zfill(2)] += linha_acumulado['quitado_anterior']
        linha_acumulado['vencido_' + str(i + 1).zfill(2)] += linha_acumulado['vencido_anterior']
    else:
        linha_acumulado['quitado_' + str(i + 1).zfill(2)] += linha_acumulado['quitado_' + str(i).zfill(2)]
        linha_acumulado['vencido_' + str(i + 1).zfill(2)] += linha_acumulado['vencido_' + str(i).zfill(2)]

res.append(linha_receita)
res.append(linha_despesa)
res.append(linha_final)
res.append(linha_acumulado)

return res

$BODY$
  LANGUAGE plpythonu VOLATILE
  COST 100
  ROWS 1000;
