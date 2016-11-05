
if variavel.FERIAS_PROPORCIONAL:
    result = True
else:
    dias, valor_proporcional, simulacao_id = contrato.ferias_proporcionais(holerite.data_inicial, holerite.data_final, exclui_simulacao=False, data_rescisao=holerite.data_afastamento, soh_busca_valor=True)
    if dias > 0:
        result = D(valor_proporcional) / (dias / D(2.5))

    if holerite.aviso_previo_indenizado and not holerite.afastamento_imediato:
        dias -= int(holerite.dias_aviso_previo / 30.00) * 2.5

    result_qty = dias / D(2.5)
    result = result_qty > 0
