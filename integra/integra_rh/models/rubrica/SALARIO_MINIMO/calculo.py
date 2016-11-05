
result = 0

ano = int(holerite.data_inicial[0:4])

if ano in TABELA_SALARIO_MINIMO:
    result = TABELA_SALARIO_MINIMO[ano]

result_qty = 1
result_rate = 100.00
aparece_no_holerite = False
