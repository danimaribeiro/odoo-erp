if variavel.SAL_13:
    result = variavel.SAL_13.valor
elif holerite.tipo == 'R':
    meses, valor_proporcional, simulacao_id = contrato.decimo_terceiro_proporcional(primeiro_dia_mes(holerite.data_afastamento), holerite.data_afastamento, data_rescisao=holerite.data_afastamento, dias_aviso_previo=holerite.dias_aviso_previo, inclui_mes=True, soh_busca_valor=True, mantem_calculo=True)
    result = D(valor_proporcional) / D(meses)
    avos = meses

    #if holerite.aviso_previo_indenizado:
        #avos -= D(int(holerite.dias_aviso_previo / 30.0))

    result_qty = avos

else:
    if contrato.unidade_salario == '1':
        if variavel.HORAS_TRABALHADAS:
            result_qty = variavel.HORAS_TRABALHADAS.valor
            result = contrato.salario_hora(holerite.data_inicial, holerite.data_final)

    else:
        result = contrato.salario_mes(holerite.data_inicial, holerite.data_final) / D(12)
        result_qty = holerite.meses_decimo_terceiro

if 'LICENCA_MATERNIDADE' in locals():
    result_qty -= LICENCA_MATERNIDADE_quantidade
