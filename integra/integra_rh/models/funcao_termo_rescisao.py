DROP FUNCTION IF EXISTS termo_rescisao_rubricas();

CREATE OR REPLACE FUNCTION termo_rescisao_rubricas()
  RETURNS TABLE(slip_id integer, sinal character varying, rubrica_1 character varying, valor_1 numeric, rubrica_2 character varying, valor_2 numeric, rubrica_3 character varying, valor_3 numeric, total numeric) AS
$BODY$
from copy import copy
from decimal import Decimal as D
from mako.template import Template
from pybrasil.valor import formata_valor

res = []
linha_modelo = {
    'slip_id': 0,
    'sinal': '',
    'rubrica_1': u'',
    'valor_1': None,
    'rubrica_2': u'',
    'valor_2': None,
    'rubrica_3': u'',
    'valor_3': None,
    'total': D(0),
}

class Rubrica(object):
    def __init__(self):
        self.codigo = ''
        self.quantidade = D(0)
        self.base = D(0)
        self.aliquota = D(0)
        self.valor = D(0)


for dados_holerite in plpy.cursor("select h.id from hr_payslip h where h.tipo = 'R' order by h.id;"):
    holerite_id = dados_holerite['id']
    res_holerite = []

    #
    # Prepara o ambiente com as rubricas necessárias
    #
    ambiente = {}
    for dados_rubricas in plpy.cursor("""
        select
            hl.code as codigo,
            cast(coalesce(hl.rate, 0) as varchar) as aliquota,
            cast(coalesce(hl.quantity, 0) as varchar) as quantidade,
            cast(coalesce(hl.amount, 0) as varchar) as base,
            cast(coalesce(hl.total, 0) as varchar) as valor
        from
            hr_payslip_line hl
        where
            hl.slip_id = %d;
    """ % holerite_id):
        rubrica = Rubrica()
        rubrica.codigo = dados_rubricas['codigo']
        rubrica.aliquota = D(dados_rubricas['aliquota'])
        rubrica.quantidade = D(dados_rubricas['quantidade'])
        rubrica.base = D(dados_rubricas['base'])
        rubrica.valor = D(dados_rubricas['valor'])
        ambiente[rubrica.codigo] = rubrica

    #
    # Agora, acumula somente as rubricas que serão usadas no termo de rescisão
    #
    num_rubrica = 1
    total = D(0)
    linha = copy(linha_modelo)
    linha['slip_id'] = holerite_id
    for dados_rubricas in plpy.cursor("""
        select
            rr.codigo,
            rr.descricao,
            cast(max(coalesce(hl.rate, 0)) as varchar) as aliquota,
            cast(sum(coalesce(hl.quantity, 0)) as varchar) as quantidade,
            cast(sum(coalesce(hl.amount, 0)) as varchar) as base,
            cast(sum(coalesce(hl.total, 0)) as varchar) as valor
        from
            hr_payslip_line hl
            join hr_salary_rule r on r.id = hl.salary_rule_id
            join hr_salary_rule_category c on c.id = r.category_id
            join hr_rubrica_rescisao rr on rr.id = r.rubrica_rescisao_id
        where
            hl.slip_id = %d and c.sinal in ('+', '-')
        group by
            rr.codigo,
            rr.descricao
        order by
            rr.codigo;
    """ % holerite_id):
        codigo = D(dados_rubricas['codigo'])

        if codigo <= 99:
            sinal = '+'
        else:
            sinal = '-'

        if linha['sinal'] == '':
            linha['sinal'] = sinal

        ambiente['aliquota'] = formata_valor(D(dados_rubricas['aliquota']), casas_decimais=2)
        ambiente['quantidade'] = formata_valor(D(dados_rubricas['quantidade']), casas_decimais=2)
        ambiente['base'] = formata_valor(D(dados_rubricas['base']), casas_decimais=2)
        ambiente['valor'] = formata_valor(D(dados_rubricas['valor']), casas_decimais=2)

        dados_rubricas['descricao'] = Template(dados_rubricas['descricao'].decode('utf-8')).render(**ambiente)

        if (linha['sinal'] != '' and sinal != linha['sinal']) or (num_rubrica > 3):
            res_holerite.append(linha)
            total = D(0)
            num_rubrica = 1
            sinal_anterior = sinal
            linha = copy(linha_modelo)
            linha['slip_id'] = holerite_id
            linha['sinal'] = sinal

        if num_rubrica == 1:
            linha['rubrica_1'] = dados_rubricas['codigo'] + ' ' + dados_rubricas['descricao']
            linha['valor_1'] = D(dados_rubricas['valor'])
        elif num_rubrica == 2:
            linha['rubrica_2'] = dados_rubricas['codigo'] + ' ' + dados_rubricas['descricao']
            linha['valor_2'] = D(dados_rubricas['valor'])
        elif num_rubrica == 3:
            linha['rubrica_3'] = dados_rubricas['codigo'] + ' ' + dados_rubricas['descricao']
            linha['valor_3'] = D(dados_rubricas['valor'])

        total += D(dados_rubricas['valor'])
        linha['total'] = total
        num_rubrica += 1

    linha['total'] = total
    res_holerite.append(linha)

    #
    # Agora, conta quantas linha existe de proventos e descontos
    # e cria as linhas dos totais e as em branco
    #
    total_provento = D(0)
    total_desconto = D(0)
    linhas_provento = 1  # Conta a linha do total
    linhas_desconto = 2  # Conta a linha do total e do total geral

    for linha in res_holerite:
        if linha['sinal'] == '+':
            linhas_provento += 1
            if linha['total']:
                total_provento += linha['total']
        else:
            linhas_desconto += 1
            if linha['total']:
                total_desconto += linha['total']

    #
    # Adiciona as linhas em branco
    #
    if linhas_provento < 6:
        for i in range(6-linhas_provento):
            linha_total = copy(linha_modelo)
            linha_total['slip_id'] = holerite_id
            linha_total['sinal'] = '+'
            linha_total['rubrica_3'] = u''
            linha_total['valor_3'] = None
            linha_total['valor_1'] = None
            linha_total['valor_2'] = None
            linha_total['total'] = None
            res_holerite.append(linha_total)

    #
    # Adiciona a linha do total
    #
    linha_total = copy(linha_modelo)
    linha_total['slip_id'] = holerite_id
    linha_total['sinal'] = '+'
    linha_total['rubrica_3'] = u'TOTAL BRUTO'
    linha_total['valor_3'] = total_provento
    linha_total['valor_1'] = None
    linha_total['valor_2'] = None
    res_holerite.append(linha_total)


    #
    # Adiciona as linhas em branco
    #
    if linhas_provento < 6:
        for i in range(6-linhas_desconto):
            linha_total = copy(linha_modelo)
            linha_total['slip_id'] = holerite_id
            linha_total['sinal'] = '-'
            linha_total['rubrica_3'] = u''
            linha_total['valor_3'] = None
            linha_total['valor_1'] = None
            linha_total['valor_2'] = None
            linha_total['total'] = None
            res_holerite.append(linha_total)

    #
    # Adiciona a linha do total
    #
    linha_total = copy(linha_modelo)
    linha_total['slip_id'] = holerite_id
    linha_total['sinal'] = '-'
    linha_total['rubrica_3'] = 'TOTAL DEDUÇÕES'
    linha_total['valor_3'] = total_desconto
    linha_total['valor_1'] = None
    linha_total['valor_2'] = None
    res_holerite.append(linha_total)

    linha_total = copy(linha_modelo)
    linha_total['slip_id'] = holerite_id
    linha_total['sinal'] = '-'
    linha_total['rubrica_3'] = 'VALOR LÍQUIDO'
    linha_total['valor_3'] = total_provento - total_desconto
    linha_total['valor_1'] = None
    linha_total['valor_2'] = None
    res_holerite.append(linha_total)

    for l in res_holerite:
        res.append(l)

return res
$BODY$
  LANGUAGE plpythonu VOLATILE
  COST 100
  ROWS 1000;
