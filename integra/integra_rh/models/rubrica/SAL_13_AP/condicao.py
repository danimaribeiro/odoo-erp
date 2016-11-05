result = False

if variavel.SAL_13_AP:
    result = variavel.SAL_13_AP.valor > 0

elif holerite.tipo == 'R':
    if holerite.data_afastamento:
        meses, x = contrato.decimo_terceiro_proporcional(primeiro_dia_mes(holerite.data_afastamento), holerite.data_afastamento, calcula=True, inclui_mes=True, soh_busca_valor=True, data_rescisao=holerite.data_afastamento, dias_aviso_previo=holerite.dias_aviso_previo)
        result = meses > 0 and holerite.aviso_previo_indenizado
    else:
        result = False
