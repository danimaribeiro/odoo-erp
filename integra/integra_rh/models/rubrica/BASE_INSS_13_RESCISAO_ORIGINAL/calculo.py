result_rate = 100.0
result_qty = 1.0
result = 0

base_anterior = holerite.rubrica_outro_periodo(rubrica='BASE_INSS_13', meses=0, tipo='R', mes_todo=True)

if base_anterior:
    result = base_anterior.total