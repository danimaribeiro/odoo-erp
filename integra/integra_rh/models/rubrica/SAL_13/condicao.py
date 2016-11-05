if variavel.SAL_13:
    result = variavel.SAL_13.valor > 0
elif holerite.tipo == 'R':
    if holerite.data_afastamento:
        meses, x = contrato.decimo_terceiro_proporcional(primeiro_dia_mes(holerite.data_afastamento), holerite.data_afastamento, calcula=True, inclui_mes=True, soh_busca_valor=True, data_rescisao=holerite.data_afastamento, dias_aviso_previo=holerite.dias_aviso_previo)
        result = meses > 0
    else:
        result = False
elif holerite.tipo == 'D':
    result = True
else:
    meses, x = contrato.decimo_terceiro_proporcional(holerite.data_inicial, holerite.data_final)
    result = meses > 0
