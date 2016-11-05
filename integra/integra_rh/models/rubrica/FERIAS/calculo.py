
result = 0
result_qty = 0

if holerite.tipo == 'F':
    if contrato.unidade_salario == '1':
        if variavel.HORAS_TRABALHADAS:
            result_qty = HORAS_TRABALHADAS_quantidade
            result = contrato.salario_hora(holerite.data_inicial, holerite.data_final)

    else:
        result_qty = holerite.dias_ferias
        result = contrato.salario_dia(holerite.data_inicial, holerite.data_final)

if variavel.FERIAS:
    result = variavel.FERIAS.valor / D(result_qty or 1)
