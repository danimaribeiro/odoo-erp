if variavel.FERIAS_VENCIDA:
    result = variavel.FERIAS_VENCIDA.valor > 0
else:
    result = contrato.ferias_vencidas(holerite.data_inicial, holerite.data_final, data_rescisao=holerite.data_afastamento, exclui_simulacao=False, soh_busca_valor=True)[0] > 0