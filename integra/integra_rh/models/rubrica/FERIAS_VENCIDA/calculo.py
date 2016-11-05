if variavel.FERIAS_VENCIDA:
    result = variavel.FERIAS_VENCIDA.valor
else:
    dias, valor_vencido, simulacao_id = contrato.ferias_vencidas(holerite.data_inicial, holerite.data_final, data_rescisao=holerite.data_afastamento, exclui_simulacao=False, soh_busca_valor=True)
    result_qty = dias / D(2.5)
    result = valor_vencido / (dias / D(2.5))
