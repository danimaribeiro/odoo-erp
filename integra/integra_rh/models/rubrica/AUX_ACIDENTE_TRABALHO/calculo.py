
simulacao_id, valor_mensal = afastamento.AUX_ACIDENTE_TRABALHO.afastamento_id.calcula_auxilio_acidente()
result_qty = afastamento.AUX_ACIDENTE_TRABALHO.dias_afastamento

if valor_mensal:
    result = valor_mensal / D(30)
else:
    result = contrato.salario_dia(holerite.data_inicial, holerite.data_final)
