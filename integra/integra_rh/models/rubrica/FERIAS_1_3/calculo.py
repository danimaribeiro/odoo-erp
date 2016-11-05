
if holerite.tipo == 'F':
    if 'ABONO' in locals():
        result = (BRUTO - ABONO_BRUTO) / 3.0
    else:
        result = BRUTO / 3.0
else:
    result = FERIAS / 3.0