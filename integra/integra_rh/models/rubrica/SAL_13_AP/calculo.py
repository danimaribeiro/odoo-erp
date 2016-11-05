if variavel.SAL_13_AP:
    result = variavel.SAL_13_AP.valor
else:
    meses, valor_proporcional, simulacao_id = contrato.decimo_terceiro_proporcional(primeiro_dia_mes(holerite.data_afastamento), holerite.data_afastamento, data_rescisao=holerite.data_afastamento, dias_aviso_previo=holerite.dias_aviso_previo, inclui_mes=True, soh_busca_valor=True, mantem_calculo=True)
    result = D(valor_proporcional) / D(meses)
    result = valor_proporcional / D(meses)

    avos = D(holerite.dias_aviso_previo or 0) / D(30)
    if avos - int(avos) >= D('0.5'):
        avos = int(avos) + 1
    else:
        avos = int(avos)

    result_qty = avos
