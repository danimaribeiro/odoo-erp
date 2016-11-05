if variavel.FERIAS_PROPORCIONAL_AP:
    result = variavel.FERIAS_PROPORCIONAL_AP.valor
else:
    dias, valor_proporcional, simulacao_id = contrato.ferias_proporcionais(holerite.data_aviso_previo, holerite.data_final, data_rescisao=holerite.data_afastamento, exclui_simulacao=False, soh_busca_valor=True, aviso_previo=True)
    result = valor_proporcional / (D(dias) / D(2.5))

    avos = D(holerite.dias_aviso_previo or 0) / D(30)
    if avos - int(avos) >= D('0.5'):
        avos = int(avos) + 1
    else:
        avos = int(avos)

    result_qty = avos
