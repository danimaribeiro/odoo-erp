
base_de_calculo = BASE_INSS

if 'BASE_INSS_INDIVIDUAL' in locals():
    base_de_calculo += BASE_INSS_INDIVIDUAL

ano = int(holerite.data_inicial[:4])
if ano in TABELA_INSS:
    faixas_de_contribuicao = TABELA_INSS[ano]
    teto_de_contribuicao = TETO_INSS[ano]

if base_de_calculo > teto_de_contribuicao:
    result = teto_de_contribuicao
    result_rate = D(11)

#
# Pro-labore e autônomos têm alíquota fixa em 11%
#
elif contrato.categoria_trabalhador >= '701' and contrato.categoria_trabalhador < '800':
    result = base_de_calculo
    result_rate = D(11)

else:
    for limite_faixa, aliquota in faixas_de_contribuicao:
        if base_de_calculo <= limite_faixa:
            result = base_de_calculo
            result_rate = D(aliquota)

#if 'INSS_anterior' in locals():
#    valor_inss = result * result_rate / D(100)
#    valor_inss = int(valor_inss * D(100)) / D(100)
#    valor_inss -= INSS_anterior
#    result = valor_inss / (result_rate / D(100))

if 'DIFERENCA_13' in locals():
    result -= DIFERENCA_13

if 'INSS_INDIVIDUAL' in locals():
    valor_inss = result * result_rate / D(100)
    valor_inss = int(valor_inss * D(100)) / D(100)
    valor_inss -= INSS_INDIVIDUAL
    result = valor_inss / (result_rate / D(100))

if result < 0:
    result = 0


#if 'INSS_anterior' in locals():
#    if holerite.tipo == 'R' and holerite.dias_ferias:
#        pass
#    else:
#        valor_inss = result * result_rate / D(100)
#        valor_inss = int(valor_inss * D(100)) / D(100)
#        valor_inss -= INSS_anterior
#        result = valor_inss / (result_rate / D(100))

if result >= 0:
    holerite.cria_apaga_variavel(valor=0, codigo='DIFERENCA_INSS')
else:
    dif = result * -1
    dif *= result_rate / D(100)
    holerite.cria_apaga_variavel(valor=dif, codigo='DIFERENCA_INSS')
    result = 0
