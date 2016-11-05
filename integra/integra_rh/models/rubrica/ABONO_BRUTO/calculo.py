
result = D(0)

for codigo_rubrica in CALCULOS_ANTERIORES:
    if 'ABONO' in codigo_rubrica and CALCULOS_ANTERIORES[codigo_rubrica]['sinal'] == '+':
        result += D(CALCULOS_ANTERIORES[codigo_rubrica]['total'] or 0)
