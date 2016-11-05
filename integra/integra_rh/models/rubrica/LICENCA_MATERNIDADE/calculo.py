
if holerite.tipo == 'D':
    result_qty = variavel.LICENCA_MATERNIDADE.valor
    result = SAL_13_base

    #
    # Compensa a divisão por 2 no adiantamento do 13º
    #
    if holerite.simulacao == False and '-12-' not in holerite.date_from:
        result *= 2

else:
    simulacao_id, valor_mensal = afastamento.LICENCA_MATERNIDADE.afastamento_id.calcula_licenca_maternidade()
    result_qty = afastamento.LICENCA_MATERNIDADE.dias_afastamento

    if valor_mensal:
        result = valor_mensal / D(30)
    else:
        result = contrato.salario_dia(holerite.data_inicial, holerite.data_final)
