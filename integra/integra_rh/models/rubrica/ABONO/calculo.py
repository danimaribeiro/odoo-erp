
result = 0
result_qty = 0

if holerite.tipo == 'F':
    if contrato.unidade_salario == '1':
        if variavel.HORAS_TRABALHADAS:
            result_qty = HORAS_TRABALHADAS_ABONO_quantidade
            result = contrato.salario_hora(holerite.data_inicial, holerite.data_final)

    else:
        result_qty = 30 - holerite.dias_ferias
        result = contrato.salario_dia(holerite.data_inicial, holerite.data_final)

if variavel.ABONO:
    result = variavel.ABONO.valor / (result_qty * 1.0)
