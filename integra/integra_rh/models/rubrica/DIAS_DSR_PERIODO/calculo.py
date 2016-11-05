
if holerite.tipo == 'R' and holerite.afastamento_imediato:
    result_qty = contrato.dias_DSR(holerite.data_afastamento[:7] + '-01', holerite.data_afastamento, total_mes=True)
else:
    result_qty = contrato.dias_DSR(holerite.date_from, holerite.date_to, total_mes=True)

horas = D(contrato.horas_mensalista) / D(30)
horas = horas.quantize(D('0.01'))

result = contrato.salario_hora(holerite.data_inicial, holerite.data_final)
result *= horas

if variavel.COMISSAO:
    dias_dsr = contrato.dias_descanso_semanal_remunerado(holerite.data_inicial, holerite.data_final)
    result = variavel.COMISSAO.valor * dias_dsr
    result /= result_qty